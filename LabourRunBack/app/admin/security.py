from __future__ import annotations

import base64
import hashlib
import hmac
import os
import threading
import time
from datetime import datetime, timedelta, timezone

import jwt

from ..config import Settings
from ..errors import AppError, ErrorCode

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32

_LOGIN_WINDOW_SECONDS = 900
_LOGIN_MAX_FAILURES = 5
_login_failures: dict[str, list[float]] = {}
_login_lock = threading.Lock()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return "scrypt${}${}${}${}${}".format(
        SCRYPT_N,
        SCRYPT_R,
        SCRYPT_P,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        parts = stored.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False
        n, r, p = int(parts[1]), int(parts[2]), int(parts[3])
        salt = base64.b64decode(parts[4].encode("ascii"))
        expected = base64.b64decode(parts[5].encode("ascii"))
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError, KeyError):
        return False


def validate_password_policy(password: str) -> None:
    has_letter = any(ch.isalpha() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    if len(password) < 10 or not has_letter or not has_digit:
        raise AppError(
            ErrorCode.ADMIN_PASSWORD_POLICY,
            400,
            "密码至少 10 位，且同时包含字母和数字",
        )


def create_admin_token(settings: Settings, admin) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": admin["id"],
        "aud": "labourrun-admin",
        "role": admin["role"],
        "typ": "admin",
        "iat": now,
        "exp": now + timedelta(seconds=settings.admin_jwt_ttl_seconds),
    }
    return jwt.encode(
        payload,
        settings.admin_jwt_secret,
        algorithm="HS256",
    )


def decode_admin_token(settings: Settings, token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.admin_jwt_secret,
            algorithms=["HS256"],
            audience="labourrun-admin",
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(
            ErrorCode.ADMIN_TOKEN_EXPIRED,
            401,
            "管理员登录已过期，请重新登录",
        ) from exc
    except jwt.PyJWTError as exc:
        raise AppError(
            ErrorCode.ADMIN_UNAUTHORIZED,
            401,
            "管理员未登录或登录无效",
        ) from exc

    if payload.get("typ") != "admin" or not payload.get("sub"):
        raise AppError(
            ErrorCode.ADMIN_UNAUTHORIZED,
            401,
            "管理员未登录或登录无效",
        )
    return payload


def _prune(key: str, now: float) -> list[float]:
    values = [
        value
        for value in _login_failures.get(key, [])
        if now - value < _LOGIN_WINDOW_SECONDS
    ]
    if values:
        _login_failures[key] = values
    else:
        _login_failures.pop(key, None)
    return values


def check_login_allowed(key: str) -> None:
    with _login_lock:
        values = _prune(key, time.monotonic())
        if len(values) >= _LOGIN_MAX_FAILURES:
            raise AppError(
                ErrorCode.ADMIN_RATE_LIMITED,
                429,
                "登录失败次数过多，请 15 分钟后再试",
            )


def record_login_failure(key: str) -> None:
    with _login_lock:
        now = time.monotonic()
        values = _prune(key, now)
        values.append(now)
        _login_failures[key] = values


def clear_login_failures(key: str) -> None:
    with _login_lock:
        _login_failures.pop(key, None)
