import datetime as dt
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from api.services.daily_domains_query_service import DailyDomainsQueryService
from api.services.home_summary_service import HomeSummaryService
from api.schemas.daily_domains import ReadinessSummaryItem, ReadinessTraceInput


class DailyDomainsQueryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user = SimpleNamespace(id=uuid.uuid4())

    def test_activity_preserves_null_active_energy(self) -> None:
        with (
            patch("api.services.daily_domains_query_service.get_or_create_default_user", return_value=self.user),
            patch(
                "api.services.daily_domains_query_service.get_daily_activity_range",
                return_value=[
                    SimpleNamespace(
                        local_date=dt.date(2026, 3, 7),
                        steps=9000,
                        walking_running_distance_m=6500.0,
                        active_energy_kcal=None,
                        completeness_status="complete",
                        provider="apple_health",
                        source_count=1,
                        has_mixed_sources=False,
                        primary_device_name="Apple Watch",
                    )
                ],
            ),
        ):
            response = DailyDomainsQueryService(self.db).get_activity(
                from_date=dt.date(2026, 3, 7),
                to_date=dt.date(2026, 3, 7),
            )

        self.assertEqual(len(response.items), 1)
        self.assertIsNone(response.items[0].active_energy_kcal)

    def test_body_query_uses_canonicalized_useful_days_only(self) -> None:
        with (
            patch("api.services.daily_domains_query_service.get_or_create_default_user", return_value=self.user),
            patch(
                "api.services.daily_domains_query_service.get_body_measurements_range",
                return_value=[
                    SimpleNamespace(
                        local_date=dt.date(2026, 3, 7),
                        measurement_type="body_fat_pct",
                        measured_at=dt.datetime(2026, 3, 7, 7, 0, tzinfo=dt.UTC),
                        measurement_value=18.0,
                        source_count=1,
                        has_mixed_sources=False,
                        source_bundle_id="com.apple.health",
                        primary_device_name="Scale",
                    ),
                    SimpleNamespace(
                        local_date=dt.date(2026, 3, 8),
                        measurement_type="weight_kg",
                        measured_at=dt.datetime(2026, 3, 8, 7, 0, tzinfo=dt.UTC),
                        measurement_value=70.1,
                        source_count=1,
                        has_mixed_sources=False,
                        source_bundle_id="com.apple.health",
                        primary_device_name="Scale",
                    ),
                ],
            ),
        ):
            response = DailyDomainsQueryService(self.db).get_body_measurements(
                from_date=dt.date(2026, 3, 7),
                to_date=dt.date(2026, 3, 8),
            )

        self.assertEqual(len(response.items), 1)
        self.assertEqual(response.items[0].date, dt.date(2026, 3, 8))
        self.assertEqual(response.items[0].weight_kg, 70.1)


class HomeSummaryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        self.user = SimpleNamespace(id=uuid.uuid4())

    def test_home_summary_composes_existing_domains_only(self) -> None:
        target_date = dt.date(2026, 3, 7)
        with (
            patch("api.services.home_summary_service.get_or_create_default_user", return_value=self.user),
            patch(
                "api.services.home_summary_service.get_daily_sleep_summary_by_date",
                return_value=SimpleNamespace(
                    local_date=target_date,
                    total_sleep_sec=8 * 3600,
                    main_sleep_duration_sec=7 * 3600,
                    naps_count=1,
                    naps_total_sleep_sec=1800,
                    completeness_status="complete",
                    provider="apple_health",
                    source_count=1,
                    has_mixed_sources=False,
                    primary_device_name="Apple Watch",
                ),
            ),
            patch("api.services.home_summary_service.get_daily_activity_by_date", return_value=None),
            patch("api.services.home_summary_service.get_daily_recovery_by_date", return_value=None),
            patch(
                "api.services.home_summary_service.get_body_measurements_for_dates",
                return_value=[],
            ),
            patch(
                "api.services.home_summary_service.ReadinessService.get_readiness",
                return_value=ReadinessSummaryItem(
                    score=78,
                    label="Ready",
                    confidence=0.91,
                    completeness_status="complete",
                    inputs_present=["sleep", "hrv", "rhr"],
                    inputs_missing=[],
                    model_version=1,
                    has_estimated_context=False,
                    trace_summary=[
                        ReadinessTraceInput(
                            name="sleep",
                            role="primary",
                            present=True,
                            baseline_used=True,
                            effect="positive",
                        )
                    ],
                ),
            ),
        ):
            response = HomeSummaryService(self.db).get_summary(target_date=target_date)

        self.assertEqual(response.date, target_date)
        self.assertIsNotNone(response.sleep)
        self.assertIsNone(response.activity)
        self.assertIsNone(response.recovery)
        self.assertIsNone(response.body_measurements)
        self.assertIsNotNone(response.readiness)
        self.assertEqual(response.readiness.label, "Ready")


if __name__ == "__main__":
    unittest.main()
