from __future__ import annotations

import sqlite3

from fastapi import Depends, Request

from .config import Settings
from .db import get_conn
from .errors import AppError, ErrorCode
from .security import decode_token


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> sqlite3.Row:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        raise AppError(ErrorCode.UNAUTHORIZED, 401, "未登录")

    token = header[7:].strip()
    if not token:
        raise AppError(ErrorCode.UNAUTHORIZED, 401, "未登录")

    payload = decode_token(settings, token)
    with get_conn(settings) as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (payload["sub"],),
        ).fetchone()

    if user is None:
        raise AppError(ErrorCode.UNAUTHORIZED, 401, "用户不存在")
    return user
