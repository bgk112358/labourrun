from __future__ import annotations

from ..config import Settings
from ..db import transaction
from ..ids import new_id
from ..security import create_token, encrypt_text
from ..timeutil import utc_now_iso
from ..wx import code2session
from .common import row_to_user


def login(settings: Settings, code: str) -> dict:
    session = code2session(settings, code)
    openid = session["openid"]
    session_key_enc = encrypt_text(settings, session["session_key"])
    now = utc_now_iso()

    with transaction(settings) as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE openid = ?",
            (openid,),
        ).fetchone()

        if user is None:
            user_id = new_id("usr")
            conn.execute(
                """
                INSERT INTO users
                    (id, openid, unionid, avatar_url, nickname, phone,
                     session_key_enc, created_at, updated_at)
                VALUES (?, ?, ?, NULL, NULL, NULL, ?, ?, ?)
                """,
                (
                    user_id,
                    openid,
                    session.get("unionid"),
                    session_key_enc,
                    now,
                    now,
                ),
            )
        else:
            user_id = user["id"]
            conn.execute(
                """
                UPDATE users
                SET unionid = COALESCE(?, unionid),
                    session_key_enc = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (session.get("unionid"), session_key_enc, now, user_id),
            )

        conn.execute(
            """
            INSERT OR IGNORE INTO coupon_accounts
                (user_id, balance_cents, total_earned_cents, total_spent_cents, updated_at)
            VALUES (?, 0, 0, 0, ?)
            """,
            (user_id, now),
        )

        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return {
        "token": create_token(settings, user_id),
        "expires_in": settings.jwt_ttl_seconds,
        "user": row_to_user(user),
    }
