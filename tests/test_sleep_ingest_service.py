import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api.core.config import Settings
from api.repositories.daily_domains_repository import SleepSessionSnapshot
from api.schemas.ingest import SleepSessionIngestItem, SleepSessionsIngestRequest
from api.services.sleep_ingest_service import SleepIngestService
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


class SleepIngestServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user = SimpleNamespace(id=uuid.uuid4(), timezone="America/New_York")
        self.sleep_uuid = uuid.uuid4()
        self.payload = SleepSessionsIngestRequest(
            timezone="America/Mexico_City",
            sleep_sessions=[
                SleepSessionIngestItem(
                    healthkit_sleep_uuid=self.sleep_uuid,
                    start=dt.datetime(2026, 3, 2, 5, 0, tzinfo=dt.UTC),
                    end=dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.UTC),
                    primary_device_name="Apple Watch",
                )
            ],
        )

    def test_ingest_sleep_sessions_upserts_and_recomputes(self) -> None:
        with (
            patch("api.services.sleep_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.sleep_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.sleep_ingest_service.get_record", return_value=None),
            patch("api.services.sleep_ingest_service.get_sleep_session_snapshots_by_uuids", return_value={}),
            patch("api.services.sleep_ingest_service.upsert_sleep_sessions", return_value=(1, 0)) as upsert_mock,
            patch("api.services.sleep_ingest_service.update_user_timezone_if_valid", return_value=True),
            patch("api.services.sleep_ingest_service.create_record"),
            patch(
                "api.services.sleep_ingest_service.SleepRecomputeService.recompute_for_sleep_uuids",
                return_value=SimpleNamespace(rebuilt_dates=1, invalidated_daily_recovery_dates=1),
            ) as recompute_mock,
        ):
            response = SleepIngestService(self.db).ingest_sleep_sessions(
                payload=self.payload,
                idempotency_key="sleep-key-1",
            )

        self.assertEqual(response.inserted, 1)
        self.assertEqual(response.updated, 0)
        self.assertEqual(response.rebuilt_dates, 1)
        self.assertEqual(response.invalidated_daily_recovery_dates, 1)
        rows = upsert_mock.call_args.kwargs["rows"]
        self.assertEqual(rows[0].local_date, dt.date(2026, 3, 2))
        self.assertEqual(
            recompute_mock.call_args.kwargs["user_timezone"],
            "America/Mexico_City",
        )
        self.db.commit.assert_called_once()

    def test_idempotent_replay_returns_saved_response(self) -> None:
        existing = SimpleNamespace(
            request_hash="same-hash",
            response_json={
                "inserted": 1,
                "updated": 0,
                "total_received": 1,
                "rebuilt_dates": 1,
                "invalidated_daily_recovery_dates": 1,
                "idempotent_replay": False,
            },
        )
        with (
            patch("api.services.sleep_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.sleep_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.sleep_ingest_service.get_record", return_value=existing),
            patch("api.services.sleep_ingest_service.compute_request_hash", return_value="same-hash"),
        ):
            response = SleepIngestService(self.db).ingest_sleep_sessions(
                payload=self.payload,
                idempotency_key="sleep-key-1",
            )

        self.assertTrue(response.idempotent_replay)
        self.assertEqual(response.inserted, 1)

    def test_idempotency_conflict_raises(self) -> None:
        existing = SimpleNamespace(request_hash="different-hash", response_json={})
        with (
            patch("api.services.sleep_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.sleep_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.sleep_ingest_service.get_record", return_value=existing),
            patch("api.services.sleep_ingest_service.compute_request_hash", return_value="new-hash"),
        ):
            with self.assertRaises(IdempotencyConflictError):
                SleepIngestService(self.db).ingest_sleep_sessions(
                    payload=self.payload,
                    idempotency_key="sleep-key-1",
                )


class SleepRecomputeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user_id = uuid.uuid4()
        self.sleep_uuid = uuid.uuid4()
        self.snapshot = SleepSessionSnapshot(
            row_id=1,
            healthkit_sleep_uuid=self.sleep_uuid,
            local_date=dt.date(2026, 3, 2),
            start_at=dt.datetime(2026, 3, 2, 5, 0, tzinfo=dt.UTC),
            end_at=dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.UTC),
        )

    def test_recompute_resets_sleep_and_recovery_only(self) -> None:
        from api.services.sleep_recompute_service import SleepRecomputeService

        with (
            patch("api.services.sleep_recompute_service.get_settings", return_value=make_settings()),
            patch(
                "api.services.sleep_recompute_service.get_sleep_session_snapshots_by_uuids",
                return_value={self.sleep_uuid: self.snapshot},
            ),
            patch(
                "api.services.sleep_recompute_service.DailyDomainRecomputeService.collect_sleep_affected_dates",
                return_value={dt.date(2026, 3, 2)},
            ),
            patch(
                "api.services.sleep_recompute_service.DailyDomainRecomputeService.reset_daily_rows_for_dates",
                return_value=SimpleNamespace(
                    deleted_daily_sleep_summary_rows=0,
                    deleted_daily_activity_rows=0,
                    deleted_daily_recovery_rows=1,
                    affected_dates=1,
                ),
            ) as reset_mock,
            patch(
                "api.services.sleep_recompute_service.get_sleep_session_snapshots_for_summary_dates",
                return_value=[],
            ),
            patch(
                "api.services.sleep_recompute_service.DailyRecoveryRecomputeService.recompute_for_dates",
                return_value=SimpleNamespace(rebuilt_dates=1, rebuilt_daily_recovery_rows=0),
            ),
            patch("api.services.sleep_recompute_service.upsert_daily_sleep_summary_rows") as upsert_mock,
        ):
            summary = SleepRecomputeService().recompute_for_sleep_uuids(
                self.db,
                user_id=self.user_id,
                user_timezone="America/New_York",
                sleep_uuids=[self.sleep_uuid],
                pre_snapshots={},
            )

        self.assertEqual(summary.rebuilt_dates, 1)
        self.assertEqual(summary.invalidated_daily_recovery_dates, 1)
        self.assertEqual(summary.rebuilt_daily_sleep_summary_rows, 0)
        self.assertFalse(reset_mock.call_args.kwargs["include_activity"])
        upsert_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
