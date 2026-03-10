import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from api.core.config import Settings
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
        self.assertEqual([item.trimp for item in response.items], [10.0, 0.0, 30.0, 0.0, 0.0])

        kwargs = get_rows_mock.call_args.kwargs
        self.assertEqual(kwargs["from_date"], dt.date(2026, 3, 1))
        self.assertEqual(kwargs["to_date"], today)
        self.assertEqual(kwargs["sport_filter"], "all")

    def test_days_one_returns_exactly_one_item(self) -> None:
        today = dt.date(2026, 3, 5)
        with (
            patch("api.services.training_load_service.get_or_create_default_user", return_value=self.user),
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
        self.assertEqual(response.items[0].trimp, 12.5)


if __name__ == "__main__":
    unittest.main()
