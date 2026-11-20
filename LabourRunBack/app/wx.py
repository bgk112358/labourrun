from __future__ import annotations

import base64
import json
import os
import re
from typing import Any

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .config import Settings
from .errors import AppError, ErrorCode
from .timeutil import timestamp_to_shanghai_date, today_shanghai

WX_LOGIN_URL = "https://api.weixin.qq.com/sns/jscode2session"


def code2session(settings: Settings, code: str) -> dict[str, Any]:
    if settings.wx_mock:
        raw = code[5:] if code.startswith("mock:") else code
        safe = re.sub(r"[^A-Za-z0-9_]", "_", raw)[:64] or "demo"
        return {
            "openid": f"mock_{safe}",
            "session_key": base64.b64encode(os.urandom(16)).decode("ascii"),
            "unionid": None,
        }

    if not settings.wx_secret:
        raise AppError(ErrorCode.WX_CONFIG_ERROR, 500, "服务端未配置 WX_SECRET")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                WX_LOGIN_URL,
                params={
                    "appid": settings.wx_appid,
                    "secret": settings.wx_secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise AppError(
            ErrorCode.WX_LOGIN_FAILED,
            502,
            "微信登录服务暂不可用，请稍后重试",
        ) from exc

    if data.get("errcode") or not data.get("openid") or not data.get("session_key"):
        raise AppError(
            ErrorCode.WX_LOGIN_FAILED,
            401,
            data.get("errmsg") or "微信登录失败",
        )

    return {
        "openid": data["openid"],
        "session_key": data["session_key"],
        "unionid": data.get("unionid"),
    }


def decrypt_we_run_data(
    session_key_b64: str,
    encrypted_data_b64: str,
    iv_b64: str,
) -> dict[str, Any]:
    key = base64.b64decode(session_key_b64.encode("ascii"), validate=True)
    iv = base64.b64decode(iv_b64.encode("ascii"), validate=True)
    ciphertext = base64.b64decode(encrypted_data_b64.encode("ascii"), validate=True)

    if len(key) != 16 or len(iv) != 16:
        raise ValueError("invalid AES-128 key or iv length")

    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    if not padded:
        raise ValueError("empty plaintext")

    pad = padded[-1]
    if pad < 1 or pad > 16 or padded[-pad:] != bytes([pad]) * pad:
        raise ValueError("invalid PKCS#7 padding")

    data = json.loads(padded[:-pad].decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("decrypted payload is not an object")
    return data


def validate_watermark(settings: Settings, data: dict[str, Any]) -> None:
    watermark = data.get("watermark") or {}
    if watermark.get("appid") != settings.wx_appid:
        raise AppError(
            ErrorCode.WX_SESSION_EXPIRED,
            401,
            "微信运动数据校验失败，请重新登录",
        )


def extract_step_days(data: dict[str, Any]) -> dict[str, int]:
    step_info_list = data.get("stepInfoList") or []
    days: dict[str, int] = {}

    for item in step_info_list:
        if not isinstance(item, dict):
            continue
        timestamp = item.get("timestamp")
        step = item.get("step")
        if not isinstance(timestamp, (int, float)) or not isinstance(step, int):
            continue
        if step < 0:
            continue
        stat_date = timestamp_to_shanghai_date(timestamp)
        days[stat_date] = max(days.get(stat_date, 0), step)

    days.setdefault(today_shanghai(), 0)
    return days
