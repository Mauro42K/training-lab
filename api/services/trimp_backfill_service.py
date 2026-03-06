import datetime as dt
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.core.config import Settings, get_settings
from api.repositories.backfill_repository import (
    apply_batch_progress,
    fetch_workout_batch,
    get_or_create_backfill_state,
    mark_backfill_completed,
    mark_backfill_failed,
    mark_backfill_started,
    reset_backfill_state,
)
from api.repositories.load_repository import (
    WorkoutLoadUpsert,
    delete_workout_load_rows,
    rebuild_daily_load_for_dates,
    upsert_workout_load_rows,
)
from api.services.local_date import resolve_local_date
from api.services.trimp_engine import TrimpEngineService

DEFAULT_BACKFILL_JOB_NAME = "trimp_v1_backfill"


@dataclass(frozen=True)
class TrimpBackfillSummary:
    job_name: str
    status: str
    last_cursor_id: int
    workouts_scanned: int
    workouts_persisted: int
    workouts_excluded_or_deleted: int
    affected_dates_rebuilt: int
    batches_completed: int


class TrimpBackfillService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        trimp_engine: TrimpEngineService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.trimp_engine = trimp_engine or TrimpEngineService(settings=self.settings)

    def run(
        self,
        db: Session,
        *,
        batch_size: int,
        max_batches: int | None = None,
        reset: bool = False,
        job_name: str = DEFAULT_BACKFILL_JOB_NAME,
    ) -> TrimpBackfillSummary:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        if max_batches is not None and max_batches <= 0:
            raise ValueError("max_batches must be greater than zero when provided")

        trimp_model_version = self.settings.trimp_active_model_version
        state = get_or_create_backfill_state(
            db,
            job_name=job_name,
            trimp_model_version=trimp_model_version,
        )

        if reset:
            # Reset only cursor/state/metrics. Persisted workout_load and daily_load stay intact.
            reset_backfill_state(state)
            db.commit()

        mark_backfill_started(state)
        db.commit()

        batches_executed = 0
        try:
            while True:
                if max_batches is not None and batches_executed >= max_batches:
                    state.status = "idle"
                    state.finished_at = dt.datetime.now(dt.UTC)
                    db.commit()
                    return self._summary_from_state(state, job_name=job_name)

                rows = fetch_workout_batch(
                    db,
                    last_cursor_id=state.last_cursor_id,
                    batch_size=batch_size,
                )

                if not rows:
                    mark_backfill_completed(state)
                    db.commit()
                    return self._summary_from_state(state, job_name=job_name)

                to_upsert: list[WorkoutLoadUpsert] = []
                to_delete_by_user: dict = defaultdict(set)
                affected_dates_by_user: dict = defaultdict(set)

                workouts_scanned = len(rows)
                workouts_persisted = 0
                workouts_excluded_or_deleted = 0

                for row in rows:
                    local_date = resolve_local_date(
                        instant=row.start,
                        user_timezone=row.user_timezone,
                        fallback_timezone=self.settings.trimp_timezone_fallback,
                    )
                    affected_dates_by_user[row.user_id].add(local_date)

                    if row.is_deleted:
                        to_delete_by_user[row.user_id].add(row.workout_id)
                        workouts_excluded_or_deleted += 1
                        continue

                    result = self.trimp_engine.calculate_for_workout(
                        user_id=row.user_id,
                        sport=row.sport,
                        duration_sec=row.duration_sec,
                        avg_hr_bpm=row.avg_hr_bpm,
                    )

                    if result.is_excluded:
                        to_delete_by_user[row.user_id].add(row.workout_id)
                        workouts_excluded_or_deleted += 1
                        continue

                    to_upsert.append(
                        WorkoutLoadUpsert(
                            workout_id=row.workout_id,
                            user_id=row.user_id,
                            local_date=local_date,
                            sport=row.sport,
                            trimp_value=result.trimp_value,
                            trimp_source=result.trimp_source,
                            trimp_model_version=result.trimp_model_version,
                            trimp_method=result.trimp_method,
                            hr_rest_bpm_used=result.hr_rest_bpm_used,
                            hr_max_bpm_used=result.hr_max_bpm_used,
                            intensity_factor_used=result.intensity_factor_used,
                        )
                    )
                    workouts_persisted += 1

                for user_id, workout_ids in to_delete_by_user.items():
                    delete_workout_load_rows(
                        db,
                        user_id=user_id,
                        workout_ids=workout_ids,
                        trimp_model_version=trimp_model_version,
                    )
                upsert_workout_load_rows(db, rows=to_upsert)

                affected_dates_rebuilt = 0
                for user_id, dates in affected_dates_by_user.items():
                    rebuild_daily_load_for_dates(
                        db,
                        user_id=user_id,
                        dates=dates,
                        trimp_model_version=trimp_model_version,
                    )
                    affected_dates_rebuilt += len(dates)

                apply_batch_progress(
                    state,
                    last_cursor_id=rows[-1].workout_id,
                    workouts_scanned=workouts_scanned,
                    workouts_persisted=workouts_persisted,
                    workouts_excluded_or_deleted=workouts_excluded_or_deleted,
                    affected_dates_rebuilt=affected_dates_rebuilt,
                )
                db.commit()
                batches_executed += 1
        except Exception as exc:
            db.rollback()
            state = get_or_create_backfill_state(
                db,
                job_name=job_name,
                trimp_model_version=trimp_model_version,
            )
            mark_backfill_failed(state, error_message=str(exc))
            db.commit()
            raise

    def _summary_from_state(self, state, *, job_name: str) -> TrimpBackfillSummary:
        return TrimpBackfillSummary(
            job_name=job_name,
            status=state.status,
            last_cursor_id=state.last_cursor_id,
            workouts_scanned=state.workouts_scanned,
            workouts_persisted=state.workouts_persisted,
            workouts_excluded_or_deleted=state.workouts_excluded_or_deleted,
            affected_dates_rebuilt=state.affected_dates_rebuilt,
            batches_completed=state.batches_completed,
        )
