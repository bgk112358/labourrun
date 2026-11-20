from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from ..config import Settings
from ..deps import get_current_user, get_settings
from ..models import ApiResponse, MeUpdate, UserOut
from ..response import ok
from ..services import user_service

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=ApiResponse[UserOut])
def get_me(
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(request, user_service.get_user(settings, user["id"]))


@router.patch("", response_model=ApiResponse[UserOut])
def update_me(
    body: MeUpdate,
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        user_service.update_nickname(settings, user["id"], body.nickname),
    )
