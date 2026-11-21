from __future__ import annotations

from ..config import Settings
from ..db import get_conn
from ..errors import AppError, ErrorCode
from .common import get_current_activity, row_to_activity, row_to_registration
from .reward_service import list_home_rewards


def get_home(settings: Settings, user_id: str) -> dict:
    with get_conn(settings) as conn:
        activity = get_current_activity(conn)
        if activity is None:
            raise AppError(ErrorCode.ACTIVITY_NOT_FOUND, 404, "活动不存在")

        registration = conn.execute(
            """
            SELECT *
            FROM registrations
            WHERE activity_id = ? AND user_id = ?
            """,
            (activity["id"], user_id),
        ).fetchone()
        rewards = list_home_rewards(
            conn,
            activity,
            user_id,
            registration,
        )

    return {
        "activity": row_to_activity(activity),
        "registration": row_to_registration(registration) if registration else None,
        "rewards": rewards,
    }
