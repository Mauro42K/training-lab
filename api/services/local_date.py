from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_local_date(
    *,
    instant: datetime,
    user_timezone: str | None,
    fallback_timezone: str,
) -> date:
    tz_name = (user_timezone or "").strip() or fallback_timezone
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo(fallback_timezone)

    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)
    return instant.astimezone(tz).date()
