import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api.core.config import Settings
from api.schemas.ingest import BodyMeasurementIngestItem, BodyMeasurementsIngestRequest
from api.services.body_measurements_ingest_service import BodyMeasurementsIngestService
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


class BodyMeasurementsIngestServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user = SimpleNamespace(id=uuid.uuid4(), timezone="America/New_York")
        self.measurement_uuid = uuid.uuid4()
        self.payload = BodyMeasurementsIngestRequest(
            timezone="America/Mexico_City",
            body_measurements=[
                BodyMeasurementIngestItem(
                    healthkit_measurement_uuid=self.measurement_uuid,
                    measurement_type="weight_kg",
                    measured_at=dt.datetime(2026, 3, 4, 13, 0, tzinfo=dt.UTC),
                    value=70.4,
                    primary_device_name="Smart Scale",
                )
            ],
        )

    def test_ingest_body_measurements_upserts_and_canonicalizes(self) -> None:
        with (
            patch("api.services.body_measurements_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.body_measurements_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.body_measurements_ingest_service.get_record", return_value=None),
            patch("api.services.body_measurements_ingest_service.update_user_timezone_if_valid", return_value=True),
            patch(
                "api.services.body_measurements_ingest_service.get_body_measurement_snapshots_by_uuids",
                side_effect=[{}, {
                    self.measurement_uuid: SimpleNamespace(
                        local_date=dt.date(2026, 3, 4)
                    )
                }],
            ),
            patch(
                "api.services.body_measurements_ingest_service.upsert_body_measurements",
                return_value=(1, 0),
            ) as upsert_mock,
            patch(
                "api.services.body_measurements_ingest_service.DailyDomainRecomputeService.collect_body_measurement_affected_dates",
                return_value={dt.date(2026, 3, 4)},
            ),
            patch(
                "api.services.body_measurements_ingest_service.get_body_measurements_for_dates",
                return_value=[SimpleNamespace(
                    local_date=dt.date(2026, 3, 4),
                    measurement_type="weight_kg",
                    measured_at=dt.datetime(2026, 3, 4, 13, 0, tzinfo=dt.UTC),
                    measurement_value=70.4,
                )],
            ),
            patch("api.services.body_measurements_ingest_service.create_record"),
        ):
            response = BodyMeasurementsIngestService(self.db).ingest_body_measurements(
                payload=self.payload,
                idempotency_key="body-key-1",
            )

        self.assertEqual(response.inserted, 1)
        self.assertEqual(response.updated, 0)
        self.assertEqual(response.affected_dates, 1)
        self.assertEqual(response.canonicalized_dates, 1)
        rows = upsert_mock.call_args.kwargs["rows"]
        self.assertEqual(rows[0].local_date, dt.date(2026, 3, 4))
        self.db.commit.assert_called_once()

    def test_idempotent_replay_returns_saved_response(self) -> None:
        existing = SimpleNamespace(
            request_hash="same-hash",
            response_json={
                "inserted": 1,
                "updated": 0,
                "total_received": 1,
                "affected_dates": 1,
                "canonicalized_dates": 1,
                "idempotent_replay": False,
            },
        )
        with (
            patch("api.services.body_measurements_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.body_measurements_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.body_measurements_ingest_service.get_record", return_value=existing),
            patch("api.services.body_measurements_ingest_service.compute_request_hash", return_value="same-hash"),
        ):
            response = BodyMeasurementsIngestService(self.db).ingest_body_measurements(
                payload=self.payload,
                idempotency_key="body-key-1",
            )

        self.assertTrue(response.idempotent_replay)

    def test_idempotency_conflict_raises(self) -> None:
        existing = SimpleNamespace(request_hash="different-hash", response_json={})
        with (
            patch("api.services.body_measurements_ingest_service.get_settings", return_value=make_settings()),
            patch("api.services.body_measurements_ingest_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.body_measurements_ingest_service.get_record", return_value=existing),
            patch("api.services.body_measurements_ingest_service.compute_request_hash", return_value="new-hash"),
        ):
            with self.assertRaises(IdempotencyConflictError):
                BodyMeasurementsIngestService(self.db).ingest_body_measurements(
                    payload=self.payload,
                    idempotency_key="body-key-1",
                )


if __name__ == "__main__":
    unittest.main()
