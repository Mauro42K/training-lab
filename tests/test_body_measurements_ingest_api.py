import datetime as dt
import os
import unittest
import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")

from api.db.session import get_db
from api.dependencies.auth import require_api_key
from api.main import app
from api.schemas.ingest import IngestBodyMeasurementsResponse


class BodyMeasurementsIngestApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[require_api_key] = lambda: None
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_post_body_measurements_ingest_returns_service_response(self) -> None:
        service_response = IngestBodyMeasurementsResponse(
            inserted=1,
            updated=0,
            total_received=1,
            affected_dates=1,
            canonicalized_dates=1,
            idempotent_replay=False,
        )
        with patch(
            "api.routers.v1.ingest.BodyMeasurementsIngestService.ingest_body_measurements",
            return_value=service_response,
        ) as ingest_mock:
            response = self.client.post(
                "/v1/ingest/body-measurements",
                headers={"X-Idempotency-Key": "body-key-1", "X-API-KEY": "test-key"},
                json={
                    "timezone": "America/Mexico_City",
                    "body_measurements": [
                        {
                            "healthkit_measurement_uuid": str(uuid.uuid4()),
                            "measurement_type": "weight_kg",
                            "measured_at": dt.datetime(2026, 3, 4, 13, 0, tzinfo=dt.UTC).isoformat(),
                            "value": 70.4,
                        }
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["canonicalized_dates"], 1)
        ingest_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
