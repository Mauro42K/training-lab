import unittest

from api.schemas.daily_domains import (
    CoreMetricsSummaryItem,
    ReadinessExplainability,
    ReadinessExplainabilityItem,
    ReadinessSummaryItem,
    ReadinessTraceInput,
)
from api.services.recommendation_service import compute_recommended_today


def _build_readiness(
    *,
    completeness_status: str,
    label: str | None,
    confidence: float,
    recent_exertion_effect: str | None = None,
) -> ReadinessSummaryItem:
    explainability_items = [
        ReadinessExplainabilityItem(
            key="sleep",
            role="primary_driver",
            status="measured",
            effect="neutral",
            display_value="8h",
            display_unit=None,
            baseline_value="7h 30m",
            baseline_unit=None,
            is_baseline_sufficient=True,
            short_reason="Sleep held near usual.",
        )
    ]
    if recent_exertion_effect is not None:
        explainability_items.append(
            ReadinessExplainabilityItem(
                key="recent_exertion",
                role="secondary_context",
                status="measured",
                effect=recent_exertion_effect,
                display_value="42",
                display_unit="load",
                baseline_value="40",
                baseline_unit="load",
                is_baseline_sufficient=True,
                short_reason="Exertion held near usual.",
            )
        )

    return ReadinessSummaryItem(
        score=78 if label == "Ready" else 64 if label == "Moderate" else 35 if label == "Recover" else None,
        label=label,
        confidence=confidence,
        completeness_status=completeness_status,
        inputs_present=["sleep", "hrv", "rhr"] if completeness_status == "complete" else ["sleep", "hrv"],
        inputs_missing=[] if completeness_status == "complete" else ["rhr"],
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
            completeness_status=completeness_status,
            confidence=confidence,
            model_version=1,
            items=explainability_items,
        ),
    )


def _build_core_metrics(*, fitness: float, fatigue: float, history_status: str = "available") -> CoreMetricsSummaryItem:
    return CoreMetricsSummaryItem(
        seven_day_load=182.0,
        fitness=fitness,
        fatigue=fatigue,
        history_status=history_status,
    )


class RecommendationServiceTests(unittest.TestCase):
    def test_missing_data_returns_sin_datos(self) -> None:
        result = compute_recommended_today(None, None)

        self.assertEqual(result.state, "sin_datos")
        self.assertEqual(result.reason_tags, ["primaries_missing"])
        self.assertTrue(result.guidance_only)

    def test_recover_maps_to_recuperar(self) -> None:
        readiness = _build_readiness(
            completeness_status="complete",
            label="Recover",
            confidence=0.93,
            recent_exertion_effect="neutral",
        )

        result = compute_recommended_today(readiness, None)

        self.assertEqual(result.state, "recuperar")
        self.assertIn("readiness_low", result.reason_tags)

    def test_moderate_maps_to_suave(self) -> None:
        readiness = _build_readiness(
            completeness_status="partial",
            label="Moderate",
            confidence=0.72,
            recent_exertion_effect="neutral",
        )

        result = compute_recommended_today(readiness, None)

        self.assertEqual(result.state, "suave")
        self.assertIn("readiness_moderate", result.reason_tags)

    def test_ready_defaults_to_estable(self) -> None:
        readiness = _build_readiness(
            completeness_status="complete",
            label="Ready",
            confidence=0.75,
            recent_exertion_effect="neutral",
        )

        result = compute_recommended_today(readiness, _build_core_metrics(fitness=50.0, fatigue=45.0))

        self.assertEqual(result.state, "estable")
        self.assertIn("readiness_high", result.reason_tags)
        self.assertNotIn("signals_mixed", result.reason_tags)

    def test_ready_promotes_to_exigente(self) -> None:
        readiness = _build_readiness(
            completeness_status="complete",
            label="Ready",
            confidence=0.91,
            recent_exertion_effect="neutral",
        )

        result = compute_recommended_today(readiness, _build_core_metrics(fitness=50.0, fatigue=40.0))

        self.assertEqual(result.state, "exigente")
        self.assertEqual(result.confidence, 0.91)

    def test_ready_is_held_back_by_mixed_signals(self) -> None:
        readiness = _build_readiness(
            completeness_status="complete",
            label="Ready",
            confidence=0.9,
            recent_exertion_effect="negative",
        )

        result = compute_recommended_today(readiness, _build_core_metrics(fitness=50.0, fatigue=40.0))

        self.assertEqual(result.state, "estable")
        self.assertIn("exertion_elevated", result.reason_tags)
        self.assertIn("signals_mixed", result.reason_tags)

    def test_ready_is_held_back_by_low_confidence(self) -> None:
        readiness = _build_readiness(
            completeness_status="complete",
            label="Ready",
            confidence=0.65,
            recent_exertion_effect="neutral",
        )

        result = compute_recommended_today(readiness, _build_core_metrics(fitness=50.0, fatigue=40.0))

        self.assertEqual(result.state, "estable")
        self.assertIn("confidence_low", result.reason_tags)
        self.assertIn("signals_mixed", result.reason_tags)

    def test_falls_back_to_core_metrics_when_recent_exertion_is_missing(self) -> None:
        readiness = _build_readiness(
            completeness_status="complete",
            label="Ready",
            confidence=0.88,
            recent_exertion_effect=None,
        )

        result = compute_recommended_today(readiness, _build_core_metrics(fitness=50.0, fatigue=60.0))

        self.assertEqual(result.state, "estable")
        self.assertIn("exertion_elevated", result.reason_tags)
        self.assertIn("signals_mixed", result.reason_tags)


if __name__ == "__main__":
    unittest.main()
