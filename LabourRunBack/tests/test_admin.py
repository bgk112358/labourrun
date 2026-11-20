from __future__ import annotations

import pytest

from app.admin.service import create_admin
from app.errors import AppError, ErrorCode


def test_admin_login_me_logout(client, admin_headers):
    me = client.get("/api/v1/admin/auth/me", headers=admin_headers)
    assert me.status_code == 200, me.text
    assert me.json()["data"]["username"] == "admin"
    assert me.json()["data"]["role"] == "super_admin"

    logout = client.post(
        "/api/v1/admin/auth/logout",
        headers=admin_headers,
    )
    assert logout.status_code == 200, logout.text
    assert logout.json()["code"] == 0


def test_admin_login_wrong_password(client, settings):
    create_admin(
        settings,
        "wrongpass",
        "AdminPass1234",
        "测试管理员",
        "super_admin",
    )
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "wrongpass", "password": "bad-password"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == 1104


def test_admin_token_isolated_from_user_token(client, login, admin_headers):
    user_headers = login("mock:token-isolation")

    admin_with_user = client.get(
        "/api/v1/admin/dashboard",
        headers=user_headers,
    )
    assert admin_with_user.status_code == 401
    assert admin_with_user.json()["code"] == 1101

    user_with_admin = client.get(
        "/api/v1/home",
        headers=admin_headers,
    )
    assert user_with_admin.status_code == 401
    assert user_with_admin.json()["code"] in {1001, 1002}


def test_activity_update_and_audit(client, admin_headers):
    before = client.get("/api/v1/admin/activity", headers=admin_headers)
    assert before.status_code == 200, before.text
    activity = before.json()["data"]

    payload = {
        "name": activity["name"],
        "noticeText": "延期：10月27日-12月31日",
        "rules": activity["rules"],
        "startDate": activity["startDate"],
        "endDate": activity["endDate"],
        "status": activity["status"],
    }
    updated = client.put(
        "/api/v1/admin/activity",
        headers=admin_headers,
        json=payload,
    )
    assert updated.status_code == 200, updated.text
    data = updated.json()["data"]
    assert data["noticeText"] == "延期：10月27日-12月31日"
    assert data["updatedBy"] == "admin"

    logs = client.get(
        "/api/v1/admin/audit-logs?resourceType=activity",
        headers=admin_headers,
    )
    assert logs.status_code == 200, logs.text
    items = logs.json()["data"]["list"]
    assert items
    log_id = items[0]["id"]

    detail = client.get(
        f"/api/v1/admin/audit-logs/{log_id}",
        headers=admin_headers,
    )
    assert detail.status_code == 200, detail.text
    detail_data = detail.json()["data"]
    assert detail_data["action"] == "update_activity"
    assert detail_data["before"]["noticeText"] != detail_data["after"]["noticeText"]


def test_challenge_update_and_deposit_conversion(client, admin_headers):
    before = client.get("/api/v1/admin/challenge", headers=admin_headers)
    assert before.status_code == 200, before.text
    challenge = before.json()["data"]

    payload = {
        "title": challenge["title"],
        "startDate": challenge["startDate"],
        "endDate": challenge["endDate"],
        "targetSteps": 15000,
        "depositCoupons": "1.20",
        "participantCount": challenge["participantCount"],
        "rules": challenge["rules"],
        "status": challenge["status"],
    }
    updated = client.put(
        "/api/v1/admin/challenge",
        headers=admin_headers,
        json=payload,
    )
    assert updated.status_code == 200, updated.text
    data = updated.json()["data"]
    assert data["targetSteps"] == 15000
    assert data["depositCoupons"] == "1.20"
    assert data["updatedBy"] == "admin"


def test_registration_list_detail_export_permissions(
    client,
    login,
    admin_headers,
    operator_headers,
):
    user_headers = login("mock:registration-admin")
    created = client.post(
        "/api/v1/registrations",
        headers=user_headers,
        json={
            "realName": "张三",
            "phone": "13800138000",
            "company": "某某单位",
        },
    )
    assert created.status_code == 200, created.text
    registration_id = created.json()["data"]["id"]

    listing = client.get(
        "/api/v1/admin/registrations?page=1&pageSize=20",
        headers=admin_headers,
    )
    assert listing.status_code == 200, listing.text
    data = listing.json()["data"]
    assert data["total"] == 1
    item = data["list"][0]
    assert item["phoneMasked"] == "138****8000"
    assert "phone" not in item

    detail = client.get(
        f"/api/v1/admin/registrations/{registration_id}",
        headers=admin_headers,
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["phone"] == "13800138000"

    operator_detail = client.get(
        f"/api/v1/admin/registrations/{registration_id}",
        headers=operator_headers,
    )
    assert operator_detail.status_code == 200, operator_detail.text
    assert operator_detail.json()["data"]["phone"] is None

    export = client.get(
        "/api/v1/admin/registrations/export",
        headers=admin_headers,
    )
    assert export.status_code == 200, export.text
    assert export.headers["content-type"].startswith("text/csv")
    assert "13800138000" in export.text
    assert "张三" in export.text

    operator_export = client.get(
        "/api/v1/admin/registrations/export",
        headers=operator_headers,
    )
    assert operator_export.status_code == 403
    assert operator_export.json()["code"] == 1103


def test_dashboard(client, admin_headers, login):
    user_headers = login("mock:dashboard")
    client.post(
        "/api/v1/registrations",
        headers=user_headers,
        json={
            "realName": "李四",
            "phone": "13900139000",
            "company": "单位 B",
        },
    )

    response = client.get(
        "/api/v1/admin/dashboard",
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["registrationCount"] == 1
    assert data["activity"]["id"] == "act_default"
    assert data["challenge"]["id"] == "ch_default"
    assert data["recentAuditLogs"]


def test_admin_create_password_policy(settings):
    with pytest.raises(AppError) as exc_info:
        create_admin(
            settings,
            "shortpass",
            "short",
            "测试",
            "operator",
        )
    assert exc_info.value.code == ErrorCode.ADMIN_PASSWORD_POLICY


def test_admin_login_rate_limit(client):
    username = "ratelimit_user"
    for _ in range(5):
        response = client.post(
            "/api/v1/admin/auth/login",
            json={"username": username, "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/v1/admin/auth/login",
        json={"username": username, "password": "wrong-password"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == 1110
