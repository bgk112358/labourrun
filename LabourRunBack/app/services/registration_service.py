from __future__ import annotations

import sqlite3
from typing import Any

from ..config import Settings
from ..db import get_conn, transaction
from ..errors import AppError, ErrorCode
from ..ids import new_id
from ..timeutil import utc_now_iso
from .common import get_current_activity, row_to_registration


def get_registration(settings: Settings, user_id: str, registration_id: str) -> dict:
    with get_conn(settings) as conn:
        row = conn.execute(
            "SELECT * FROM registrations WHERE id = ? AND user_id = ?",
            (registration_id, user_id),
        ).fetchone()
    if row is None:
        raise AppError(ErrorCode.REGISTRATION_NOT_FOUND, 404, "报名记录不存在")
    return row_to_registration(row)


def create_or_restore(
    settings: Settings,
    user_id: str,
    body: Any,
) -> dict:
    try:
        with transaction(settings) as conn:
            activity = get_current_activity(conn)
            if activity is None:
                raise AppError(ErrorCode.ACTIVITY_NOT_FOUND, 404, "活动不存在")

            existing = conn.execute(
                """
                SELECT *
                FROM registrations
                WHERE activity_id = ? AND user_id = ?
                """,
                (activity["id"], user_id),
            ).fetchone()

            phone_owner = conn.execute(
                """
                SELECT id
                FROM registrations
                WHERE activity_id = ? AND phone = ? AND user_id <> ?
                """,
                (activity["id"], body.phone, user_id),
            ).fetchone()
            if phone_owner is not None:
                raise AppError(
                    ErrorCode.REGISTRATION_DUPLICATE,
                    409,
                    "该手机号已报名",
                )

            now = utc_now_iso()
            if existing is not None:
                if existing["status"] == "registered":
                    raise AppError(
                        ErrorCode.REGISTRATION_DUPLICATE,
                        409,
                        "您已报名",
                    )
                registration_id = existing["id"]
                conn.execute(
                    """
                    UPDATE registrations
                    SET real_name = ?, phone = ?, company = ?,
                        status = 'registered', cancelled_at = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        body.real_name,
                        body.phone,
                        body.company,
                        now,
                        registration_id,
                    ),
                )
            else:
                registration_id = new_id("reg")
                conn.execute(
                    """
                    INSERT INTO registrations
                        (id, activity_id, user_id, real_name, phone, company,
                         status, created_at, updated_at, cancelled_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'registered', ?, ?, NULL)
                    """,
                    (
                        registration_id,
                        activity["id"],
                        user_id,
                        body.real_name,
                        body.phone,
                        body.company,
                        now,
                        now,
                    ),
                )

            row = conn.execute(
                "SELECT * FROM registrations WHERE id = ?",
                (registration_id,),
            ).fetchone()

        return row_to_registration(row)
    except sqlite3.IntegrityError as exc:
        raise AppError(
            ErrorCode.REGISTRATION_DUPLICATE,
            409,
            "该用户或手机号已报名",
        ) from exc


def update_registration(
    settings: Settings,
    user_id: str,
    registration_id: str,
    body: Any,
) -> dict:
    try:
        with transaction(settings) as conn:
            row = conn.execute(
                """
                SELECT *
                FROM registrations
                WHERE id = ? AND user_id = ?
                """,
                (registration_id, user_id),
            ).fetchone()
            if row is None:
                raise AppError(
                    ErrorCode.REGISTRATION_NOT_FOUND,
                    404,
                    "报名记录不存在",
                )
            if row["status"] != "registered":
                raise AppError(
                    ErrorCode.REGISTRATION_CANCELLED,
                    409,
                    "报名已取消，请重新报名",
                )

            updates: dict[str, Any] = {}
            if body.real_name is not None:
                updates["real_name"] = body.real_name
            if body.phone is not None:
                conflict = conn.execute(
                    """
                    SELECT id
                    FROM registrations
                    WHERE activity_id = ? AND phone = ? AND id <> ?
                    """,
                    (row["activity_id"], body.phone, registration_id),
                ).fetchone()
                if conflict is not None:
                    raise AppError(
                        ErrorCode.REGISTRATION_DUPLICATE,
                        409,
                        "该手机号已报名",
                    )
                updates["phone"] = body.phone
            if body.company is not None:
                updates["company"] = body.company

            updates["updated_at"] = utc_now_iso()
            assignments = ", ".join(f"{key} = ?" for key in updates)
            conn.execute(
                f"UPDATE registrations SET {assignments} WHERE id = ?",
                (*updates.values(), registration_id),
            )

            row = conn.execute(
                "SELECT * FROM registrations WHERE id = ?",
                (registration_id,),
            ).fetchone()

        return row_to_registration(row)
    except sqlite3.IntegrityError as exc:
        raise AppError(
            ErrorCode.REGISTRATION_DUPLICATE,
            409,
            "该手机号已报名",
        ) from exc


def cancel_registration(
    settings: Settings,
    user_id: str,
    registration_id: str,
) -> dict:
    with transaction(settings) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM registrations
            WHERE id = ? AND user_id = ?
            """,
            (registration_id, user_id),
        ).fetchone()
        if row is None:
            raise AppError(
                ErrorCode.REGISTRATION_NOT_FOUND,
                404,
                "报名记录不存在",
            )

        if row["status"] == "registered":
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE registrations
                SET status = 'cancelled', cancelled_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, registration_id),
            )

        row = conn.execute(
            "SELECT * FROM registrations WHERE id = ?",
            (registration_id,),
        ).fetchone()

    return row_to_registration(row)
