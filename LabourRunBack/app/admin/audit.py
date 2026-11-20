from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import Request

from ..ids import new_id
from ..timeutil import utc_now_iso


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else None


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, default=str)


def write_audit(
    conn: sqlite3.Connection,
    request: Request | None,
    admin_id: str | None,
    admin_username: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    before: Any = None,
    after: Any = None,
) -> None:
    conn.execute(
        """
        INSERT INTO admin_audit_logs
            (id, admin_id, admin_username, action, resource_type,
             resource_id, before_json, after_json, ip, user_agent, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("aud"),
            admin_id,
            admin_username,
            action,
            resource_type,
            resource_id,
            _json(before),
            _json(after),
            client_ip(request),
            request.headers.get("User-Agent") if request else None,
            utc_now_iso(),
        ),
    )
