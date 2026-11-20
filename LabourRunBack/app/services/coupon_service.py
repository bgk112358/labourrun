from __future__ import annotations

import sqlite3
from typing import Any

from ..config import Settings
from ..db import get_conn
from ..timeutil import format_cents


def get_account_row(
    conn: sqlite3.Connection,
    user_id: str,
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM coupon_accounts WHERE user_id = ?",
        (user_id,),
    ).fetchone()


def serialize_account(row: sqlite3.Row | None) -> dict[str, str]:
    if row is None:
        return {
            "balance": "0.00",
            "total_earned": "0.00",
            "total_spent": "0.00",
        }
    return {
        "balance": format_cents(row["balance_cents"]),
        "total_earned": format_cents(row["total_earned_cents"]),
        "total_spent": format_cents(row["total_spent_cents"]),
    }


def get_ledger(
    settings: Settings,
    user_id: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    offset = (page - 1) * page_size
    with get_conn(settings) as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM coupon_ledger WHERE user_id = ?",
            (user_id,),
        ).fetchone()["n"]
        rows = conn.execute(
            """
            SELECT *
            FROM coupon_ledger
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, page_size, offset),
        ).fetchall()

    items = [
        {
            "id": row["id"],
            "type": row["type"],
            "amount": format_cents(row["amount_cents"]),
            "balance_after": format_cents(row["balance_after_cents"]),
            "ref_type": row["ref_type"],
            "ref_id": row["ref_id"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
