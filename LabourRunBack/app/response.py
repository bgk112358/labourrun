from __future__ import annotations

from typing import Any

from fastapi import Request

from .ids import new_id


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or new_id("req")


def ok(request: Request, data: Any, message: str = "ok") -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": data,
        "requestId": get_request_id(request),
    }


def error_payload(
    request: Request,
    code: int,
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data,
        "requestId": get_request_id(request),
    }
