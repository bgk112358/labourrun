from __future__ import annotations

from datetime import datetime, timedelta, timezone

SHANGHAI_TZ = timezone(timedelta(hours=8))


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def today_shanghai() -> str:
    return datetime.now(SHANGHAI_TZ).date().isoformat()


def start_of_today_shanghai_utc_iso() -> str:
    now = datetime.now(SHANGHAI_TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        start.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def timestamp_to_shanghai_date(timestamp: int | float) -> str:
    return datetime.fromtimestamp(float(timestamp), tz=SHANGHAI_TZ).date().isoformat()


def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(int(cents))
    return f"{sign}{cents // 100}.{cents % 100:02d}"
