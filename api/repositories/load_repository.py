from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models import DailyLoad, Workout, WorkoutLoad
from api.repositories.workout_identity import WORKOUT_INGEST_IDENTITY_FIELD

SUPPORTED_LOAD_SPORTS = ("run", "bike", "strength", "walk")


@dataclass(frozen=True)
class WorkoutSnapshot:
    workout_id: int
    healthkit_workout_uuid: UUID
    sport: str
    start: datetime
    duration_sec: int
    avg_hr_bpm: float | None
    is_deleted: bool


@dataclass(frozen=True)
class WorkoutLoadUpsert:
    workout_id: int
    user_id: UUID
    local_date: date
    sport: str
    trimp_value: float
    trimp_source: str
    trimp_model_version: int
    trimp_method: str
    hr_rest_bpm_used: int | None
    hr_max_bpm_used: int | None
    intensity_factor_used: float | None


def get_workout_snapshots_by_uuids(
    db: Session,
    *,
    user_id: UUID,
    workout_uuids: Sequence[UUID],
) -> dict[UUID, WorkoutSnapshot]:
    if not workout_uuids:
        return {}

    ingest_identity_col = getattr(Workout, WORKOUT_INGEST_IDENTITY_FIELD)
    stmt = select(
        Workout.id,
        ingest_identity_col.label("healthkit_workout_uuid"),
        Workout.sport,
        Workout.start,
        Workout.duration_sec,
        Workout.avg_hr_bpm,
        Workout.is_deleted,
    ).where(
        Workout.user_id == user_id,
        ingest_identity_col.in_(list(workout_uuids)),
    )

    rows = db.execute(stmt).all()
    return {
        row.healthkit_workout_uuid: WorkoutSnapshot(
            workout_id=row.id,
            healthkit_workout_uuid=row.healthkit_workout_uuid,
            sport=row.sport,
            start=row.start,
            duration_sec=row.duration_sec,
            avg_hr_bpm=row.avg_hr_bpm,
            is_deleted=row.is_deleted,
        )
        for row in rows
    }


def upsert_workout_load_rows(
    db: Session,
    *,
    rows: Sequence[WorkoutLoadUpsert],
) -> None:
    if not rows:
        return

    values = [
        {
            "workout_id": row.workout_id,
            "user_id": row.user_id,
            "local_date": row.local_date,
            "sport": row.sport,
            "trimp_value": row.trimp_value,
            "trimp_source": row.trimp_source,
            "trimp_model_version": row.trimp_model_version,
            "trimp_method": row.trimp_method,
            "hr_rest_bpm_used": row.hr_rest_bpm_used,
            "hr_max_bpm_used": row.hr_max_bpm_used,
            "intensity_factor_used": row.intensity_factor_used,
        }
        for row in rows
    ]

    insert_stmt = pg_insert(WorkoutLoad).values(values)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["workout_id", "trimp_model_version"],
        set_={
            "user_id": insert_stmt.excluded.user_id,
            "local_date": insert_stmt.excluded.local_date,
            "sport": insert_stmt.excluded.sport,
            "trimp_value": insert_stmt.excluded.trimp_value,
            "trimp_source": insert_stmt.excluded.trimp_source,
            "trimp_method": insert_stmt.excluded.trimp_method,
            "hr_rest_bpm_used": insert_stmt.excluded.hr_rest_bpm_used,
            "hr_max_bpm_used": insert_stmt.excluded.hr_max_bpm_used,
            "intensity_factor_used": insert_stmt.excluded.intensity_factor_used,
            "updated_at": func.now(),
        },
    )
    db.execute(upsert_stmt)


def delete_workout_load_rows(
    db: Session,
    *,
    user_id: UUID,
    workout_ids: Iterable[int],
    trimp_model_version: int,
) -> None:
    ids = sorted(set(workout_ids))
    if not ids:
        return

    stmt = delete(WorkoutLoad).where(
        WorkoutLoad.user_id == user_id,
        WorkoutLoad.workout_id.in_(ids),
        WorkoutLoad.trimp_model_version == trimp_model_version,
    )
    db.execute(stmt)


def rebuild_daily_load_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Iterable[date],
    trimp_model_version: int,
) -> None:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return

    for current_date in unique_dates:
        delete_stmt = delete(DailyLoad).where(
            DailyLoad.user_id == user_id,
            DailyLoad.date == current_date,
            DailyLoad.trimp_model_version == trimp_model_version,
        )
        db.execute(delete_stmt)

        aggregate_stmt = (
            select(
                WorkoutLoad.sport,
                func.coalesce(func.sum(WorkoutLoad.trimp_value), 0.0).label("trimp_total"),
                func.count().label("sessions_count"),
            )
            .where(
                WorkoutLoad.user_id == user_id,
                WorkoutLoad.local_date == current_date,
                WorkoutLoad.trimp_model_version == trimp_model_version,
                WorkoutLoad.sport.in_(SUPPORTED_LOAD_SPORTS),
            )
            .group_by(WorkoutLoad.sport)
        )
        rows = db.execute(aggregate_stmt).all()
        by_sport = {
            row.sport: {
                "trimp_total": float(row.trimp_total or 0.0),
                "sessions_count": int(row.sessions_count or 0),
            }
            for row in rows
        }

        all_trimp = 0.0
        all_sessions = 0
        values: list[dict] = []
        for sport in SUPPORTED_LOAD_SPORTS:
            sport_total = by_sport.get(sport, {}).get("trimp_total", 0.0)
            sport_sessions = by_sport.get(sport, {}).get("sessions_count", 0)
            all_trimp += sport_total
            all_sessions += sport_sessions
            values.append(
                {
                    "user_id": user_id,
                    "date": current_date,
                    "sport_filter": sport,
                    "trimp_total": sport_total,
                    "sessions_count": sport_sessions,
                    "trimp_model_version": trimp_model_version,
                }
            )

        values.append(
            {
                "user_id": user_id,
                "date": current_date,
                "sport_filter": "all",
                "trimp_total": all_trimp,
                "sessions_count": all_sessions,
                "trimp_model_version": trimp_model_version,
            }
        )

        db.execute(pg_insert(DailyLoad).values(values))


def get_daily_load_rows(
    db: Session,
    *,
    user_id: UUID,
    from_date: date,
    to_date: date,
    sport_filter: str,
    trimp_model_version: int,
) -> list[tuple[date, float]]:
    stmt = (
        select(DailyLoad.date, DailyLoad.trimp_total)
        .where(
            DailyLoad.user_id == user_id,
            DailyLoad.date >= from_date,
            DailyLoad.date <= to_date,
            DailyLoad.sport_filter == sport_filter,
            DailyLoad.trimp_model_version == trimp_model_version,
        )
        .order_by(DailyLoad.date.asc())
    )
    rows = db.execute(stmt).all()
    return [(row.date, float(row.trimp_total)) for row in rows]


def get_first_daily_load_date(
    db: Session,
    *,
    user_id: UUID,
    sport_filter: str,
    trimp_model_version: int,
) -> date | None:
    stmt = select(func.min(DailyLoad.date)).where(
        DailyLoad.user_id == user_id,
        DailyLoad.sport_filter == sport_filter,
        DailyLoad.trimp_model_version == trimp_model_version,
    )
    return db.execute(stmt).scalar_one_or_none()
