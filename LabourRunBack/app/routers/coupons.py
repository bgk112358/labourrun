from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query, Request

from ..config import Settings
from ..deps import get_current_user, get_settings
from ..models import ApiResponse, LedgerPage
from ..response import ok
from ..services import coupon_service

router = APIRouter(prefix="/coupons", tags=["coupons"])


@router.get("/ledger", response_model=ApiResponse[LedgerPage])
def get_ledger(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    user: sqlite3.Row = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        coupon_service.get_ledger(
            settings,
            user["id"],
            page,
            page_size,
        ),
    )
