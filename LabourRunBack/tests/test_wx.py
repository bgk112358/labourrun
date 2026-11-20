from __future__ import annotations

import base64
import json
import os
from datetime import datetime

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.config import Settings
from app.errors import AppError, ErrorCode
from app.timeutil import SHANGHAI_TZ
from app.wx import (
    code2session,
    decrypt_we_run_data,
    extract_step_days,
    validate_watermark,
)


def _settings() -> Settings:
    return Settings(
        host="127.0.0.1",
        port=3000,
        db_path=":memory:",
        jwt_secret="test-secret-please-use-32-bytes-ok",
        jwt_ttl_seconds=3600,
        wx_appid="wx_test",
        wx_secret="",
        wx_mock=True,
        log_level="error",
    )


def _encrypt_payload(payload: dict) -> tuple[str, str, str]:
    session_key = os.urandom(16)
    iv = os.urandom(16)
    plain = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    pad = 16 - len(plain) % 16
    padded = plain + bytes([pad]) * pad

    encryptor = Cipher(algorithms.AES(session_key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return (
        base64.b64encode(session_key).decode("ascii"),
        base64.b64encode(ciphertext).decode("ascii"),
        base64.b64encode(iv).decode("ascii"),
    )


def test_decrypt_we_run_data_and_extract_days():
    timestamp = int(
        datetime(2026, 11, 17, 8, 0, tzinfo=SHANGHAI_TZ).timestamp()
    )
    payload = {
        "stepInfoList": [
            {"timestamp": timestamp, "step": 6638},
        ],
        "watermark": {"appid": "wx_test", "timestamp": timestamp},
    }
    session_key, encrypted_data, iv = _encrypt_payload(payload)

    decrypted = decrypt_we_run_data(session_key, encrypted_data, iv)
    assert decrypted["stepInfoList"][0]["step"] == 6638

    validate_watermark(_settings(), decrypted)
    days = extract_step_days(decrypted)
    assert days["2026-11-17"] == 6638


def test_watermark_mismatch():
    with pytest.raises(AppError) as exc_info:
        validate_watermark(
            _settings(),
            {"watermark": {"appid": "wx_other"}},
        )
    assert exc_info.value.code == ErrorCode.WX_SESSION_EXPIRED


def test_mock_code2session():
    session = code2session(_settings(), "mock:demo")
    assert session["openid"] == "mock_demo"
    assert session["session_key"]
