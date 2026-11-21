from __future__ import annotations

import re
from io import BytesIO
from urllib.parse import urlparse

import pytest


CODE_RE = re.compile(r"^LR-[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{8}$")


def _register(client, headers, phone="13800138001"):
    response = client.post(
        "/api/v1/registrations",
        headers=headers,
        json={
            "realName": "奖品测试",
            "phone": phone,
            "company": "测试单位",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _earn_one_coupon(client, headers):
    synced = client.post(
        "/api/v1/steps/sync",
        headers=headers,
        json={"mockSteps": 10000},
    )
    assert synced.status_code == 200, synced.text
    exchanged = client.post(
        "/api/v1/steps/exchange",
        headers=headers,
        json={"requestId": "reward-earn-0001"},
    )
    assert exchanged.status_code == 200, exchanged.text
    return exchanged.json()["data"]


def test_home_rewards_require_registration(client, login):
    headers = login()
    home = client.get("/api/v1/home", headers=headers)
    assert home.status_code == 200, home.text
    rewards = home.json()["data"]["rewards"]
    assert [item["name"] for item in rewards] == [
        "运动水杯",
        "运动毛巾",
        "运动背包",
    ]
    assert [item["couponCost"] for item in rewards] == [
        "0.50",
        "1.00",
        "2.00",
    ]
    assert all(item["redeemed"] is False for item in rewards)
    assert all(item["canRedeem"] is False for item in rewards)
    assert all(
        item["disabledReason"] == "请先报名" for item in rewards
    )

    _earn_one_coupon(client, headers)
    response = client.post(
        "/api/v1/rewards/rwd_water_bottle/redeem",
        headers=headers,
        json={"requestId": "reward-no-reg-0001"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == 3011
    assert response.json()["message"] == "请先报名"


def test_reward_redeem_flow_and_idempotency(client, login):
    headers = login()
    _register(client, headers)
    _earn_one_coupon(client, headers)

    home = client.get("/api/v1/home", headers=headers)
    rewards = home.json()["data"]["rewards"]
    assert all(item["canRedeem"] is True for item in rewards)

    redeemed = client.post(
        "/api/v1/rewards/rwd_water_bottle/redeem",
        headers=headers,
        json={"requestId": "reward-flow-0001"},
    )
    assert redeemed.status_code == 200, redeemed.text
    data = redeemed.json()["data"]
    code = data["redemption"]["code"]
    assert CODE_RE.match(code)
    assert data["redemption"]["rewardName"] == "运动水杯"
    assert data["redemption"]["couponAmount"] == "0.50"
    assert data["couponAccount"]["balance"] == "0.50"

    repeated = client.post(
        "/api/v1/rewards/rwd_water_bottle/redeem",
        headers=headers,
        json={"requestId": "reward-flow-0001"},
    )
    assert repeated.status_code == 200, repeated.text
    repeated_data = repeated.json()["data"]
    assert repeated_data["redemption"]["code"] == code
    assert repeated_data["couponAccount"]["balance"] == "0.50"

    home = client.get("/api/v1/home", headers=headers)
    rewards = {
        item["id"]: item for item in home.json()["data"]["rewards"]
    }
    assert rewards["rwd_water_bottle"]["redeemed"] is True
    assert rewards["rwd_water_bottle"]["redemptionCode"] == code
    assert rewards["rwd_towel"]["canRedeem"] is True

    duplicate = client.post(
        "/api/v1/rewards/rwd_water_bottle/redeem",
        headers=headers,
        json={"requestId": "reward-flow-0002"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 3010

    insufficient = client.post(
        "/api/v1/rewards/rwd_backpack/redeem",
        headers=headers,
        json={"requestId": "reward-flow-0003"},
    )
    assert insufficient.status_code == 422
    assert insufficient.json()["code"] == 3009
    assert insufficient.json()["message"] == "兑换券不足"

    ledger = client.get(
        "/api/v1/coupons/ledger?page=1&pageSize=20",
        headers=headers,
    )
    assert ledger.status_code == 200, ledger.text
    items = ledger.json()["data"]["list"]
    reward_items = [item for item in items if item["type"] == "reward"]
    assert len(reward_items) == 1
    assert reward_items[0]["amount"] == "-0.50"
    assert reward_items[0]["balanceAfter"] == "0.50"


def test_admin_reward_lookup(client, login, admin_headers, operator_headers):
    user_headers = login("mock:reward-admin-lookup")
    _register(client, user_headers, phone="13800138002")
    _earn_one_coupon(client, user_headers)
    redeemed = client.post(
        "/api/v1/rewards/rwd_water_bottle/redeem",
        headers=user_headers,
        json={"requestId": "reward-admin-0001"},
    )
    assert redeemed.status_code == 200, redeemed.text
    code = redeemed.json()["data"]["redemption"]["code"]

    lookup = client.get(
        f"/api/v1/admin/redemptions/{code}",
        headers=admin_headers,
    )
    assert lookup.status_code == 200, lookup.text
    data = lookup.json()["data"]
    assert data["redemption"]["code"] == code
    assert data["redemption"]["rewardName"] == "运动水杯"
    assert data["redemption"]["couponCost"] == "0.50"
    assert data["redeemer"]["realName"] == "奖品测试"
    assert data["redeemer"]["phone"] == "13800138002"
    assert data["registration"]["status"] == "registered"
    assert data["couponAccount"]["balance"] == "0.50"
    assert data["stepSummary"]["todaySteps"] == 10000
    assert data["stepSummary"]["todayExchangedSteps"] == 10000
    assert data["stepSummary"]["todayConvertibleSteps"] == 0
    assert len(data["redemptions"]) == 1
    assert data["redemptions"][0]["code"] == code
    assert len(data["ledger"]) == 2

    normalized = client.get(
        "/api/v1/admin/redemptions/"
        + code.replace("-", "").lower(),
        headers=admin_headers,
    )
    assert normalized.status_code == 200, normalized.text

    masked = client.get(
        f"/api/v1/admin/redemptions/{code}",
        headers=operator_headers,
    )
    assert masked.status_code == 200, masked.text
    masked_data = masked.json()["data"]
    assert masked_data["redeemer"]["phone"] is None
    assert "****" in masked_data["redeemer"]["phoneMasked"]
    assert masked_data["registration"]["phone"] is None

    missing = client.get(
        "/api/v1/admin/redemptions/LR-NOTFOUND",
        headers=admin_headers,
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == 1206

    logs = client.get(
        "/api/v1/admin/audit-logs?resourceType=reward_redemption",
        headers=admin_headers,
    )
    assert logs.status_code == 200, logs.text
    assert logs.json()["data"]["total"] >= 1


def test_admin_reward_update_and_image(
    client,
    login,
    admin_headers,
):
    pytest.importorskip("PIL")
    from PIL import Image

    listing = client.get(
        "/api/v1/admin/rewards",
        headers=admin_headers,
    )
    assert listing.status_code == 200, listing.text
    items = listing.json()["data"]["list"]
    assert len(items) == 3

    reward_id = items[0]["id"]
    updated = client.patch(
        f"/api/v1/admin/rewards/{reward_id}",
        headers=admin_headers,
        json={
            "name": "定制水杯",
            "couponCost": "0.60",
            "imageUrl": None,
            "sortOrder": 1,
            "active": True,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["name"] == "定制水杯"
    assert updated.json()["data"]["couponCost"] == "0.60"

    user_headers = login("mock:reward-home")
    home = client.get("/api/v1/home", headers=user_headers)
    rewards = home.json()["data"]["rewards"]
    assert rewards[0]["name"] == "定制水杯"
    assert rewards[0]["couponCost"] == "0.60"

    image_bytes = BytesIO()
    Image.new("RGB", (800, 600), (233, 59, 51)).save(
        image_bytes,
        format="PNG",
    )
    upload_headers = dict(admin_headers)
    upload_headers["Content-Type"] = "image/png"
    uploaded = client.post(
        "/api/v1/admin/rewards/image",
        headers=upload_headers,
        content=image_bytes.getvalue(),
    )
    assert uploaded.status_code == 200, uploaded.text
    image = uploaded.json()["data"]
    assert image["width"] == 400
    assert image["height"] == 400
    assert image["imageUrl"].startswith(
        "http://testserver/uploads/reward/"
    )
    served = client.get(urlparse(image["imageUrl"]).path)
    assert served.status_code == 200
    assert served.content.startswith(b"\xff\xd8\xff")

    saved = client.patch(
        f"/api/v1/admin/rewards/{reward_id}",
        headers=admin_headers,
        json={
            "name": "定制水杯",
            "couponCost": "0.60",
            "imageUrl": image["imageUrl"],
            "sortOrder": 1,
            "active": True,
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["data"]["imageUrl"] == image["imageUrl"]
