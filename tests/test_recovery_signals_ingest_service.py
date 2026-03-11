import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api.core.config import Settings
from api.schemas.ingest import RecoverySignalIngestItem, RecoverySignalsIngestRequest
from api.services.ingest_service import IdempotencyConflictError
from api.services.recovery_signals_ingest_service import RecoverySignalsIngestService


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


class RecoverySignalsIngestServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user = SimpleNamespace(id=uuid.uuid4(), timezone="America/New_York")
        self.signal_uuid = uuid.uuid4()
        self.payload = RecoverySignalsIngestRequest(
            timezone="America/Mexico_City",
            recovery_signals=[
                RecoverySignalIngestItem(
                    healthkit_signal_uuid=self.signal_uuid,
                    signal_type="hrv_sdnn",
                    measured_at=dt.datetime(2026, 3, 6, 12, 0, tzinfo=dt.UTC),
                    value=52.5,
                    primary_device_name="Apple Watch",
                )
            ],
        )

    def test_ingest_recovery_signals_upserts_and_rebuilds_recovery(self) -> None:
        with (
            patch("api.services.recovery_signals_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.recovery_signals_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.recovery_signals_ingest_service.get_record", return_value=None),
            patch("api.services.recovery_signals_ingest_service.update_user_timezone_if_valid", return_value=True),
            patch(
                "api.services.recovery_signals_ingest_service.get_recovery_signal_snapshots_by_uuids",
                side_effect=[{}, {
                    self.signal_uuid: SimpleNamespace(local_date=dt.date(2026, 3, 6))
                }],
            ),
            patch("api.services.recovery_signals_ingest_service.upsert_recovery_signals", return_value=(1, 0)) as upsert_mock,
            patch(
                "api.services.recovery_signals_ingest_service.DailyDomainRecomputeService.collect_recovery_signal_affected_dates",
                return_value={dt.date(2026, 3, 6)},
            ),
            patch(
                "api.services.recovery_signals_ingest_service.DailyRecoveryRecomputeService.recompute_for_dates",
                return_value=SimpleNamespace(rebuilt_dates=1, rebuilt_daily_recovery_rows=1),
            ) as recompute_mock,
            patch("api.services.recovery_signals_ingest_service.create_record"),
        ):
            response = RecoverySignalsIngestService(self.db).ingest_recovery_signals(
                payload=self.payload,
                idempotency_key="recovery-key-1",
            )

        self.assertEqual(response.inserted, 1)
        self.assertEqual(response.updated, 0)
        self.assertEqual(response.rebuilt_dates, 1)
        self.assertEqual(response.rebuilt_daily_recovery_rows, 1)
        rows = upsert_mock.call_args.kwargs["rows"]
        self.assertEqual(rows[0].local_date, dt.date(2026, 3, 6))
        recompute_mock.assert_called_once()
        self.db.commit.assert_called_once()

    def test_idempotent_replay_returns_saved_response(self) -> None:
        existing = SimpleNamespace(
            request_hash="same-hash",
            response_json={
                "inserted": 1,
                "updated": 0,
                "total_received": 1,
                "rebuilt_dates": 1,
                "rebuilt_daily_recovery_rows": 1,
                "idempotent_replay": False,
            },
        )
        with (
            patch("api.services.recovery_signals_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.recovery_signals_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.recovery_signals_ingest_service.get_record", return_value=existing),
            patch("api.services.recovery_signals_ingest_service.compute_request_hash", return_value="same-hash"),
        ):
            response = RecoverySignalsIngestService(self.db).ingest_recovery_signals(
                payload=self.payload,
                idempotency_key="recovery-key-1",
            )

        self.assertTrue(response.idempotent_replay)

    def test_idempotency_conflict_raises(self) -> None:
        existing = SimpleNamespace(request_hash="different-hash", response_json={})
        with (
            patch("api.services.recovery_signals_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.recovery_signals_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.recovery_signals_ingest_service.get_record", return_value=existing),
            patch("api.services.recovery_signals_ingest_service.compute_request_hash", return_value="new-hash"),
        ):
            with self.assertRaises(IdempotencyConflictError):
                RecoverySignalsIngestService(self.db).ingest_recovery_signals(
                    payload=self.payload,
                    idempotency_key="recovery-key-1",
                )


if __name__ == "__main__":
    unittest.main()
