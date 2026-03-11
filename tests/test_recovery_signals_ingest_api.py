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
from api.schemas.ingest import IngestRecoverySignalsResponse


class RecoverySignalsIngestApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[require_api_key] = lambda: None
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_post_recovery_signals_ingest_returns_service_response(self) -> None:
        service_response = IngestRecoverySignalsResponse(
            inserted=1,
            updated=0,
            total_received=1,
            rebuilt_dates=1,
            rebuilt_daily_recovery_rows=1,
            idempotent_replay=False,
        )
        with patch(
            "api.routers.v1.ingest.RecoverySignalsIngestService.ingest_recovery_signals",
            return_value=service_response,
        ) as ingest_mock:
            response = self.client.post(
                "/v1/ingest/recovery-signals",
                headers={"X-Idempotency-Key": "recovery-key-1", "X-API-KEY": "test-key"},
                json={
                    "timezone": "America/Mexico_City",
                    "recovery_signals": [
                        {
                            "healthkit_signal_uuid": str(uuid.uuid4()),
                            "signal_type": "hrv_sdnn",
                            "measured_at": dt.datetime(2026, 3, 6, 12, 0, tzinfo=dt.UTC).isoformat(),
                            "value": 52.5,
                        }
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rebuilt_daily_recovery_rows"], 1)
        ingest_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
