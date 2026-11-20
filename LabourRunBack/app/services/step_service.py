from __future__ import annotations

import sqlite3
from typing import Any

from ..config import Settings
from ..db import get_conn, transaction
from ..errors import AppError, ErrorCode
from ..ids import new_id
from ..security import decrypt_text
from ..timeutil import format_cents, today_shanghai, utc_now_iso
from ..wx import decrypt_we_run_data, extract_step_days, validate_watermark
from .common import get_current_challenge, get_int_config, row_to_challenge
from .coupon_service import get_account_row, serialize_account


def build_step_summary(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    today = today_shanghai()
    row = conn.execute(
        """
        SELECT *
        FROM daily_steps
        WHERE user_id = ? AND stat_date = ?
        """,
        (user_id, today),
    ).fetchone()

    daily_cap = get_int_config(conn, "daily_cap_steps", 12000)
    steps_per_coupon = get_int_config(conn, "steps_per_coupon", 10000)

    steps = max(int(row["steps"]), 0) if row is not None else 0
    exchanged = max(int(row["exchanged_steps"]), 0) if row is not None else 0
    available = max(steps - exchanged, 0)
    remaining_cap = max(daily_cap - exchanged, 0)
    convertible = min(available, remaining_cap)
    coupon_cents = convertible * 100 // steps_per_coupon

    return {
        "today_steps": steps,
        "exchanged_steps": exchanged,
        "convertible_steps": convertible,
        "convertible_coupons": format_cents(coupon_cents),
        "daily_cap_steps": daily_cap,
        "steps_per_coupon": steps_per_coupon,
        "last_synced_at": row["synced_at"] if row is not None else None,
    }


def get_steps_data(settings: Settings, user_id: str) -> dict[str, Any]:
    with get_conn(settings) as conn:
        account = serialize_account(get_account_row(conn, user_id))
        summary = build_step_summary(conn, user_id)
        challenge = get_current_challenge(conn)

    return {
        "coupon_account": account,
        "step_summary": summary,
        "challenge": row_to_challenge(challenge) if challenge is not None else None,
    }


def sync_steps(settings: Settings, user_id: str, body: Any) -> dict[str, Any]:
    today = today_shanghai()

    if settings.wx_mock:
        if body.mock_steps is None:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                400,
                "mock 模式需要提供 mockSteps",
            )
        days = {today: int(body.mock_steps)}
        source = "mock"
    else:
        if body.mock_steps is not None:
            raise AppError(
                ErrorCode.MOCK_DISABLED,
                400,
                "生产模式不支持 mockSteps",
            )
        if not body.encrypted_data or not body.iv:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                400,
                "需要提供 encryptedData + iv",
            )

        with get_conn(settings) as conn:
            user = conn.execute(
                "SELECT session_key_enc FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

        if user is None or not user["session_key_enc"]:
            raise AppError(
                ErrorCode.WX_SESSION_EXPIRED,
                401,
                "微信登录状态已失效，请重新登录",
            )

        session_key = decrypt_text(settings, user["session_key_enc"])
        try:
            payload = decrypt_we_run_data(
                session_key,
                body.encrypted_data,
                body.iv,
            )
        except (ValueError, TypeError, KeyError) as exc:
            raise AppError(
                ErrorCode.WX_SESSION_EXPIRED,
                401,
                "微信运动数据解密失败，请重新登录",
            ) from exc

        validate_watermark(settings, payload)
        days = extract_step_days(payload)
        source = "werun"

    now = utc_now_iso()
    with transaction(settings) as conn:
        for stat_date, steps in days.items():
            conn.execute(
                """
                INSERT INTO daily_steps
                    (id, user_id, stat_date, steps, exchanged_steps,
                     source, synced_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
                ON CONFLICT(user_id, stat_date) DO UPDATE SET
                    steps = excluded.steps,
                    source = excluded.source,
                    synced_at = excluded.synced_at,
                    updated_at = excluded.updated_at
                """,
                (
                    new_id("step"),
                    user_id,
                    stat_date,
                    max(int(steps), 0),
                    source,
                    now,
                    now,
                    now,
                ),
            )

        account = serialize_account(get_account_row(conn, user_id))
        summary = build_step_summary(conn, user_id)

    return {
        "coupon_account": account,
        "step_summary": summary,
    }


def _exchange_payload(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
) -> dict[str, Any]:
    return {
        "exchange": {
            "id": row["id"],
            "steps": row["steps"],
            "coupon_amount": format_cents(row["coupon_cents"]),
            "steps_per_coupon": row["steps_per_coupon"],
            "created_at": row["created_at"],
        },
        "coupon_account": serialize_account(
            get_account_row(conn, row["user_id"])
        ),
        "step_summary": build_step_summary(conn, row["user_id"]),
    }


def exchange_steps(
    settings: Settings,
    user_id: str,
    request_id: str,
) -> dict[str, Any]:
    try:
        with transaction(settings) as conn:
            existing = conn.execute(
                """
                SELECT *
                FROM exchange_records
                WHERE user_id = ? AND request_id = ?
                """,
                (user_id, request_id),
            ).fetchone()
            if existing is not None:
                return _exchange_payload(conn, existing)

            today = today_shanghai()
            step_row = conn.execute(
                """
                SELECT *
                FROM daily_steps
                WHERE user_id = ? AND stat_date = ?
                """,
                (user_id, today),
            ).fetchone()

            if step_row is None or int(step_row["steps"]) <= 0:
                raise AppError(
                    ErrorCode.NO_STEP_DATA,
                    422,
                    "暂无步数数据，请先同步步数",
                )

            daily_cap = get_int_config(conn, "daily_cap_steps", 12000)
            steps_per_coupon = get_int_config(conn, "steps_per_coupon", 10000)

            steps = max(int(step_row["steps"]), 0)
            exchanged = max(int(step_row["exchanged_steps"]), 0)
            available = max(steps - exchanged, 0)
            remaining_cap = max(daily_cap - exchanged, 0)
            steps_to_exchange = min(available, remaining_cap)

            if steps_to_exchange <= 0:
                if available <= 0:
                    raise AppError(
                        ErrorCode.NO_CONVERTIBLE_STEPS,
                        422,
                        "暂无可兑换步数",
                    )
                raise AppError(
                    ErrorCode.DAILY_CAP_REACHED,
                    422,
                    "已达到每日兑换上限",
                )

            coupon_cents = steps_to_exchange * 100 // steps_per_coupon
            if coupon_cents <= 0:
                raise AppError(
                    ErrorCode.EXCHANGE_AMOUNT_TOO_SMALL,
                    422,
                    "可兑金额不足 0.01 兑换券",
                )

            now = utc_now_iso()
            conn.execute(
                """
                UPDATE daily_steps
                SET exchanged_steps = exchanged_steps + ?,
                    updated_at = ?
                WHERE user_id = ? AND stat_date = ?
                """,
                (steps_to_exchange, now, user_id, today),
            )

            account = get_account_row(conn, user_id)
            old_balance = int(account["balance_cents"]) if account else 0
            new_balance = old_balance + coupon_cents

            conn.execute(
                """
                INSERT INTO coupon_accounts
                    (user_id, balance_cents, total_earned_cents,
                     total_spent_cents, updated_at)
                VALUES (?, ?, ?, 0, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    balance_cents = coupon_accounts.balance_cents + excluded.balance_cents,
                    total_earned_cents = coupon_accounts.total_earned_cents + excluded.total_earned_cents,
                    updated_at = excluded.updated_at
                """,
                (user_id, coupon_cents, coupon_cents, now),
            )

            exchange_id = new_id("ex")
            conn.execute(
                """
                INSERT INTO exchange_records
                    (id, user_id, stat_date, steps, coupon_cents,
                     steps_per_coupon, request_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'success', ?)
                """,
                (
                    exchange_id,
                    user_id,
                    today,
                    steps_to_exchange,
                    coupon_cents,
                    steps_per_coupon,
                    request_id,
                    now,
                ),
            )

            conn.execute(
                """
                INSERT INTO coupon_ledger
                    (id, user_id, type, amount_cents, balance_after_cents,
                     ref_type, ref_id, created_at)
                VALUES (?, ?, 'exchange', ?, ?, 'exchange', ?, ?)
                """,
                (
                    new_id("led"),
                    user_id,
                    coupon_cents,
                    new_balance,
                    exchange_id,
                    now,
                ),
            )

            row = conn.execute(
                "SELECT * FROM exchange_records WHERE id = ?",
                (exchange_id,),
            ).fetchone()
            return _exchange_payload(conn, row)

    except sqlite3.IntegrityError as exc:
        with get_conn(settings) as conn:
            existing = conn.execute(
                """
                SELECT *
                FROM exchange_records
                WHERE user_id = ? AND request_id = ?
                """,
                (user_id, request_id),
            ).fetchone()
            if existing is not None:
                return _exchange_payload(conn, existing)

        raise AppError(
            ErrorCode.INTERNAL_ERROR,
            500,
            "兑换处理冲突，请重试",
        ) from exc
