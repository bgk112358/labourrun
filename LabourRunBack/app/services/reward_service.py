from __future__ import annotations

import re
import secrets
import sqlite3
from typing import Any

from ..config import Settings
from ..db import transaction
from ..errors import AppError, ErrorCode
from ..ids import new_id
from ..timeutil import format_cents, utc_now_iso
from .common import get_current_activity
from .coupon_service import get_account_row, serialize_account

CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_PREFIX = "LR-"
CODE_LENGTH = 8


def activity_open_state(
    activity: sqlite3.Row,
) -> tuple[bool, str | None]:
    status = activity["status"]
    if status == "upcoming":
        return False, "活动未开始"
    if status == "ended":
        return False, "活动已结束"
    if status != "ongoing":
        return False, "活动未开放"
    return True, None


def _reward_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "image_url": row["image_url"],
        "coupon_cost": format_cents(row["coupon_cost_cents"]),
    }


def list_home_rewards(
    conn: sqlite3.Connection,
    activity: sqlite3.Row,
    user_id: str,
    registration: sqlite3.Row | None,
) -> list[dict[str, Any]]:
    rewards = conn.execute(
        """
        SELECT *
        FROM rewards
        WHERE activity_id = ?
        ORDER BY sort_order ASC, id ASC
        """,
        (activity["id"],),
    ).fetchall()

    redemption_rows = conn.execute(
        """
        SELECT *
        FROM reward_redemptions
        WHERE user_id = ? AND activity_id = ?
        """,
        (user_id, activity["id"]),
    ).fetchall()
    redemptions = {row["reward_id"]: row for row in redemption_rows}

    activity_open, closed_reason = activity_open_state(activity)
    registered = bool(
        registration is not None
        and registration["status"] == "registered"
    )

    result: list[dict[str, Any]] = []
    for row in rewards:
        redemption = redemptions.get(row["id"])
        redeemed = redemption is not None
        if not int(row["active"]) and not redeemed:
            continue
        can_redeem = bool(
            not redeemed
            and int(row["active"])
            and activity_open
            and registered
        )
        disabled_reason: str | None = None
        if not can_redeem and not redeemed:
            if not activity_open:
                disabled_reason = closed_reason
            elif not registered:
                disabled_reason = "请先报名"

        item = _reward_row(row)
        item.update(
            {
                "redeemed": redeemed,
                "redemption_code": (
                    redemption["code"] if redemption else None
                ),
                "redeemed_at": (
                    redemption["created_at"] if redemption else None
                ),
                "redemption_reward_name": (
                    redemption["reward_name"] if redemption else None
                ),
                "redemption_coupon_cost": (
                    format_cents(redemption["coupon_cost_cents"])
                    if redemption
                    else None
                ),
                "can_redeem": can_redeem,
                "disabled_reason": disabled_reason,
            }
        )
        result.append(item)
    return result


def generate_reward_code() -> str:
    raw = "".join(
        secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH)
    )
    return f"{CODE_PREFIX}{raw}"


def normalize_reward_code(raw: str | None) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", (raw or "").upper())
    if len(compact) == CODE_LENGTH:
        compact = "LR" + compact
    if compact.startswith("LR") and len(compact) == 2 + CODE_LENGTH:
        return f"{CODE_PREFIX}{compact[2:]}"
    return compact


def _redemption_payload(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
) -> dict[str, Any]:
    return {
        "redemption": {
            "id": row["id"],
            "reward_id": row["reward_id"],
            "code": row["code"],
            "reward_name": row["reward_name"],
            "coupon_amount": format_cents(row["coupon_cost_cents"]),
            "created_at": row["created_at"],
        },
        "coupon_account": serialize_account(
            get_account_row(conn, row["user_id"])
        ),
    }


