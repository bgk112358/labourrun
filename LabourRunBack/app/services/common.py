from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..errors import AppError, ErrorCode
from ..timeutil import format_cents


def _json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return value if isinstance(value, list) else []


def row_to_user(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "nickname": row["nickname"],
        "avatar_url": row["avatar_url"],
        "phone": row["phone"],
    }


def row_to_registration(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "activity_id": row["activity_id"],
        "real_name": row["real_name"],
        "phone": row["phone"],
        "company": row["company"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "cancelled_at": row["cancelled_at"],
    }


def row_to_activity(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "notice_text": row["notice_text"],
        "rules": _json_list(row["rules_json"]),
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "status": row["status"],
    }


def row_to_challenge(
    row: sqlite3.Row,
    *,
    include_rules: bool = False,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": row["id"],
        "title": row["title"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "target_steps": row["target_steps"],
        "deposit_coupons": format_cents(row["deposit_cents"]),
        "participant_count": row["participant_count"],
        "status": row["status"],
    }
    if include_rules:
        data["rules"] = _json_list(row["rules_json"])
    return data


def get_config(conn: sqlite3.Connection, key: str, default: str) -> str:
    row = conn.execute(
        "SELECT value FROM app_config WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        return default
    return str(row["value"])


def get_int_config(conn: sqlite3.Connection, key: str, default: int) -> int:
    raw = get_config(conn, key, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise AppError(
            ErrorCode.CONFIG_ERROR,
            500,
            f"配置项 {key} 不是有效整数",
        ) from exc
    if value <= 0:
        raise AppError(
            ErrorCode.CONFIG_ERROR,
            500,
            f"配置项 {key} 必须大于 0",
        )
    return value


def get_current_activity(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT *
        FROM activities
        ORDER BY
            CASE status
                WHEN 'ongoing' THEN 0
                WHEN 'upcoming' THEN 1
                ELSE 2
            END,
            created_at DESC
        LIMIT 1
        """
    ).fetchone()


def get_current_challenge(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT *
        FROM challenges
        ORDER BY
            CASE status
                WHEN 'ongoing' THEN 0
                WHEN 'upcoming' THEN 1
                ELSE 2
            END,
            created_at DESC
        LIMIT 1
        """
    ).fetchone()
