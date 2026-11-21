from __future__ import annotations

import json
import sqlite3

from .timeutil import utc_now_iso


ACTIVITY_ID = "act_default"
CHALLENGE_ID = "ch_default"
REWARD_IDS = (
    "rwd_water_bottle",
    "rwd_towel",
    "rwd_backpack",
)


def seed(conn: sqlite3.Connection) -> None:
    now = utc_now_iso()

    activity_rules = [
        {"no": "01", "text": "一、本次活动为线上步行挑战赛，参赛者需每日完成指定步数。"},
        {"no": "02", "text": "二、每日步数于零点自动清零，请及时兑换您的步数奖励。"},
        {"no": "03", "text": "三、参赛者不得使用任何外挂或作弊手段，一经发现将取消资格。"},
        {"no": "04", "text": "四、活动最终解释权归主办方所有，如有疑问请联系客服。"},
    ]
    conn.execute(
        """
        INSERT OR IGNORE INTO activities
            (id, name, notice_text, rules_json, start_date, end_date, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ACTIVITY_ID,
            "线上步行挑战赛",
            "延期：10月27日-12月27日",
            json.dumps(activity_rules, ensure_ascii=False),
            "2026-10-27",
            "2026-12-27",
            "ongoing",
            now,
            now,
        ),
    )

    challenge_rules = [
        {"title": "挑战目标", "content": "每日完成 12000 步。"},
        {"title": "挑战保证金", "content": "本期保证金 0.00 兑换券。"},
        {"title": "参与方式", "content": "本期仅展示挑战配置与规则，参赛流程后续开放。"},
        {"title": "奖励说明", "content": "完成情况与奖励以后台配置为准。"},
    ]
    conn.execute(
        """
        INSERT OR IGNORE INTO challenges
            (id, title, start_date, end_date, target_steps, deposit_cents,
             participant_count, rules_json, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            CHALLENGE_ID,
            "步数挑战",
            "2026-11-18",
            None,
            12000,
            0,
            309,
            json.dumps(challenge_rules, ensure_ascii=False),
            "upcoming",
            now,
            now,
        ),
    )

    conn.execute(
        "INSERT OR IGNORE INTO app_config(key, value) VALUES (?, ?)",
        ("daily_cap_steps", "10000"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO app_config(key, value) VALUES (?, ?)",
        ("steps_per_coupon", "10000"),
    )
    # 旧库默认上限为 12000，按新规则迁移到 10000。
    conn.execute(
        """
        UPDATE app_config
        SET value = '10000'
        WHERE key = 'daily_cap_steps' AND value = '12000'
        """
    )

    rewards = [
        (
            REWARD_IDS[0],
            ACTIVITY_ID,
            "运动水杯",
            None,
            50,
            1,
            1,
        ),
        (
            REWARD_IDS[1],
            ACTIVITY_ID,
            "运动毛巾",
            None,
            100,
            2,
            1,
        ),
        (
            REWARD_IDS[2],
            ACTIVITY_ID,
            "运动背包",
            None,
            200,
            3,
            1,
        ),
    ]
    for (
        reward_id,
        activity_id,
        name,
        image_url,
        coupon_cost_cents,
        sort_order,
        active,
    ) in rewards:
        conn.execute(
            """
            INSERT OR IGNORE INTO rewards
                (id, activity_id, name, image_url, coupon_cost_cents,
                 sort_order, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reward_id,
                activity_id,
                name,
                image_url,
                coupon_cost_cents,
                sort_order,
                active,
                now,
                now,
            ),
        )
