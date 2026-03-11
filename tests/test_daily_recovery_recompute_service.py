import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from api.core.config import Settings
from api.repositories.daily_recovery_repository import DailyLoadContext
from api.services.daily_recovery_recompute_service import DailyRecoveryRecomputeService


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


class DailyRecoveryRecomputeServiceTests(unittest.TestCase):
    def test_recompute_resets_and_rebuilds_rows(self) -> None:
        service = DailyRecoveryRecomputeService(settings=make_settings())
        user_id = uuid.uuid4()
        local_date = dt.date(2026, 3, 6)
        with (
            patch(
                "api.services.daily_recovery_recompute_service.DailyDomainRecomputeService.reset_daily_rows_for_dates"
            ) as reset_mock,
            patch(
                "api.services.daily_recovery_recompute_service.get_daily_sleep_summary_rows_for_dates",
                return_value=[SimpleNamespace(
                    local_date=local_date,
                    total_sleep_sec=8 * 3600,
                    source_count=1,
                    has_mixed_sources=False,
                    source_bundle_id="com.apple.health",
                    primary_device_name="Apple Watch",
                )],
            ),
            patch(
                "api.services.daily_recovery_recompute_service.get_recovery_signals_for_dates",
                return_value=[],
            ),
            patch(
                "api.services.daily_recovery_recompute_service.get_daily_activity_rows_for_dates",
                return_value=[],
            ),
            patch(
                "api.services.daily_recovery_recompute_service.get_daily_load_context_for_dates",
                return_value={local_date: DailyLoadContext(local_date=local_date, load_present=False, has_estimated_inputs=False)},
            ),
            patch("api.services.daily_recovery_recompute_service.upsert_daily_recovery_rows") as upsert_mock,
        ):
            summary = service.recompute_for_dates(
                db=object(),
                user_id=user_id,
                dates=[local_date],
            )

        self.assertEqual(summary.rebuilt_dates, 1)
        self.assertEqual(summary.rebuilt_daily_recovery_rows, 1)
        self.assertFalse(reset_mock.call_args.kwargs["include_sleep"])
        self.assertFalse(reset_mock.call_args.kwargs["include_activity"])
        self.assertTrue(reset_mock.call_args.kwargs["include_recovery"])
        upsert_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
