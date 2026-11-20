from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..config import Settings
from ..deps import get_settings
from ..models import ApiResponse, LoginData, LoginRequest
from ..response import ok
from ..services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[LoginData])
def login(
    body: LoginRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    return ok(request, auth_service.login(settings, body.code))
