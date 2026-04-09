from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

PERIOD_LABELS = {
    "mes_atual": "mês atual",
    "7d": "últimos 7 dias",
    "30d": "últimos 30 dias",
}


def now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_local_time(value: datetime | None, app_timezone: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    return ensure_utc(value).astimezone(app_timezone)


def format_datetime(value: datetime | None, app_timezone: ZoneInfo) -> str:
    local_value = to_local_time(value, app_timezone)
    if local_value is None:
        return "-"
    return local_value.strftime("%d/%m/%Y %H:%M:%S")


def format_duration(total_seconds: int) -> str:
    if total_seconds <= 0:
        return "0s"

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}min")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def resolve_period_range(
    period_key: str,
    app_timezone: ZoneInfo,
) -> tuple[datetime, datetime, str]:
    now_local = datetime.now(app_timezone)

    if period_key == "mes_atual":
        started_from_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period_key == "7d":
        started_from_local = now_local - timedelta(days=7)
    elif period_key == "30d":
        started_from_local = now_local - timedelta(days=30)
    else:
        raise ValueError("Invalid period. Use one of: mes_atual, 7d, 30d.")

    started_from_utc = started_from_local.astimezone(timezone.utc).replace(tzinfo=None)
    started_until_utc = now_local.astimezone(timezone.utc).replace(tzinfo=None)
    return started_from_utc, started_until_utc, PERIOD_LABELS[period_key]
