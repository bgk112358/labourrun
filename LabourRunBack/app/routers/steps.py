from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from ..config import Settings
from ..deps import get_current_user, get_settings
from ..models import (
    ApiResponse,
    ExchangeData,
    ExchangeRequest,
    StepsData,
    StepSyncRequest,
    SyncData,
)
from ..response import ok
from ..services import step_service

router = APIRouter(prefix="/steps", tags=["steps"])


@router.get("", response_model=ApiResponse[StepsData])
def get_steps(
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(request, step_service.get_steps_data(settings, user["id"]))


@router.post("/sync", response_model=ApiResponse[SyncData])
def sync_steps(
    body: StepSyncRequest,
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        step_service.sync_steps(settings, user["id"], body),
    )


@router.post("/exchange", response_model=ApiResponse[ExchangeData])
def exchange_steps(
    body: ExchangeRequest,
    request: Request,
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        step_service.exchange_steps(
            settings,
            user["id"],
            body.request_id,
        ),
    )
