from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import DailyActivity


def get_daily_activity_rows_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Sequence[date],
) -> list[DailyActivity]:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return []

    stmt = (
        select(DailyActivity)
        .where(
            DailyActivity.user_id == user_id,
            DailyActivity.local_date.in_(unique_dates),
        )
        .order_by(DailyActivity.local_date.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_daily_activity_range(
    db: Session,
    *,
    user_id: UUID,
    from_date: date,
    to_date: date,
) -> list[DailyActivity]:
    stmt = (
        select(DailyActivity)
        .where(
            DailyActivity.user_id == user_id,
            DailyActivity.local_date >= from_date,
            DailyActivity.local_date <= to_date,
        )
        .order_by(DailyActivity.local_date.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_daily_activity_by_date(
    db: Session,
    *,
    user_id: UUID,
    target_date: date,
) -> DailyActivity | None:
    stmt = select(DailyActivity).where(
        DailyActivity.user_id == user_id,
        DailyActivity.local_date == target_date,
    )
    return db.execute(stmt).scalar_one_or_none()
