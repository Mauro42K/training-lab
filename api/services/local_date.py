from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def normalize_timezone_name(timezone_name: str | None) -> str | None:
    candidate = (timezone_name or "").strip()
    if candidate == "":
        return None
    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return None
    return candidate


def resolve_timezone_name(
    *,
    user_timezone: str | None,
    fallback_timezone: str,
) -> str:
    normalized = normalize_timezone_name(user_timezone)
    if normalized is not None:
        return normalized
    fallback = normalize_timezone_name(fallback_timezone)
    if fallback is None:
        raise RuntimeError(f"Invalid fallback timezone configured: {fallback_timezone}")
    return fallback


def resolve_authoritative_timezone_name(
    *,
    request_timezone: str | None,
    stored_timezone: str | None,
    fallback_timezone: str,
) -> str:
    request_resolved = normalize_timezone_name(request_timezone)
    if request_resolved is not None:
        return request_resolved

    stored_resolved = normalize_timezone_name(stored_timezone)
    if stored_resolved is not None:
        return stored_resolved

    return resolve_timezone_name(
        user_timezone=None,
        fallback_timezone=fallback_timezone,
    )


def resolve_local_datetime(
    *,
    instant: datetime,
    user_timezone: str | None,
    fallback_timezone: str,
) -> datetime:
    tz_name = resolve_timezone_name(
        user_timezone=user_timezone,
        fallback_timezone=fallback_timezone,
    )
    tz = ZoneInfo(tz_name)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)
    return instant.astimezone(tz)


def resolve_local_date(
    *,
    instant: datetime,
    user_timezone: str | None,
    fallback_timezone: str,
) -> date:
    return resolve_local_datetime(
        instant=instant,
        user_timezone=user_timezone,
        fallback_timezone=fallback_timezone,
    ).date()


def resolve_sleep_session_local_date(
    *,
    start_at: datetime,
    end_at: datetime,
    user_timezone: str | None,
    fallback_timezone: str,
) -> date:
    _ = start_at
    return resolve_local_date(
        instant=end_at,
        user_timezone=user_timezone,
        fallback_timezone=fallback_timezone,
    )


def resolve_measurement_local_date(
    *,
    measured_at: datetime,
    user_timezone: str | None,
    fallback_timezone: str,
) -> date:
    return resolve_local_date(
        instant=measured_at,
        user_timezone=user_timezone,
        fallback_timezone=fallback_timezone,
    )


def resolve_daily_activity_local_date(
    *,
    bucket_start: datetime,
    user_timezone: str | None,
    fallback_timezone: str,
) -> date:
    return resolve_local_date(
        instant=bucket_start,
        user_timezone=user_timezone,
        fallback_timezone=fallback_timezone,
    )
