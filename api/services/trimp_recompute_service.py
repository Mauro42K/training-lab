from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from api.core.config import Settings, get_settings
from api.repositories.load_repository import (
    WorkoutLoadUpsert,
    WorkoutSnapshot,
    delete_workout_load_rows,
    get_workout_snapshots_by_uuids,
    rebuild_daily_load_for_dates,
    upsert_workout_load_rows,
)
from api.services.local_date import resolve_local_date
from api.services.trimp_engine import TrimpEngineService


@dataclass(frozen=True)
class RecomputeSummary:
    upserted_workout_load_rows: int
    deleted_workout_load_rows: int
    rebuilt_dates: int


class TrimpRecomputeService:
    def __init__(
        self,
        *,
        trimp_engine: TrimpEngineService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.trimp_engine = trimp_engine or TrimpEngineService(settings=self.settings)

    def recompute_for_workout_uuids(
        self,
        db: Session,
        *,
        user_id: UUID,
        user_timezone: str | None,
        workout_uuids: Sequence[UUID],
        pre_snapshots: dict[UUID, WorkoutSnapshot],
    ) -> RecomputeSummary:
        if not workout_uuids:
            return RecomputeSummary(
                upserted_workout_load_rows=0,
                deleted_workout_load_rows=0,
                rebuilt_dates=0,
            )

        post_snapshots = get_workout_snapshots_by_uuids(
            db,
            user_id=user_id,
            workout_uuids=workout_uuids,
        )

        affected_dates = self._collect_affected_dates(
            pre_snapshots=pre_snapshots,
            post_snapshots=post_snapshots,
            user_timezone=user_timezone,
        )

        to_upsert: list[WorkoutLoadUpsert] = []
        to_delete_ids: set[int] = set()

        for workout_uuid in workout_uuids:
            post = post_snapshots.get(workout_uuid)
            if post is None:
                continue

            if post.is_deleted:
                to_delete_ids.add(post.workout_id)
                continue

            result = self.trimp_engine.calculate_for_workout(
                user_id=user_id,
                sport=post.sport,
                duration_sec=post.duration_sec,
                avg_hr_bpm=post.avg_hr_bpm,
            )

            # Do not persist excluded results in workout_load.
            if result.is_excluded:
                to_delete_ids.add(post.workout_id)
                continue

            local_date = resolve_local_date(
                instant=post.start,
                user_timezone=user_timezone,
                fallback_timezone=self.settings.trimp_timezone_fallback,
            )
            to_upsert.append(
                WorkoutLoadUpsert(
                    workout_id=post.workout_id,
                    user_id=user_id,
                    local_date=local_date,
                    sport=post.sport,
                    trimp_value=result.trimp_value,
                    trimp_source=result.trimp_source,
                    trimp_model_version=result.trimp_model_version,
                    trimp_method=result.trimp_method,
                    hr_rest_bpm_used=result.hr_rest_bpm_used,
                    hr_max_bpm_used=result.hr_max_bpm_used,
                    intensity_factor_used=result.intensity_factor_used,
                )
            )

        delete_workout_load_rows(
            db,
            user_id=user_id,
            workout_ids=to_delete_ids,
            trimp_model_version=self.settings.trimp_active_model_version,
        )
        upsert_workout_load_rows(db, rows=to_upsert)
        rebuild_daily_load_for_dates(
            db,
            user_id=user_id,
            dates=affected_dates,
            trimp_model_version=self.settings.trimp_active_model_version,
        )

        return RecomputeSummary(
            upserted_workout_load_rows=len(to_upsert),
            deleted_workout_load_rows=len(to_delete_ids),
            rebuilt_dates=len(affected_dates),
        )

    def _collect_affected_dates(
        self,
        *,
        pre_snapshots: dict[UUID, WorkoutSnapshot],
        post_snapshots: dict[UUID, WorkoutSnapshot],
        user_timezone: str | None,
    ) -> set[date]:
        affected_dates: set[date] = set()

        for snapshot in pre_snapshots.values():
            affected_dates.add(
                resolve_local_date(
                    instant=snapshot.start,
                    user_timezone=user_timezone,
                    fallback_timezone=self.settings.trimp_timezone_fallback,
                )
            )

        for snapshot in post_snapshots.values():
            affected_dates.add(
                resolve_local_date(
                    instant=snapshot.start,
                    user_timezone=user_timezone,
                    fallback_timezone=self.settings.trimp_timezone_fallback,
                )
            )

        return affected_dates
