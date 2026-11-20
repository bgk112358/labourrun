from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.fernet import Fernet, InvalidToken

from .config import Settings
from .errors import AppError, ErrorCode


def create_token(settings: Settings, user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(settings: Settings, token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AppError(ErrorCode.TOKEN_EXPIRED, 401, "登录已过期，请重新登录") from exc
    except jwt.PyJWTError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, 401, "未登录或登录无效") from exc

    if not payload.get("sub"):
        raise AppError(ErrorCode.UNAUTHORIZED, 401, "未登录或登录无效")
    return payload


def _fernet(settings: Settings) -> Fernet:
    digest = hashlib.sha256(settings.jwt_secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_text(settings: Settings, text: str) -> str:
    return _fernet(settings).encrypt(text.encode("utf-8")).decode("ascii")


def decrypt_text(settings: Settings, token: str) -> str:
    try:
        return _fernet(settings).decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise AppError(
            ErrorCode.WX_SESSION_EXPIRED,
            401,
            "微信登录状态已失效，请重新登录",
        ) from exc
