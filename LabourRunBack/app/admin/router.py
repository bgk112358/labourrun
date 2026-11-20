from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query, Request, Response

from ..config import Settings
from ..db import transaction
from ..deps import get_settings
from ..models import ApiResponse
from ..response import ok
from . import service
from .audit import write_audit
from .deps import get_current_admin
from .models import (
    ActivityAdminOut,
    ActivityAdminUpdate,
    ActivityImageOut,
    AdminLoginData,
    AdminLoginRequest,
    AdminOut,
    AuditLogDetail,
    AuditLogPage,
    ChallengeAdminOut,
    ChallengeAdminUpdate,
    DashboardData,
    RegistrationAdminDetail,
    RegistrationAdminPage,
)

router = APIRouter()


@router.post("/auth/login", response_model=ApiResponse[AdminLoginData])
def admin_login(
    body: AdminLoginRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        service.admin_login(
            settings,
            request,
            body.username,
            body.password,
        ),
    )


@router.get("/auth/me", response_model=ApiResponse[AdminOut])
def admin_me(
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
):
    return ok(request, service.admin_public(admin))


@router.post("/auth/logout")
def admin_logout(
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    with transaction(settings) as conn:
        write_audit(
            conn,
            request,
            admin["id"],
            admin["username"],
            "logout",
            "auth",
            admin["id"],
        )
    return ok(request, None)


@router.get("/dashboard", response_model=ApiResponse[DashboardData])
def dashboard(
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(request, service.get_dashboard(settings))


@router.get("/activity", response_model=ApiResponse[ActivityAdminOut])
def get_activity(
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(request, service.get_activity(settings))


@router.put("/activity", response_model=ApiResponse[ActivityAdminOut])
def update_activity(
    body: ActivityAdminUpdate,
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        service.update_activity(settings, request, admin, body),
    )


@router.post(
    "/activity/image",
    response_model=ApiResponse[ActivityImageOut],
)
async def upload_activity_image(
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    content = await request.body()
    return ok(
        request,
        service.process_activity_image(settings, content),
    )


@router.get("/challenge", response_model=ApiResponse[ChallengeAdminOut])
def get_challenge(
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(request, service.get_challenge(settings))


@router.put("/challenge", response_model=ApiResponse[ChallengeAdminOut])
def update_challenge(
    body: ChallengeAdminUpdate,
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        service.update_challenge(settings, request, admin, body),
    )


@router.get(
    "/registrations",
    response_model=ApiResponse[RegistrationAdminPage],
)
def list_registrations(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    keyword: str | None = Query(None, max_length=100),
    status: str | None = Query(None),
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        service.list_registrations(
            settings,
            page,
            page_size,
            keyword,
            status,
        ),
    )


@router.get("/registrations/export")
def export_registrations(
    request: Request,
    keyword: str | None = Query(None, max_length=100),
    status: str | None = Query(None),
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    content = service.export_registrations(
        settings,
        admin,
        keyword,
        status,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="registrations.csv"'
            )
        },
    )


@router.get(
    "/registrations/{registration_id}",
    response_model=ApiResponse[RegistrationAdminDetail],
)
def get_registration(
    registration_id: str,
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        service.get_registration(settings, admin, registration_id),
    )


@router.get("/audit-logs", response_model=ApiResponse[AuditLogPage])
def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    admin_id: str | None = Query(None, alias="adminId"),
    resource_type: str | None = Query(None, alias="resourceType"),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(
        request,
        service.list_audit_logs(
            settings,
            page,
            page_size,
            admin_id,
            resource_type,
            from_date,
            to_date,
        ),
    )


@router.get(
    "/audit-logs/{log_id}",
    response_model=ApiResponse[AuditLogDetail],
)
def get_audit_log(
    log_id: str,
    request: Request,
    admin: sqlite3.Row = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
):
    return ok(request, service.get_audit_log(settings, log_id))
