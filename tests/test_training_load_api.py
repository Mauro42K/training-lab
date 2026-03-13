import datetime as dt
import os
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")

from api.db.session import get_db
from api.dependencies.auth import require_api_key
from api.main import app
from api.core.config import Settings
from api.schemas.training_load import TrainingLoadItem, TrainingLoadResponse
from api.services.training_load_service import TrainingLoadService


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


class TrainingLoadServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = make_settings()
        self.db = object()
        self.service = TrainingLoadService(self.db, settings=self.settings)
        self.user = SimpleNamespace(id=uuid.uuid4(), timezone="America/New_York")

    def test_zero_fill_and_ascending_output(self) -> None:
        today = dt.date(2026, 3, 5)
        rows = [
            (dt.date(2026, 3, 3), 30.0),
            (dt.date(2026, 3, 1), 10.0),
        ]

        with (
            patch("api.services.training_load_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.training_load_service.get_first_daily_load_date", return_value=dt.date(2026, 3, 1)),
            patch("api.services.training_load_service.get_daily_load_rows", return_value=rows) as get_rows_mock,
        ):
            response = self.service.get_training_load(
                days=5,
                sport="all",
                today_local=today,
            )

        self.assertEqual(len(response.items), 5)
        self.assertEqual(
            [item.date for item in response.items],
            [
                dt.date(2026, 3, 1),
                dt.date(2026, 3, 2),
                dt.date(2026, 3, 3),
                dt.date(2026, 3, 4),
                dt.date(2026, 3, 5),
            ],
        )
        self.assertEqual([item.load for item in response.items], [10.0, 0.0, 30.0, 0.0, 0.0])
        self.assertEqual([item.trimp for item in response.items], [10.0, 0.0, 30.0, 0.0, 0.0])
        self.assertEqual(response.history_status, "insufficient_history")
        self.assertIsNone(response.semantic_state)
        self.assertEqual(response.latest_load, 0.0)

        kwargs = get_rows_mock.call_args.kwargs
        self.assertEqual(kwargs["from_date"], dt.date(2026, 1, 19))
        self.assertEqual(kwargs["to_date"], today)
        self.assertEqual(kwargs["sport_filter"], "all")

    def test_days_one_returns_exactly_one_item(self) -> None:
        today = dt.date(2026, 3, 5)
        with (
            patch("api.services.training_load_service.get_or_create_default_user", return_value=self.user),
            patch("api.services.training_load_service.get_first_daily_load_date", return_value=today),
            patch(
                "api.services.training_load_service.get_daily_load_rows",
                return_value=[(today, 12.5)],
            ),
        ):
            response = self.service.get_training_load(
                days=1,
                sport="run",
                today_local=today,
            )

        self.assertEqual(len(response.items), 1)
        self.assertEqual(response.items[0].date, today)
        self.assertEqual(response.items[0].load, 12.5)
        self.assertEqual(response.items[0].trimp, 12.5)
        self.assertEqual(response.history_status, "insufficient_history")

    def test_semantic_state_uses_smoothed_acute_load_vs_capacity(self) -> None:
        today = dt.date(2026, 3, 5)
        first_useful_date = today - dt.timedelta(days=41)
        spike_day = today - dt.timedelta(days=1)
        rows = [(spike_day, 100.0)]

        with (
            patch("api.services.training_load_service.get_or_create_default_user", return_value=self.user),
            patch(
                "api.services.training_load_service.get_first_daily_load_date",
                return_value=first_useful_date,
            ),
            patch("api.services.training_load_service.get_daily_load_rows", return_value=rows),
        ):
            response = self.service.get_training_load(
                days=28,
                sport="all",
                today_local=today,
            )

        self.assertEqual(response.history_status, "available")
        self.assertEqual(response.latest_load, 0.0)
        self.assertGreater(response.latest_capacity, 0.0)
        self.assertEqual(response.semantic_state, "above_capacity")

    def test_history_status_uses_calendar_coverage_not_row_count(self) -> None:
        today = dt.date(2026, 3, 5)
        first_useful_date = today - dt.timedelta(days=59)
        sparse_rows = [
            (first_useful_date, 22.0),
            (today - dt.timedelta(days=12), 15.0),
            (today - dt.timedelta(days=1), 18.0),
        ]

        with (
            patch("api.services.training_load_service.get_or_create_default_user", return_value=self.user),
            patch(
                "api.services.training_load_service.get_first_daily_load_date",
                return_value=first_useful_date,
            ),
            patch("api.services.training_load_service.get_daily_load_rows", return_value=sparse_rows),
        ):
            response = self.service.get_training_load(
                days=28,
                sport="all",
                today_local=today,
            )

        self.assertEqual(response.history_status, "available")

    def test_history_status_thresholds(self) -> None:
        today = dt.date(2026, 3, 5)
        cases = [
            (today - dt.timedelta(days=41), "available"),
            (today - dt.timedelta(days=13), "partial"),
            (today - dt.timedelta(days=12), "insufficient_history"),
            (None, "missing"),
        ]

        for first_useful_date, expected in cases:
            with self.subTest(expected=expected):
                with (
                    patch(
                        "api.services.training_load_service.get_or_create_default_user",
                        return_value=self.user,
                    ),
                    patch(
                        "api.services.training_load_service.get_first_daily_load_date",
                        return_value=first_useful_date,
                    ),
                    patch("api.services.training_load_service.get_daily_load_rows", return_value=[]),
                ):
                    response = self.service.get_training_load(
                        days=28,
                        sport="all",
                        today_local=today,
                    )

                self.assertEqual(response.history_status, expected)
                if expected in {"missing", "insufficient_history"}:
                    self.assertIsNone(response.semantic_state)

    def test_capacity_is_returned_as_daily_series_not_flat_latest_replication(self) -> None:
        today = dt.date(2026, 3, 5)
        first_useful_date = today - dt.timedelta(days=41)
        rows = [
            (today - dt.timedelta(days=5), 18.0),
            (today - dt.timedelta(days=4), 24.0),
            (today - dt.timedelta(days=3), 33.0),
            (today - dt.timedelta(days=2), 41.0),
            (today - dt.timedelta(days=1), 52.0),
            (today, 60.0),
        ]

        with (
            patch("api.services.training_load_service.get_or_create_default_user", return_value=self.user),
            patch(
                "api.services.training_load_service.get_first_daily_load_date",
                return_value=first_useful_date,
            ),
            patch("api.services.training_load_service.get_daily_load_rows", return_value=rows),
        ):
            response = self.service.get_training_load(
                days=7,
                sport="all",
                today_local=today,
            )

        capacities = [round(item.capacity, 4) for item in response.items]
        self.assertGreater(len(set(capacities)), 1)
        self.assertEqual(round(response.latest_capacity, 4), capacities[-1])
        self.assertNotEqual(capacities[-1], capacities[0])


class TrainingLoadApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[require_api_key] = lambda: None
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_training_load_endpoint_returns_extended_contract(self) -> None:
        service_response = TrainingLoadResponse(
            items=[
                TrainingLoadItem(
                    date=dt.date(2026, 3, 5),
                    load=42.0,
                    capacity=38.5,
                    trimp=42.0,
                )
            ],
            history_status="partial",
            semantic_state="near_limit",
            latest_load=42.0,
            latest_capacity=38.5,
        )

        with patch(
            "api.routers.v1.training_load.TrainingLoadService.get_training_load",
            return_value=service_response,
        ) as service_mock:
            response = self.client.get(
                "/v1/training-load?days=28&sport=all",
                headers={"X-API-KEY": "test-key"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["history_status"], "partial")
        self.assertEqual(payload["semantic_state"], "near_limit")
        self.assertEqual(payload["latest_load"], 42.0)
        self.assertEqual(payload["latest_capacity"], 38.5)
        self.assertEqual(payload["items"][0]["load"], 42.0)
        self.assertEqual(payload["items"][0]["capacity"], 38.5)
        self.assertEqual(payload["items"][0]["trimp"], 42.0)
        service_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
