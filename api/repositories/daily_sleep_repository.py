from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import DailySleepSummary


def get_daily_sleep_summary_rows_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Sequence[date],
) -> list[DailySleepSummary]:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return []

    stmt = (
        select(DailySleepSummary)
        .where(
            DailySleepSummary.user_id == user_id,
            DailySleepSummary.local_date.in_(unique_dates),
        )
        .order_by(DailySleepSummary.local_date.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_daily_sleep_summary_range(
    db: Session,
    *,
    user_id: UUID,
    from_date: date,
    to_date: date,
) -> list[DailySleepSummary]:
    stmt = (
        select(DailySleepSummary)
        .where(
            DailySleepSummary.user_id == user_id,
            DailySleepSummary.local_date >= from_date,
            DailySleepSummary.local_date <= to_date,
        )
        .order_by(DailySleepSummary.local_date.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_daily_sleep_summary_by_date(
    db: Session,
    *,
    user_id: UUID,
    target_date: date,
) -> DailySleepSummary | None:
    stmt = select(DailySleepSummary).where(
        DailySleepSummary.user_id == user_id,
        DailySleepSummary.local_date == target_date,
    )
    return db.execute(stmt).scalar_one_or_none()