def redeem_reward(
    settings: Settings,
    user_id: str,
    reward_id: str,
    request_id: str,
) -> dict[str, Any]:
    with transaction(settings) as conn:
        existing_request = conn.execute(
            """
            SELECT *
            FROM reward_redemptions
            WHERE user_id = ? AND request_id = ?
            """,
            (user_id, request_id),
        ).fetchone()
        if existing_request is not None:
            return _redemption_payload(conn, existing_request)

        activity = get_current_activity(conn)
        if activity is None:
            raise AppError(
                ErrorCode.ACTIVITY_NOT_FOUND,
                404,
                "活动不存在",
            )

        reward = conn.execute(
            """
            SELECT *
            FROM rewards
            WHERE id = ? AND activity_id = ?
            """,
            (reward_id, activity["id"]),
        ).fetchone()
        if reward is None:
            raise AppError(
                ErrorCode.REWARD_NOT_FOUND,
                404,
                "奖品不存在",
            )
        if not int(reward["active"]):
            raise AppError(
                ErrorCode.REWARD_UNAVAILABLE,
                422,
                "奖品已下架",
            )

        activity_open, closed_reason = activity_open_state(activity)
        if not activity_open:
            raise AppError(
                ErrorCode.REWARD_ACTIVITY_CLOSED,
                422,
                closed_reason or "活动未开放",
            )

        registration = conn.execute(
            """
            SELECT *
            FROM registrations
            WHERE activity_id = ? AND user_id = ?
            """,
            (activity["id"], user_id),
        ).fetchone()
        if (
            registration is None
            or registration["status"] != "registered"
        ):
            raise AppError(
                ErrorCode.REWARD_REGISTRATION_REQUIRED,
                422,
                "请先报名",
            )

        existing_reward = conn.execute(
            """
            SELECT *
            FROM reward_redemptions
            WHERE user_id = ? AND reward_id = ?
            """,
            (user_id, reward_id),
        ).fetchone()
        if existing_reward is not None:
            raise AppError(
                ErrorCode.REWARD_ALREADY_REDEEMED,
                409,
                "该奖励已兑换",
            )

        account = get_account_row(conn, user_id)
        old_balance = int(account["balance_cents"]) if account else 0
        cost = int(reward["coupon_cost_cents"])
        if old_balance < cost:
            raise AppError(
                ErrorCode.REWARD_INSUFFICIENT_COUPONS,
                422,
                "兑换券不足",
            )

        now = utc_now_iso()
        cursor = conn.execute(
            """
            UPDATE coupon_accounts
            SET balance_cents = balance_cents - ?,
                total_spent_cents = total_spent_cents + ?,
                updated_at = ?
            WHERE user_id = ? AND balance_cents >= ?
            """,
            (cost, cost, now, user_id, cost),
        )
        if cursor.rowcount != 1:
            raise AppError(
                ErrorCode.REWARD_INSUFFICIENT_COUPONS,
                422,
                "兑换券不足",
            )
        new_balance = old_balance - cost

        redemption_id = new_id("red")
        code = generate_reward_code()
        try:
            conn.execute(
                """
                INSERT INTO reward_redemptions
                    (id, code, user_id, registration_id, reward_id,
                     activity_id, reward_name, coupon_cost_cents,
                     real_name, phone, company, request_id, status,
                     created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success', ?)
                """,
                (
                    redemption_id,
                    code,
                    user_id,
                    registration["id"],
                    reward["id"],
                    activity["id"],
                    reward["name"],
                    cost,
                    registration["real_name"],
                    registration["phone"],
                    registration["company"],
                    request_id,
                    now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise AppError(
                ErrorCode.INTERNAL_ERROR,
                500,
                "生成兑换码失败，请重试",
            ) from exc

        conn.execute(
            """
            INSERT INTO coupon_ledger
                (id, user_id, type, amount_cents, balance_after_cents,
                 ref_type, ref_id, created_at)
            VALUES (?, ?, 'reward', ?, ?, 'reward', ?, ?)
            """,
            (
                new_id("led"),
                user_id,
                -cost,
                new_balance,
                redemption_id,
                now,
            ),
        )

        row = conn.execute(
            "SELECT * FROM reward_redemptions WHERE id = ?",
            (redemption_id,),
        ).fetchone()
        return _redemption_payload(conn, row)
