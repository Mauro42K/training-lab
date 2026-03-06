import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import BackfillJobState, User, Workout


@dataclass(frozen=True)
class WorkoutBackfillRow:
    workout_id: int
    user_id: UUID
    sport: str
    start: dt.datetime
    duration_sec: int
    avg_hr_bpm: float | None
    is_deleted: bool
    user_timezone: str | None


def get_or_create_backfill_state(
    db: Session,
    *,
    job_name: str,
    trimp_model_version: int,
) -> BackfillJobState:
    stmt = select(BackfillJobState).where(
        BackfillJobState.job_name == job_name,
        BackfillJobState.trimp_model_version == trimp_model_version,
    )
    state = db.execute(stmt).scalar_one_or_none()
    if state is not None:
        return state

    state = BackfillJobState(
        job_name=job_name,
        trimp_model_version=trimp_model_version,
        status="idle",
        last_cursor_id=0,
        workouts_scanned=0,
        workouts_persisted=0,
        workouts_excluded_or_deleted=0,
        affected_dates_rebuilt=0,
        batches_completed=0,
    )
    db.add(state)
    db.flush()
    return state


def fetch_workout_batch(
    db: Session,
    *,
    last_cursor_id: int,
    batch_size: int,
) -> list[WorkoutBackfillRow]:
    stmt = (
        select(
            Workout.id,
            Workout.user_id,
            Workout.sport,
            Workout.start,
            Workout.duration_sec,
            Workout.avg_hr_bpm,
            Workout.is_deleted,
            User.timezone,
        )
        .join(User, User.id == Workout.user_id)
        .where(Workout.id > last_cursor_id)
        .order_by(Workout.id.asc())
        .limit(batch_size)
    )
    rows = db.execute(stmt).all()
    return [
        WorkoutBackfillRow(
            workout_id=row.id,
            user_id=row.user_id,
            sport=row.sport,
            start=row.start,
            duration_sec=row.duration_sec,
            avg_hr_bpm=row.avg_hr_bpm,
            is_deleted=row.is_deleted,
            user_timezone=row.timezone,
        )
        for row in rows
    ]


def reset_backfill_state(state: BackfillJobState) -> None:
    state.status = "idle"
    state.last_cursor_id = 0
    state.workouts_scanned = 0
    state.workouts_persisted = 0
    state.workouts_excluded_or_deleted = 0
    state.affected_dates_rebuilt = 0
    state.batches_completed = 0
    state.started_at = None
    state.finished_at = None
    state.last_error = None


def mark_backfill_started(state: BackfillJobState) -> None:
    state.status = "running"
    state.started_at = dt.datetime.now(dt.UTC)
    state.finished_at = None
    state.last_error = None


def apply_batch_progress(
    state: BackfillJobState,
    *,
    last_cursor_id: int,
    workouts_scanned: int,
    workouts_persisted: int,
    workouts_excluded_or_deleted: int,
    affected_dates_rebuilt: int,
) -> None:
    state.last_cursor_id = last_cursor_id
    state.workouts_scanned += workouts_scanned
    state.workouts_persisted += workouts_persisted
    state.workouts_excluded_or_deleted += workouts_excluded_or_deleted
    state.affected_dates_rebuilt += affected_dates_rebuilt
    state.batches_completed += 1
    state.status = "running"
    state.last_error = None


def mark_backfill_completed(state: BackfillJobState) -> None:
    state.status = "completed"
    state.finished_at = dt.datetime.now(dt.UTC)
    state.last_error = None


def mark_backfill_failed(state: BackfillJobState, *, error_message: str) -> None:
    state.status = "failed"
    state.last_error = error_message[:1024]
    state.finished_at = dt.datetime.now(dt.UTC)
