from __future__ import annotations

import sqlite3

from fastapi import Depends, Request

from ..config import Settings
from ..db import get_conn
from ..deps import get_settings
from ..errors import AppError, ErrorCode
from .security import decode_admin_token


def get_current_admin(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> sqlite3.Row:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        raise AppError(ErrorCode.ADMIN_UNAUTHORIZED, 401, "管理员未登录")

    token = header[7:].strip()
    if not token:
        raise AppError(ErrorCode.ADMIN_UNAUTHORIZED, 401, "管理员未登录")

    payload = decode_admin_token(settings, token)
    with get_conn(settings) as conn:
        admin = conn.execute(
            "SELECT * FROM admin_users WHERE id = ?",
            (payload["sub"],),
        ).fetchone()

    if admin is None:
        raise AppError(
            ErrorCode.ADMIN_UNAUTHORIZED,
            401,
            "管理员账号不存在",
        )
    if admin["status"] != "active":
        raise AppError(
            ErrorCode.ADMIN_DISABLED,
            403,
            "管理员账号已禁用",
        )
    return admin


def require_super_admin(
    admin: sqlite3.Row = Depends(get_current_admin),
) -> sqlite3.Row:
    if admin["role"] != "super_admin":
        raise AppError(
            ErrorCode.ADMIN_FORBIDDEN,
            403,
            "需要超级管理员权限",
        )
    return admin
