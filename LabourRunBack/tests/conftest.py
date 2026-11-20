from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.admin.service import create_admin
from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        host="127.0.0.1",
        port=3000,
        db_path=str(tmp_path / "test.sqlite"),
        jwt_secret="test-secret-please-use-32-bytes-ok",
        jwt_ttl_seconds=3600,
        wx_appid="wx_test",
        wx_secret="",
        wx_mock=True,
        log_level="error",
        upload_dir=str(tmp_path / "uploads"),
        public_base_url="http://testserver",
        activity_image_width=750,
        activity_image_height=400,
        activity_image_quality=82,
    )


@pytest.fixture
def client(settings: Settings):
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def login(client: TestClient):
    def _login(code: str = "mock:alice") -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login",
            json={"code": code},
        )
        assert response.status_code == 200, response.text
        token = response.json()["data"]["token"]
        return {"Authorization": f"Bearer {token}"}

    return _login


@pytest.fixture
def admin_headers(client: TestClient, settings: Settings):
    create_admin(
        settings,
        "admin",
        "AdminPass1234",
        "超级管理员",
        "super_admin",
    )
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "AdminPass1234"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def operator_headers(client: TestClient, settings: Settings):
    create_admin(
        settings,
        "operator",
        "OperatorPass1234",
        "运营管理员",
        "operator",
    )
    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "operator",
            "password": "OperatorPass1234",
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
