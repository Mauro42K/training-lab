import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api.core.config import Settings
from api.db.models import BackfillJobState
from api.repositories.backfill_repository import WorkoutBackfillRow
from api.services.trimp_backfill_service import TrimpBackfillService
from api.services.trimp_engine import TrimpEngineResult


def make_settings() -> Settings:
    return Settings(
        database_url=None,
        app_environment="test",
        training_lab_api_key=None,
        ingest_max_batch_size=500,
        trimp_active_model_version=1,
        trimp_active_method="banister_hrr",
        trimp_hr_rest_default=60,
        trimp_hr_max_default=190,
        trimp_sport_factor_run=1.0,
        trimp_sport_factor_bike=0.75,
        trimp_sport_factor_strength=0.35,
        trimp_sport_factor_walk=0.25,
        trimp_timezone_fallback="America/New_York",
    )


def make_state() -> BackfillJobState:
    return BackfillJobState(
        job_name="trimp_v1_backfill",
        trimp_model_version=1,
        status="idle",
        last_cursor_id=0,
        workouts_scanned=0,
        workouts_persisted=0,
        workouts_excluded_or_deleted=0,
        affected_dates_rebuilt=0,
        batches_completed=0,
    )


class TrimpBackfillServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = make_settings()
        self.service = TrimpBackfillService(settings=self.settings)
        self.user_id = uuid.uuid4()
        self.db = SimpleNamespace(commit=MagicMock(), rollback=MagicMock())

    def _engine_result_real(self) -> TrimpEngineResult:
        return TrimpEngineResult(
            trimp_value=25.0,
            trimp_source="estimated",
            trimp_method="banister_hrr",
            trimp_model_version=1,
            hr_rest_bpm_used=None,
            hr_max_bpm_used=None,
            intensity_factor_used=1.0,
            is_computed=True,
            is_excluded=False,
        )

    def _engine_result_excluded(self) -> TrimpEngineResult:
        return TrimpEngineResult(
            trimp_value=0.0,
            trimp_source="excluded",
            trimp_method="banister_hrr",
            trimp_model_version=1,
            hr_rest_bpm_used=None,
            hr_max_bpm_used=None,
            intensity_factor_used=None,
            is_computed=False,
            is_excluded=True,
        )

    def test_small_batch_resume_across_runs_and_finish_without_drift(self) -> None:
        state = make_state()
        row1 = WorkoutBackfillRow(
            workout_id=1,
            user_id=self.user_id,
            sport="run",
            start=dt.datetime(2026, 3, 1, 12, 0, tzinfo=dt.UTC),
            duration_sec=1800,
            avg_hr_bpm=None,
            is_deleted=False,
            user_timezone="America/New_York",
        )
        row2 = WorkoutBackfillRow(
            workout_id=2,
            user_id=self.user_id,
            sport="other",
            start=dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.UTC),
            duration_sec=1800,
            avg_hr_bpm=None,
            is_deleted=False,
            user_timezone="America/New_York",
        )

        def fetch_side_effect(_db, *, last_cursor_id: int, batch_size: int):
            self.assertEqual(batch_size, 1)
            if last_cursor_id == 0:
                return [row1]
            if last_cursor_id == 1:
                return [row2]
            return []

        upsert_calls: list[list] = []

        def upsert_capture(_db, *, rows):
            upsert_calls.append(rows)

        with (
            patch("api.services.trimp_backfill_service.get_or_create_backfill_state", return_value=state),
            patch("api.services.trimp_backfill_service.fetch_workout_batch", side_effect=fetch_side_effect),
            patch("api.services.trimp_backfill_service.upsert_workout_load_rows", side_effect=upsert_capture),
            patch("api.services.trimp_backfill_service.delete_workout_load_rows"),
            patch("api.services.trimp_backfill_service.rebuild_daily_load_for_dates"),
            patch.object(self.service.trimp_engine, "calculate_for_workout", side_effect=[self._engine_result_real(), self._engine_result_excluded()]),
        ):
            summary1 = self.service.run(self.db, batch_size=1, max_batches=1, reset=True)
            summary2 = self.service.run(self.db, batch_size=1, max_batches=1, reset=False)
            summary3 = self.service.run(self.db, batch_size=1, max_batches=None, reset=False)

        self.assertEqual(summary1.status, "idle")
        self.assertEqual(summary1.last_cursor_id, 1)
        self.assertEqual(summary2.status, "idle")
        self.assertEqual(summary2.last_cursor_id, 2)
        self.assertEqual(summary3.status, "completed")
        self.assertEqual(summary3.last_cursor_id, 2)
        self.assertEqual(summary3.workouts_scanned, 2)
        self.assertEqual(summary3.workouts_persisted, 1)
        self.assertEqual(summary3.workouts_excluded_or_deleted, 1)
        self.assertEqual(summary3.batches_completed, 2)
        self.assertEqual(len(upsert_calls), 2)
        self.assertEqual(len(upsert_calls[0]), 1)
        self.assertEqual(upsert_calls[0][0].workout_id, 1)
        self.assertEqual(len(upsert_calls[1]), 0)

    def test_reset_resets_state_only_not_data_paths(self) -> None:
        state = make_state()
        state.last_cursor_id = 99
        state.workouts_scanned = 123
        state.workouts_persisted = 90
        state.workouts_excluded_or_deleted = 33
        state.affected_dates_rebuilt = 44
        state.batches_completed = 9
        state.status = "failed"
        state.last_error = "boom"

        with (
            patch("api.services.trimp_backfill_service.get_or_create_backfill_state", return_value=state),
            patch("api.services.trimp_backfill_service.fetch_workout_batch", return_value=[]),
            patch("api.services.trimp_backfill_service.upsert_workout_load_rows") as upsert_mock,
            patch("api.services.trimp_backfill_service.delete_workout_load_rows") as delete_mock,
        ):
            summary = self.service.run(self.db, batch_size=10, max_batches=None, reset=True)

        self.assertEqual(summary.status, "completed")
        self.assertEqual(summary.last_cursor_id, 0)
        self.assertEqual(summary.workouts_scanned, 0)
        self.assertEqual(summary.workouts_persisted, 0)
        self.assertEqual(summary.workouts_excluded_or_deleted, 0)
        self.assertEqual(summary.affected_dates_rebuilt, 0)
        self.assertEqual(summary.batches_completed, 0)
        upsert_mock.assert_not_called()
        delete_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
