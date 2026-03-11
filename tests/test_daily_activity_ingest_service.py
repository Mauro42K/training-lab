import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api.core.config import Settings
from api.schemas.ingest import DailyActivityIngestItem, DailyActivityIngestRequest
from api.services.daily_activity_ingest_service import DailyActivityIngestService
from api.services.ingest_service import IdempotencyConflictError


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


class DailyActivityIngestServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user = SimpleNamespace(id=uuid.uuid4(), timezone="America/New_York")
        self.payload = DailyActivityIngestRequest(
            timezone="America/Mexico_City",
            daily_activity=[
                DailyActivityIngestItem(
                    bucket_start=dt.datetime(2026, 3, 3, 6, 0, tzinfo=dt.UTC),
                    steps=8000,
                    walking_running_distance_m=6200.0,
                    active_energy_kcal=None,
                    primary_device_name="Apple Watch",
                )
            ],
        )

    def test_ingest_daily_activity_upserts_and_invalidates_recovery(self) -> None:
        with (
            patch("api.services.daily_activity_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.daily_activity_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.daily_activity_ingest_service.get_record", return_value=None),
            patch("api.services.daily_activity_ingest_service.update_user_timezone_if_valid", return_value=True),
            patch(
                "api.services.daily_activity_ingest_service.get_existing_daily_activity_dates",
                return_value=set(),
            ),
            patch(
                "api.services.daily_activity_ingest_service.DailyDomainRecomputeService.reset_daily_rows_for_dates",
                return_value=SimpleNamespace(
                    deleted_daily_sleep_summary_rows=0,
                    deleted_daily_activity_rows=0,
                    deleted_daily_recovery_rows=1,
                    affected_dates=1,
                ),
            ) as reset_mock,
            patch(
                "api.services.daily_activity_ingest_service.DailyRecoveryRecomputeService.recompute_for_dates",
                return_value=SimpleNamespace(rebuilt_dates=1, rebuilt_daily_recovery_rows=0),
            ),
            patch("api.services.daily_activity_ingest_service.upsert_daily_activity_rows") as upsert_mock,
            patch("api.services.daily_activity_ingest_service.create_record"),
        ):
            response = DailyActivityIngestService(self.db).ingest_daily_activity(
                payload=self.payload,
                idempotency_key="activity-key-1",
            )

        self.assertEqual(response.inserted, 1)
        self.assertEqual(response.updated, 0)
        self.assertEqual(response.rebuilt_dates, 1)
        self.assertEqual(response.invalidated_daily_recovery_dates, 1)
        rows = upsert_mock.call_args.kwargs["rows"]
        self.assertEqual(rows[0].local_date, dt.date(2026, 3, 3))
        self.assertEqual(rows[0].completeness_status, "complete")
        self.assertIsNone(rows[0].active_energy_kcal)
        self.assertFalse(reset_mock.call_args.kwargs["include_sleep"])
        self.assertTrue(reset_mock.call_args.kwargs["include_activity"])
        self.assertTrue(reset_mock.call_args.kwargs["include_recovery"])
        self.db.commit.assert_called_once()

    def test_steps_only_day_is_partial_and_still_persists(self) -> None:
        payload = DailyActivityIngestRequest(
            timezone="America/Mexico_City",
            daily_activity=[
                DailyActivityIngestItem(
                    bucket_start=dt.datetime(2026, 3, 3, 6, 0, tzinfo=dt.UTC),
                    steps=4000,
                )
            ],
        )
        with (
            patch("api.services.daily_activity_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.daily_activity_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.daily_activity_ingest_service.get_record", return_value=None),
            patch("api.services.daily_activity_ingest_service.update_user_timezone_if_valid", return_value=True),
            patch(
                "api.services.daily_activity_ingest_service.get_existing_daily_activity_dates",
                return_value=set(),
            ),
            patch(
                "api.services.daily_activity_ingest_service.DailyDomainRecomputeService.reset_daily_rows_for_dates",
                return_value=SimpleNamespace(
                    deleted_daily_sleep_summary_rows=0,
                    deleted_daily_activity_rows=0,
                    deleted_daily_recovery_rows=0,
                    affected_dates=1,
                ),
            ),
            patch(
                "api.services.daily_activity_ingest_service.DailyRecoveryRecomputeService.recompute_for_dates",
                return_value=SimpleNamespace(rebuilt_dates=1, rebuilt_daily_recovery_rows=0),
            ),
            patch("api.services.daily_activity_ingest_service.upsert_daily_activity_rows") as upsert_mock,
            patch("api.services.daily_activity_ingest_service.create_record"),
        ):
            DailyActivityIngestService(self.db).ingest_daily_activity(
                payload=payload,
                idempotency_key="activity-key-2",
            )

        rows = upsert_mock.call_args.kwargs["rows"]
        self.assertEqual(rows[0].completeness_status, "partial")

    def test_idempotent_replay_returns_saved_response(self) -> None:
        existing = SimpleNamespace(
            request_hash="same-hash",
            response_json={
                "inserted": 1,
                "updated": 0,
                "total_received": 1,
                "rebuilt_dates": 1,
                "invalidated_daily_recovery_dates": 0,
                "idempotent_replay": False,
            },
        )
        with (
            patch("api.services.daily_activity_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.daily_activity_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.daily_activity_ingest_service.get_record", return_value=existing),
            patch("api.services.daily_activity_ingest_service.compute_request_hash", return_value="same-hash"),
        ):
            response = DailyActivityIngestService(self.db).ingest_daily_activity(
                payload=self.payload,
                idempotency_key="activity-key-1",
            )

        self.assertTrue(response.idempotent_replay)

    def test_idempotency_conflict_raises(self) -> None:
        existing = SimpleNamespace(request_hash="different-hash", response_json={})
        with (
            patch("api.services.daily_activity_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.daily_activity_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.daily_activity_ingest_service.get_record", return_value=existing),
            patch("api.services.daily_activity_ingest_service.compute_request_hash", return_value="new-hash"),
        ):
            with self.assertRaises(IdempotencyConflictError):
                DailyActivityIngestService(self.db).ingest_daily_activity(
                    payload=self.payload,
                    idempotency_key="activity-key-1",
                )


if __name__ == "__main__":
    unittest.main()
