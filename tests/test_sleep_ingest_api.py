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
from api.schemas.ingest import IngestSleepSessionsResponse


class SleepIngestApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[require_api_key] = lambda: None
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_post_sleep_ingest_returns_service_response(self) -> None:
        sleep_uuid = str(uuid.uuid4())
        service_response = IngestSleepSessionsResponse(
            inserted=1,
            updated=0,
            total_received=1,
            rebuilt_dates=1,
            invalidated_daily_recovery_dates=1,
            idempotent_replay=False,
        )
        with patch(
            "api.routers.v1.ingest.SleepIngestService.ingest_sleep_sessions",
            return_value=service_response,
        ) as ingest_mock:
            response = self.client.post(
                "/v1/ingest/sleep",
                headers={"X-Idempotency-Key": "sleep-key-1", "X-API-KEY": "test-key"},
                json={
                    "timezone": "America/Mexico_City",
                    "sleep_sessions": [
                        {
                            "healthkit_sleep_uuid": sleep_uuid,
                            "start": dt.datetime(2026, 3, 2, 5, 0, tzinfo=dt.UTC).isoformat(),
                            "end": dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.UTC).isoformat(),
                            "category_value": "asleep",
                            "primary_device_name": "Apple Watch",
                        }
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["inserted"], 1)
        ingest_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
