from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .admin.router import router as admin_router
from .config import Settings, load_settings
from .db import init_db
from .errors import AppError, ErrorCode
from .response import error_payload
from .routers import (
    auth,
    challenges,
    coupons,
    health,
    home,
    me,
    registrations,
    steps,
)

logger = logging.getLogger("labourrun")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    app = FastAPI(
        title="LabourRun API",
        version="1.0.0",
        description="LabourRun 微信小程序后端接口",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.settings = settings
    init_db(settings)

    admin_origins = [
        origin.strip()
        for origin in settings.admin_origins.split(",")
        if origin.strip()
    ]
    if admin_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=admin_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.http_status,
            content=error_payload(
                request,
                exc.code,
                exc.message,
                exc.data,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        errors = [
            {
                "loc": list(item.get("loc", [])),
                "msg": item.get("msg", ""),
                "type": item.get("type", ""),
            }
            for item in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=error_payload(
                request,
                ErrorCode.VALIDATION_ERROR,
                "参数错误",
                {"errors": errors},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        if exc.status_code == 404:
            code = ErrorCode.NOT_FOUND
        elif exc.status_code == 405:
            code = ErrorCode.METHOD_NOT_ALLOWED
        elif exc.status_code == 401:
            code = ErrorCode.UNAUTHORIZED
        elif exc.status_code < 500:
            code = ErrorCode.VALIDATION_ERROR
        else:
            code = ErrorCode.INTERNAL_ERROR

        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                request,
                code,
                str(exc.detail),
            ),
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled error requestId=%s",
            getattr(request.state, "request_id", None),
        )
        return JSONResponse(
            status_code=500,
            content=error_payload(
                request,
                ErrorCode.INTERNAL_ERROR,
                "服务器内部错误",
            ),
        )

    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(home.router, prefix=prefix)
    app.include_router(registrations.router, prefix=prefix)
    app.include_router(steps.router, prefix=prefix)
    app.include_router(coupons.router, prefix=prefix)
    app.include_router(me.router, prefix=prefix)
    app.include_router(challenges.router, prefix=prefix)
    app.include_router(
        admin_router,
        prefix=f"{prefix}/admin",
    )
    app.include_router(health.router)

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads",
        StaticFiles(directory=str(upload_dir)),
        name="uploads",
    )

    admin_dist = (
        Path(__file__).resolve().parents[2]
        / "LabourRunAdmin"
        / "dist"
    )
    if admin_dist.is_dir():

        @app.get("/admin", include_in_schema=False)
        def admin_redirect():
            return RedirectResponse(url="/admin/")

        @app.get("/admin/", include_in_schema=False)
        def admin_index():
            return FileResponse(admin_dist / "index.html")

        @app.get("/admin/{path:path}", include_in_schema=False)
        def admin_spa(path: str):
            candidate = (admin_dist / path).resolve()
            if (
                candidate.is_file()
                and admin_dist in candidate.parents
            ):
                return FileResponse(candidate)
            return FileResponse(admin_dist / "index.html")

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "name": "LabourRun API",
            "version": "1.0.0",
            "docs": "/docs",
            "admin": "/admin",
        }

    return app
