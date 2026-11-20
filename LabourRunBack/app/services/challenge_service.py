from __future__ import annotations

from ..config import Settings
from ..db import get_conn
from ..errors import AppError, ErrorCode
from .common import get_current_challenge as fetch_current_challenge
from .common import row_to_challenge


def get_current(settings: Settings) -> dict:
    with get_conn(settings) as conn:
        row = fetch_current_challenge(conn)
    if row is None:
        raise AppError(ErrorCode.CHALLENGE_NOT_FOUND, 404, "挑战不存在")
    return row_to_challenge(row, include_rules=True)
