from collections.abc import Sequence
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models import Workout
from api.repositories.workout_identity import WORKOUT_INGEST_IDENTITY_FIELD
from api.schemas.ingest import WorkoutIngestItem

SportType = Literal["run", "bike", "strength", "walk", "other"]


def upsert_workouts(
    db: Session,
    *,
    user_id: UUID,
    workouts: Sequence[WorkoutIngestItem],
) -> tuple[int, int]:
    if not workouts:
        return (0, 0)

    normalized = {getattr(item, WORKOUT_INGEST_IDENTITY_FIELD): item for item in workouts}
    unique_workouts = list(normalized.values())
    uuids = list(normalized.keys())

    existing_stmt = select(Workout.healthkit_workout_uuid).where(
        Workout.user_id == user_id,
        getattr(Workout, WORKOUT_INGEST_IDENTITY_FIELD).in_(uuids),
    )
    existing_rows = db.execute(existing_stmt).scalars().all()
    existing_uuids = set(existing_rows)

    values = [
        {
            "user_id": user_id,
            "healthkit_workout_uuid": item.healthkit_workout_uuid,
            "sport": item.sport,
            "start": item.start,
            "end": item.end,
            "duration_sec": item.duration_sec,
            "avg_hr_bpm": item.avg_hr_bpm,
            "distance_m": item.distance_m,
            "energy_kcal": item.energy_kcal,
            "source_bundle_id": item.source_bundle_id,
            "device_name": item.device_name,
            "is_deleted": item.is_deleted,
        }
        for item in unique_workouts
        # Tombstone for unknown workout UUID is a no-op for idempotent delete behavior.
        if not (item.is_deleted and item.healthkit_workout_uuid not in existing_uuids)
    ]

    if not values:
        return (0, 0)

    insert_stmt = pg_insert(Workout).values(values)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["user_id", "healthkit_workout_uuid"],
        set_={
            "sport": insert_stmt.excluded.sport,
            "start": insert_stmt.excluded.start,
            "end": insert_stmt.excluded.end,
            "duration_sec": insert_stmt.excluded.duration_sec,
            "avg_hr_bpm": insert_stmt.excluded.avg_hr_bpm,
            "distance_m": insert_stmt.excluded.distance_m,
            "energy_kcal": insert_stmt.excluded.energy_kcal,
            "source_bundle_id": insert_stmt.excluded.source_bundle_id,
            "device_name": insert_stmt.excluded.device_name,
            "is_deleted": insert_stmt.excluded.is_deleted,
            "updated_at": func.now(),
        },
    )
    db.execute(upsert_stmt)

    included_uuids = {value["healthkit_workout_uuid"] for value in values}
    updated = len(existing_uuids.intersection(included_uuids))
    inserted = len(values) - updated
    return (inserted, updated)


def get_workouts(
    db: Session,
    *,
    user_id: UUID,
    from_dt: datetime,
    to_dt: datetime,
    sport: SportType | None,
) -> list[Workout]:
    filters = [
        Workout.user_id == user_id,
        Workout.is_deleted.is_(False),
        Workout.start >= from_dt,
        Workout.start <= to_dt,
    ]
    if sport is not None:
        filters.append(Workout.sport == sport)

    stmt = select(Workout).where(and_(*filters)).order_by(Workout.start.desc())
    return list(db.execute(stmt).scalars().all())


def get_daily_aggregates(
    db: Session,
    *,
    user_id: UUID,
    from_date: date,
    to_date: date,
) -> list[dict]:
    day_expr = func.date(Workout.start)
    stmt = (
        select(
            day_expr.label("date"),
            func.count().label("workouts_count"),
            func.coalesce(func.sum(Workout.duration_sec), 0).label("duration_sec_total"),
            func.coalesce(func.sum(Workout.distance_m), 0.0).label("distance_m_total"),
            func.coalesce(func.sum(Workout.energy_kcal), 0.0).label("energy_kcal_total"),
        )
        .where(
            Workout.user_id == user_id,
            Workout.is_deleted.is_(False),
            day_expr >= from_date,
            day_expr <= to_date,
        )
        .group_by(day_expr)
        .order_by(day_expr.asc())
    )

    rows = db.execute(stmt).mappings().all()
    return [dict(row) for row in rows]
