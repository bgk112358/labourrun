from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    db_path: str
    jwt_secret: str
    jwt_ttl_seconds: int
    wx_appid: str
    wx_secret: str
    wx_mock: bool
    log_level: str
    admin_jwt_secret: str = "dev-admin-secret-change-me-please-32"
    admin_jwt_ttl_seconds: int = 28800
    admin_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    upload_dir: str = "./uploads"
    public_base_url: str = "http://192.168.100.20:3000"
    activity_image_width: int = 750
    activity_image_height: int = 400
    activity_image_quality: int = 82
    activity_image_max_upload_bytes: int = 10 * 1024 * 1024
    activity_image_target_bytes: int = 200 * 1024


def load_settings() -> Settings:
    return Settings(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "3000")),
        db_path=os.getenv("DB_PATH", "./data/labourrun.sqlite"),
        jwt_secret=os.getenv(
            "JWT_SECRET",
            "dev-secret-change-me-please-use-32-bytes",
        ),
        jwt_ttl_seconds=int(os.getenv("JWT_TTL_SECONDS", "604800")),
        wx_appid=os.getenv("WX_APPID", "wx553877a9e7439113"),
        wx_secret=os.getenv("WX_SECRET", ""),
        wx_mock=_env_bool("WX_MOCK", True),
        log_level=os.getenv("LOG_LEVEL", "info"),
        admin_jwt_secret=os.getenv(
            "ADMIN_JWT_SECRET",
            "dev-admin-secret-change-me-please-32",
        ),
        admin_jwt_ttl_seconds=int(
            os.getenv("ADMIN_JWT_TTL_SECONDS", "28800")
        ),
        admin_origins=os.getenv(
            "ADMIN_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ),
        upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
        public_base_url=os.getenv(
            "PUBLIC_BASE_URL",
            "http://192.168.100.20:3000",
        ),
        activity_image_width=int(
            os.getenv("ACTIVITY_IMAGE_WIDTH", "750")
        ),
        activity_image_height=int(
            os.getenv("ACTIVITY_IMAGE_HEIGHT", "400")
        ),
        activity_image_quality=int(
            os.getenv("ACTIVITY_IMAGE_QUALITY", "82")
        ),
    )
