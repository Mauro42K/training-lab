from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import BodyMeasurement


def get_body_measurements_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Sequence[date],
) -> list[BodyMeasurement]:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return []

    stmt = (
        select(BodyMeasurement)
        .where(
            BodyMeasurement.user_id == user_id,
            BodyMeasurement.local_date.in_(unique_dates),
        )
        .order_by(
            BodyMeasurement.local_date.asc(),
            BodyMeasurement.measured_at.asc(),
        )
    )
    return list(db.execute(stmt).scalars().all())


def get_body_measurements_range(
    db: Session,
    *,
    user_id: UUID,
    from_date: date,
    to_date: date,
) -> list[BodyMeasurement]:
    stmt = (
        select(BodyMeasurement)
        .where(
            BodyMeasurement.user_id == user_id,
            BodyMeasurement.local_date >= from_date,
            BodyMeasurement.local_date <= to_date,
        )
        .order_by(
            BodyMeasurement.local_date.asc(),
            BodyMeasurement.measured_at.asc(),
        )
    )
    return list(db.execute(stmt).scalars().all())
