import datetime as dt
import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")

from api.db.session import get_db
from api.dependencies.auth import require_api_key
from api.main import app
from api.schemas.daily_domains import (
    CoreMetricsSummaryItem,
    DailyActivityDomainItem,
    DailyActivityDomainResponse,
    HomeSummaryResponse,
    ReadinessExplainability,
    ReadinessExplainabilityItem,
    ReadinessSummaryItem,
    ReadinessTraceInput,
)


class DailyDomainsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[require_api_key] = lambda: None
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_activity_endpoint_returns_service_response(self) -> None:
        service_response = DailyActivityDomainResponse(
            items=[
                DailyActivityDomainItem(
                    date=dt.date(2026, 3, 7),
                    steps=9000,
                    walking_running_distance_m=6500.0,
                    active_energy_kcal=None,
                    completeness_status="complete",
                    provider="apple_health",
                    source_count=1,
                    has_mixed_sources=False,
                    primary_device_name="Apple Watch",
                )
            ]
        )
        with patch(
            "api.routers.v1.daily_domains.DailyDomainsQueryService.get_activity",
            return_value=service_response,
        ) as service_mock:
            response = self.client.get(
                "/v1/daily-domains/activity?from=2026-03-07&to=2026-03-07",
                headers={"X-API-KEY": "test-key"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["items"][0]["active_energy_kcal"])
        service_mock.assert_called_once()

    def test_invalid_range_returns_422(self) -> None:
        response = self.client.get(
            "/v1/daily-domains/sleep?from=2026-03-08&to=2026-03-07",
            headers={"X-API-KEY": "test-key"},
        )
        self.assertEqual(response.status_code, 422)

    def test_home_summary_endpoint_returns_service_response(self) -> None:
        service_response = HomeSummaryResponse(
            date=dt.date(2026, 3, 7),
            sleep=None,
            activity=None,
            recovery=None,
            body_measurements=None,
            readiness=ReadinessSummaryItem(
                score=64,
                label="Moderate",
                confidence=0.68,
                completeness_status="partial",
                inputs_present=["sleep", "hrv"],
                inputs_missing=["rhr"],
                model_version=1,
                has_estimated_context=False,
                trace_summary=[
                    ReadinessTraceInput(
                        name="sleep",
                        role="primary",
                        present=True,
                        baseline_used=True,
                        effect="neutral",
                    )
                ],
                explainability=ReadinessExplainability(
                    completeness_status="partial",
                    confidence=0.68,
                    model_version=1,
                    items=[
                        ReadinessExplainabilityItem(
                            key="sleep",
                            role="primary_driver",
                            status="measured",
                            effect="neutral",
                            display_value="7h 30m",
                            display_unit=None,
                            baseline_value="7h",
                            baseline_unit=None,
                            is_baseline_sufficient=True,
                            short_reason="Sleep held near usual.",
                        ),
                        ReadinessExplainabilityItem(
                            key="recent_exertion",
                            role="secondary_context",
                            status="estimated",
                            effect="negative",
                            display_value="182",
                            display_unit="load",
                            baseline_value="140",
                            baseline_unit="load",
                            is_baseline_sufficient=True,
                            short_reason="Exertion stayed elevated.",
                        ),
                    ],
                ),
            ),
            core_metrics=CoreMetricsSummaryItem(
                seven_day_load=182.0,
                fitness=36.4,
                fatigue=41.2,
                history_status="partial",
            ),
        )
        with patch(
            "api.routers.v1.daily_domains.HomeSummaryService.get_summary",
            return_value=service_response,
        ) as service_mock:
            response = self.client.get(
                "/v1/home/summary?date=2026-03-07",
                headers={"X-API-KEY": "test-key"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["sleep"])
        self.assertEqual(response.json()["readiness"]["label"], "Moderate")
        self.assertEqual(
            response.json()["readiness"]["explainability"]["items"][0]["role"],
            "primary_driver",
        )
        self.assertEqual(
            response.json()["readiness"]["explainability"]["items"][1]["status"],
            "estimated",
        )
        self.assertEqual(response.json()["core_metrics"]["seven_day_load"], 182.0)
        self.assertEqual(response.json()["core_metrics"]["history_status"], "partial")
        service_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
