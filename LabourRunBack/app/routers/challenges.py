from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..config import Settings
from ..deps import get_settings
from ..models import ApiResponse, ChallengeOut
from ..response import ok
from ..services import challenge_service

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("/current", response_model=ApiResponse[ChallengeOut])
def get_current_challenge(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    return ok(request, challenge_service.get_current(settings))
