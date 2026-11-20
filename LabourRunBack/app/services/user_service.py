from __future__ import annotations

from ..config import Settings
from ..db import get_conn, transaction
from ..errors import AppError, ErrorCode
from ..timeutil import utc_now_iso
from .common import row_to_user


def get_user(settings: Settings, user_id: str) -> dict:
    with get_conn(settings) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        raise AppError(ErrorCode.UNAUTHORIZED, 401, "用户不存在")
    return row_to_user(row)


def update_nickname(settings: Settings, user_id: str, nickname: str) -> dict:
    now = utc_now_iso()
    with transaction(settings) as conn:
        conn.execute(
            "UPDATE users SET nickname = ?, updated_at = ? WHERE id = ?",
            (nickname, now, user_id),
        )
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        raise AppError(ErrorCode.UNAUTHORIZED, 401, "用户不存在")
    return row_to_user(row)
