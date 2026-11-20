from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from ..config import Settings
from ..deps import get_current_user, get_settings
from ..models import (
    ApiResponse,
    RegistrationCreate,
    RegistrationOut,
    RegistrationUpdate,
)
from ..response import ok
from ..services import registration_service

router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.post("", response_model=ApiResponse[RegistrationOut])
def create_registration(
    body: RegistrationCreate,
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        registration_service.create_or_restore(settings, user["id"], body),
    )


@router.patch("/{registration_id}", response_model=ApiResponse[RegistrationOut])
def update_registration(
    registration_id: str,
    body: RegistrationUpdate,
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        registration_service.update_registration(
            settings,
            user["id"],
            registration_id,
            body,
        ),
    )


@router.post(
    "/{registration_id}/cancel",
    response_model=ApiResponse[RegistrationOut],
)
def cancel_registration(
    registration_id: str,
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        registration_service.cancel_registration(
            settings,
            user["id"],
            registration_id,
        ),
    )
