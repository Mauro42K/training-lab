import datetime as dt
import unittest
import uuid
from unittest.mock import patch

from api.core.config import Settings
from api.repositories.load_repository import WorkoutSnapshot
from api.services.trimp_recompute_service import TrimpRecomputeService


def make_settings() -> Settings:
    return Settings(
        database_url=None,
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


class TrimpRecomputeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = make_settings()
        self.service = TrimpRecomputeService(settings=self.settings)
        self.user_id = uuid.uuid4()
        self.w1 = uuid.uuid4()
        self.now = dt.datetime(2026, 3, 1, 12, 0, tzinfo=dt.UTC)

    def _snapshot(
        self,
        *,
        workout_id: int,
        workout_uuid: uuid.UUID,
        sport: str,
        start: dt.datetime,
        duration_sec: int = 3600,
        avg_hr_bpm: float | None = None,
        is_deleted: bool = False,
    ) -> WorkoutSnapshot:
        return WorkoutSnapshot(
            workout_id=workout_id,
            healthkit_workout_uuid=workout_uuid,
            sport=sport,
            start=start,
            duration_sec=duration_sec,
            avg_hr_bpm=avg_hr_bpm,
            is_deleted=is_deleted,
        )

    def test_insert_workout_upserts_load_and_rebuilds_date(self) -> None:
        post = {self.w1: self._snapshot(workout_id=10, workout_uuid=self.w1, sport="run", start=self.now)}
        with (
            patch("api.services.trimp_recompute_service.get_workout_snapshots_by_uuids", return_value=post),
            patch("api.services.trimp_recompute_service.upsert_workout_load_rows") as upsert_mock,
            patch("api.services.trimp_recompute_service.delete_workout_load_rows") as delete_mock,
            patch("api.services.trimp_recompute_service.rebuild_daily_load_for_dates") as rebuild_mock,
        ):
            summary = self.service.recompute_for_workout_uuids(
                db=object(),
                user_id=self.user_id,
                user_timezone="America/New_York",
                workout_uuids=[self.w1],
                pre_snapshots={},
            )

        self.assertEqual(summary.upserted_workout_load_rows, 1)
        self.assertEqual(summary.deleted_workout_load_rows, 0)
        self.assertEqual(summary.rebuilt_dates, 1)
        upsert_rows = upsert_mock.call_args.kwargs["rows"]
        self.assertEqual(len(upsert_rows), 1)
        self.assertEqual(upsert_rows[0].sport, "run")
        delete_mock.assert_called_once()
        rebuild_dates = rebuild_mock.call_args.kwargs["dates"]
        self.assertEqual(len(list(rebuild_dates)), 1)

    def test_update_change_sport_recomputes_new_sport(self) -> None:
        pre = {self.w1: self._snapshot(workout_id=10, workout_uuid=self.w1, sport="run", start=self.now)}
        post = {self.w1: self._snapshot(workout_id=10, workout_uuid=self.w1, sport="bike", start=self.now)}
        with (
            patch("api.services.trimp_recompute_service.get_workout_snapshots_by_uuids", return_value=post),
            patch("api.services.trimp_recompute_service.upsert_workout_load_rows") as upsert_mock,
            patch("api.services.trimp_recompute_service.delete_workout_load_rows"),
            patch("api.services.trimp_recompute_service.rebuild_daily_load_for_dates") as rebuild_mock,
        ):
            self.service.recompute_for_workout_uuids(
                db=object(),
                user_id=self.user_id,
                user_timezone="America/New_York",
                workout_uuids=[self.w1],
                pre_snapshots=pre,
            )

        upsert_rows = upsert_mock.call_args.kwargs["rows"]
        self.assertEqual(upsert_rows[0].sport, "bike")
        rebuild_dates = rebuild_mock.call_args.kwargs["dates"]
        self.assertEqual(len(list(rebuild_dates)), 1)

    def test_deleted_workout_removes_load_and_rebuilds(self) -> None:
        pre = {self.w1: self._snapshot(workout_id=10, workout_uuid=self.w1, sport="run", start=self.now)}
        post = {
            self.w1: self._snapshot(
                workout_id=10,
                workout_uuid=self.w1,
                sport="run",
                start=self.now,
                is_deleted=True,
            )
        }
        with (
            patch("api.services.trimp_recompute_service.get_workout_snapshots_by_uuids", return_value=post),
            patch("api.services.trimp_recompute_service.upsert_workout_load_rows") as upsert_mock,
            patch("api.services.trimp_recompute_service.delete_workout_load_rows") as delete_mock,
            patch("api.services.trimp_recompute_service.rebuild_daily_load_for_dates") as rebuild_mock,
        ):
            self.service.recompute_for_workout_uuids(
                db=object(),
                user_id=self.user_id,
                user_timezone="America/New_York",
                workout_uuids=[self.w1],
                pre_snapshots=pre,
            )

        self.assertEqual(upsert_mock.call_args.kwargs["rows"], [])
        deleted_ids = set(delete_mock.call_args.kwargs["workout_ids"])
        self.assertEqual(deleted_ids, {10})
        self.assertEqual(len(list(rebuild_mock.call_args.kwargs["dates"])), 1)

    def test_tombstone_unknown_uuid_is_noop(self) -> None:
        with (
            patch("api.services.trimp_recompute_service.get_workout_snapshots_by_uuids", return_value={}),
            patch("api.services.trimp_recompute_service.upsert_workout_load_rows") as upsert_mock,
            patch("api.services.trimp_recompute_service.delete_workout_load_rows") as delete_mock,
            patch("api.services.trimp_recompute_service.rebuild_daily_load_for_dates") as rebuild_mock,
        ):
            summary = self.service.recompute_for_workout_uuids(
                db=object(),
                user_id=self.user_id,
                user_timezone="America/New_York",
                workout_uuids=[self.w1],
                pre_snapshots={},
            )

        self.assertEqual(summary.upserted_workout_load_rows, 0)
        self.assertEqual(summary.deleted_workout_load_rows, 0)
        self.assertEqual(summary.rebuilt_dates, 0)
        self.assertEqual(upsert_mock.call_args.kwargs["rows"], [])
        self.assertEqual(list(delete_mock.call_args.kwargs["workout_ids"]), [])
        self.assertEqual(list(rebuild_mock.call_args.kwargs["dates"]), [])

    def test_reingest_is_deterministic_for_same_input(self) -> None:
        post = {
            self.w1: self._snapshot(
                workout_id=10,
                workout_uuid=self.w1,
                sport="run",
                start=self.now,
                duration_sec=3600,
                avg_hr_bpm=150,
            )
        }

        captured_rows: list[list] = []

        def capture_rows(_db, *, rows):
            captured_rows.append(rows)

        with (
            patch("api.services.trimp_recompute_service.get_workout_snapshots_by_uuids", return_value=post),
            patch("api.services.trimp_recompute_service.upsert_workout_load_rows", side_effect=capture_rows),
            patch("api.services.trimp_recompute_service.delete_workout_load_rows"),
            patch("api.services.trimp_recompute_service.rebuild_daily_load_for_dates"),
        ):
            self.service.recompute_for_workout_uuids(
                db=object(),
                user_id=self.user_id,
                user_timezone="America/New_York",
                workout_uuids=[self.w1],
                pre_snapshots={},
            )
            self.service.recompute_for_workout_uuids(
                db=object(),
                user_id=self.user_id,
                user_timezone="America/New_York",
                workout_uuids=[self.w1],
                pre_snapshots={},
            )

        self.assertEqual(captured_rows[0], captured_rows[1])

    def test_update_that_moves_local_date_rebuilds_both_days(self) -> None:
        pre_start = dt.datetime(2026, 3, 2, 4, 30, tzinfo=dt.UTC)  # 2026-03-01 local NY
        post_start = dt.datetime(2026, 3, 2, 5, 30, tzinfo=dt.UTC)  # 2026-03-02 local NY
        pre = {
            self.w1: self._snapshot(
                workout_id=10,
                workout_uuid=self.w1,
                sport="run",
                start=pre_start,
                duration_sec=1800,
            )
        }
        post = {
            self.w1: self._snapshot(
                workout_id=10,
                workout_uuid=self.w1,
                sport="run",
                start=post_start,
                duration_sec=1800,
            )
        }
        with (
            patch("api.services.trimp_recompute_service.get_workout_snapshots_by_uuids", return_value=post),
            patch("api.services.trimp_recompute_service.upsert_workout_load_rows"),
            patch("api.services.trimp_recompute_service.delete_workout_load_rows"),
            patch("api.services.trimp_recompute_service.rebuild_daily_load_for_dates") as rebuild_mock,
        ):
            summary = self.service.recompute_for_workout_uuids(
                db=object(),
                user_id=self.user_id,
                user_timezone="America/New_York",
                workout_uuids=[self.w1],
                pre_snapshots=pre,
            )

        self.assertEqual(summary.rebuilt_dates, 2)
        rebuilt_dates = set(rebuild_mock.call_args.kwargs["dates"])
        self.assertEqual(
            rebuilt_dates,
            {dt.date(2026, 3, 1), dt.date(2026, 3, 2)},
        )


if __name__ == "__main__":
    unittest.main()
