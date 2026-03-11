from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.db.models import DailyLoad, DailyRecovery, RecoverySignal, WorkoutLoad


@dataclass(frozen=True)
class DailyLoadContext:
    local_date: date
    load_present: bool
    has_estimated_inputs: bool


def get_daily_recovery_range(
    db: Session,
    *,
    user_id: UUID,
    from_date: date,
    to_date: date,
) -> list[DailyRecovery]:
    stmt = (
        select(DailyRecovery)
        .where(
            DailyRecovery.user_id == user_id,
            DailyRecovery.local_date >= from_date,
            DailyRecovery.local_date <= to_date,
        )
        .order_by(DailyRecovery.local_date.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_daily_recovery_by_date(
    db: Session,
    *,
    user_id: UUID,
    target_date: date,
) -> DailyRecovery | None:
    stmt = select(DailyRecovery).where(
        DailyRecovery.user_id == user_id,
        DailyRecovery.local_date == target_date,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_recovery_signals_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Sequence[date],
) -> list[RecoverySignal]:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return []

    stmt = (
        select(RecoverySignal)
        .where(
            RecoverySignal.user_id == user_id,
            RecoverySignal.local_date.in_(unique_dates),
        )
        .order_by(
            RecoverySignal.local_date.asc(),
            RecoverySignal.measured_at.asc(),
        )
    )
    return list(db.execute(stmt).scalars().all())


def get_daily_load_context_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Sequence[date],
    trimp_model_version: int,
) -> dict[date, DailyLoadContext]:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return {}

    load_stmt = select(DailyLoad.date).where(
        DailyLoad.user_id == user_id,
        DailyLoad.date.in_(unique_dates),
        DailyLoad.sport_filter == "all",
        DailyLoad.trimp_model_version == trimp_model_version,
        DailyLoad.sessions_count > 0,
    )
    estimated_stmt = (
        select(
            WorkoutLoad.local_date,
            func.bool_or(WorkoutLoad.trimp_source == "estimated").label("has_estimated_inputs"),
        )
        .where(
            WorkoutLoad.user_id == user_id,
            WorkoutLoad.local_date.in_(unique_dates),
            WorkoutLoad.trimp_model_version == trimp_model_version,
        )
        .group_by(WorkoutLoad.local_date)
    )

    load_dates = set(db.execute(load_stmt).scalars().all())
    estimated_by_date = {
        row.local_date: bool(row.has_estimated_inputs)
        for row in db.execute(estimated_stmt).all()
    }
    return {
        current_date: DailyLoadContext(
            local_date=current_date,
            load_present=current_date in load_dates,
            has_estimated_inputs=estimated_by_date.get(current_date, False),
        )
        for current_date in unique_dates
    }
