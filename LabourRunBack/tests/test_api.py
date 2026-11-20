from __future__ import annotations


def test_login_and_me(client, login):
    headers = login()
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["requestId"]
    assert body["data"]["id"].startswith("usr_")
    assert body["data"]["nickname"] is None
    assert body["data"]["avatarUrl"] is None
    assert body["data"]["phone"] is None


def test_home_defaults(client, login):
    headers = login()
    response = client.get("/api/v1/home", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["activity"]["id"] == "act_default"
    assert data["activity"]["noticeText"] == "延期：10月27日-12月27日"
    assert len(data["activity"]["rules"]) == 4
    assert data["activity"]["rules"][0]["no"] == "01"
    assert data["registration"] is None


def test_registration_create_update_cancel_reregister(client, login):
    headers = login()

    response = client.post(
        "/api/v1/registrations",
        headers=headers,
        json={
            "realName": "张三",
            "phone": "13800138000",
            "company": "某某单位",
        },
    )
    assert response.status_code == 200, response.text
    registration = response.json()["data"]
    registration_id = registration["id"]
    assert registration["status"] == "registered"
    assert registration["realName"] == "张三"

    duplicate = client.post(
        "/api/v1/registrations",
        headers=headers,
        json={
            "realName": "张三",
            "phone": "13800138000",
            "company": "某某单位",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 2001

    updated = client.patch(
        f"/api/v1/registrations/{registration_id}",
        headers=headers,
        json={"company": "新单位"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["company"] == "新单位"

    cancelled = client.post(
        f"/api/v1/registrations/{registration_id}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["data"]["status"] == "cancelled"
    assert cancelled.json()["data"]["cancelledAt"] is not None

    cancelled_again = client.post(
        f"/api/v1/registrations/{registration_id}/cancel",
        headers=headers,
    )
    assert cancelled_again.status_code == 200
    assert cancelled_again.json()["data"]["status"] == "cancelled"

    reregistered = client.post(
        "/api/v1/registrations",
        headers=headers,
        json={
            "realName": "张三",
            "phone": "13800138000",
            "company": "新单位",
        },
    )
    assert reregistered.status_code == 200, reregistered.text
    assert reregistered.json()["data"]["id"] == registration_id
    assert reregistered.json()["data"]["status"] == "registered"


def test_registration_phone_conflict(client, login):
    headers_a = login("mock:alice")
    headers_b = login("mock:bob")

    first = client.post(
        "/api/v1/registrations",
        headers=headers_a,
        json={
            "realName": "张三",
            "phone": "13800138000",
            "company": "单位 A",
        },
    )
    assert first.status_code == 200, first.text

    conflict = client.post(
        "/api/v1/registrations",
        headers=headers_b,
        json={
            "realName": "李四",
            "phone": "13800138000",
            "company": "单位 B",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == 2001


def test_registration_validation(client, login):
    headers = login()
    response = client.post(
        "/api/v1/registrations",
        headers=headers,
        json={
            "realName": "张三",
            "phone": "123",
            "company": "某某单位",
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == 4000
    assert body["data"]["errors"]


def test_steps_exchange_and_idempotency(client, login):
    headers = login()

    synced = client.post(
        "/api/v1/steps/sync",
        headers=headers,
        json={"mockSteps": 6638},
    )
    assert synced.status_code == 200, synced.text
    summary = synced.json()["data"]["stepSummary"]
    assert summary["todaySteps"] == 6638
    assert summary["convertibleSteps"] == 6638
    assert summary["convertibleCoupons"] == "0.66"

    exchanged = client.post(
        "/api/v1/steps/exchange",
        headers=headers,
        json={"requestId": "req-00000001"},
    )
    assert exchanged.status_code == 200, exchanged.text
    exchange_data = exchanged.json()["data"]
    exchange_id = exchange_data["exchange"]["id"]
    assert exchange_data["exchange"]["steps"] == 6638
    assert exchange_data["exchange"]["couponAmount"] == "0.66"
    assert exchange_data["couponAccount"]["balance"] == "0.66"
    assert exchange_data["stepSummary"]["convertibleSteps"] == 0

    repeated = client.post(
        "/api/v1/steps/exchange",
        headers=headers,
        json={"requestId": "req-00000001"},
    )
    assert repeated.status_code == 200, repeated.text
    repeated_data = repeated.json()["data"]
    assert repeated_data["exchange"]["id"] == exchange_id
    assert repeated_data["couponAccount"]["balance"] == "0.66"

    steps = client.get("/api/v1/steps", headers=headers)
    assert steps.status_code == 200
    step_data = steps.json()["data"]
    assert step_data["stepSummary"]["exchangedSteps"] == 6638
    assert step_data["stepSummary"]["convertibleSteps"] == 0
    assert step_data["couponAccount"]["balance"] == "0.66"

    no_more = client.post(
        "/api/v1/steps/exchange",
        headers=headers,
        json={"requestId": "req-00000002"},
    )
    assert no_more.status_code == 422
    assert no_more.json()["code"] == 3003


def test_exchange_daily_cap(client, login):
    headers = login()
    client.post(
        "/api/v1/steps/sync",
        headers=headers,
        json={"mockSteps": 20000},
    )

    steps = client.get("/api/v1/steps", headers=headers)
    summary = steps.json()["data"]["stepSummary"]
    assert summary["todaySteps"] == 20000
    assert summary["convertibleSteps"] == 12000
    assert summary["convertibleCoupons"] == "1.20"

    exchanged = client.post(
        "/api/v1/steps/exchange",
        headers=headers,
        json={"requestId": "req-cap-0001"},
    )
    assert exchanged.status_code == 200, exchanged.text
    data = exchanged.json()["data"]
    assert data["exchange"]["steps"] == 12000
    assert data["exchange"]["couponAmount"] == "1.20"
    assert data["stepSummary"]["convertibleSteps"] == 0

    cap_error = client.post(
        "/api/v1/steps/exchange",
        headers=headers,
        json={"requestId": "req-cap-0002"},
    )
    assert cap_error.status_code == 422
    assert cap_error.json()["code"] == 3004


def test_ledger(client, login):
    headers = login()
    client.post(
        "/api/v1/steps/sync",
        headers=headers,
        json={"mockSteps": 6638},
    )
    client.post(
        "/api/v1/steps/exchange",
        headers=headers,
        json={"requestId": "req-ledger-01"},
    )

    response = client.get(
        "/api/v1/coupons/ledger?page=1&pageSize=20",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["pageSize"] == 20
    item = data["list"][0]
    assert item["type"] == "exchange"
    assert item["amount"] == "0.66"
    assert item["balanceAfter"] == "0.66"
    assert item["refType"] == "exchange"
    assert item["refId"]


def test_me_update_nickname(client, login):
    headers = login()
    response = client.patch(
        "/api/v1/me",
        headers=headers,
        json={"nickname": " 张三 "},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["nickname"] == "张三"

    me = client.get("/api/v1/me", headers=headers)
    assert me.json()["data"]["nickname"] == "张三"


def test_challenge(client):
    response = client.get("/api/v1/challenges/current")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["targetSteps"] == 12000
    assert data["depositCoupons"] == "0.00"
    assert data["participantCount"] == 309
    assert len(data["rules"]) > 0


def test_auth_required(client):
    response = client.get("/api/v1/home")
    assert response.status_code == 401
    assert response.json()["code"] == 1001


def test_health(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sync_payload_validation(client, login):
    headers = login()
    response = client.post(
        "/api/v1/steps/sync",
        headers=headers,
        json={},
    )
    assert response.status_code == 400
    assert response.json()["code"] == 4000
