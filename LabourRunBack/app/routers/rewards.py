from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from ..config import Settings
from ..deps import get_current_user, get_settings
from ..models import (
    ApiResponse,
    RewardRedeemData,
    RewardRedeemRequest,
)
from ..response import ok
from ..services import reward_service

router = APIRouter(tags=["rewards"])


@router.post(
    "/rewards/{reward_id}/redeem",
    response_model=ApiResponse[RewardRedeemData],
)
def redeem_reward(
    reward_id: str,
    body: RewardRedeemRequest,
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        reward_service.redeem_reward(
            settings,
            user["id"],
            reward_id,
            body.request_id,
        ),
    )
