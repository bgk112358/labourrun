from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from ..config import Settings
from ..deps import get_current_user, get_settings
from ..models import ApiResponse, HomeData
from ..response import ok
from ..services import home_service

router = APIRouter(tags=["home"])


@router.get("/home", response_model=ApiResponse[HomeData])
def get_home(
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(request, home_service.get_home(settings, user["id"]))
