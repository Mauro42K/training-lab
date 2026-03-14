import datetime as dt
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from api.repositories.daily_recovery_repository import DailyLoadContext
from api.services.readiness_service import ReadinessService


class ReadinessServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ReadinessService(MagicMock())
        self.target_date = dt.date(2026, 3, 15)

    def _recovery_row(
        self,
        *,
        local_date: dt.date,
        sleep_total_sec: int | None = None,
        hrv_sdnn_ms: float | None = None,
        resting_hr_bpm: float | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            local_date=local_date,
            sleep_total_sec=sleep_total_sec,
            hrv_sdnn_ms=hrv_sdnn_ms,
            resting_hr_bpm=resting_hr_bpm,
        )

    def _sleep_row(self, *, local_date: dt.date, total_sleep_sec: int) -> SimpleNamespace:
        return SimpleNamespace(
            local_date=local_date,
            total_sleep_sec=total_sleep_sec,
        )

    def _history_dates(self, *, days: int) -> list[dt.date]:
        return [
            self.target_date - dt.timedelta(days=offset)
            for offset in range(days, 0, -1)
        ]

    def test_complete_readiness_returns_score_label_and_confidence(self) -> None:
        recovery_history = [
            self._recovery_row(
                local_date=current_date,
                hrv_sdnn_ms=50.0,
                resting_hr_bpm=52.0,
            )
            for current_date in self._history_dates(days=28)
        ]
        sleep_history = [
            self._sleep_row(local_date=current_date, total_sleep_sec=7 * 3600 + 1800)
            for current_date in self._history_dates(days=14)
        ]

        readiness = self.service.build_readiness(
            target_date=self.target_date,
            current_recovery_row=self._recovery_row(
                local_date=self.target_date,
                sleep_total_sec=8 * 3600,
                hrv_sdnn_ms=60.0,
                resting_hr_bpm=48.0,
            ),
            recovery_history_rows=recovery_history,
            sleep_history_rows=sleep_history,
            load_rows=[],
            load_context_by_date={},
        )

        self.assertEqual(readiness.completeness_status, "complete")
        self.assertEqual(readiness.label, "Ready")
        self.assertGreaterEqual(readiness.score or 0, 75)
        self.assertGreater(readiness.confidence, 0.8)
        self.assertEqual(readiness.inputs_present, ["sleep", "hrv", "rhr"])
        self.assertEqual(readiness.inputs_missing, [])

    def test_partial_readiness_degrades_confidence_without_changing_contract(self) -> None:
        recovery_history = [
            self._recovery_row(
                local_date=current_date,
                hrv_sdnn_ms=52.0,
                resting_hr_bpm=51.0,
            )
            for current_date in self._history_dates(days=28)
        ]
        sleep_history = [
            self._sleep_row(local_date=current_date, total_sleep_sec=7 * 3600)
            for current_date in self._history_dates(days=7)
        ]

        readiness = self.service.build_readiness(
            target_date=self.target_date,
            current_recovery_row=self._recovery_row(
                local_date=self.target_date,
                sleep_total_sec=7 * 3600 + 900,
                hrv_sdnn_ms=49.0,
                resting_hr_bpm=None,
            ),
            recovery_history_rows=recovery_history,
            sleep_history_rows=sleep_history,
            load_rows=[],
            load_context_by_date={},
        )

        self.assertEqual(readiness.completeness_status, "partial")
        self.assertIsNotNone(readiness.score)
        self.assertLess(readiness.confidence, 0.8)
        self.assertEqual(readiness.inputs_present, ["sleep", "hrv"])
        self.assertEqual(readiness.inputs_missing, ["rhr"])

    def test_insufficient_readiness_returns_guarded_low_trust_score(self) -> None:
        sleep_history = [
            self._sleep_row(local_date=current_date, total_sleep_sec=8 * 3600)
            for current_date in self._history_dates(days=14)
        ]

        readiness = self.service.build_readiness(
            target_date=self.target_date,
            current_recovery_row=self._recovery_row(
                local_date=self.target_date,
                sleep_total_sec=6 * 3600 + 1800,
            ),
            recovery_history_rows=[],
            sleep_history_rows=sleep_history,
            load_rows=[],
            load_context_by_date={},
        )

        self.assertEqual(readiness.completeness_status, "insufficient")
        self.assertIsNotNone(readiness.score)
        self.assertIsNotNone(readiness.label)
        self.assertLess(readiness.confidence, 0.5)

    def test_missing_readiness_returns_no_real_score(self) -> None:
        readiness = self.service.build_readiness(
            target_date=self.target_date,
            current_recovery_row=None,
            recovery_history_rows=[],
            sleep_history_rows=[],
            load_rows=[],
            load_context_by_date={},
        )

        self.assertEqual(readiness.completeness_status, "missing")
        self.assertIsNone(readiness.score)
        self.assertIsNone(readiness.label)
        self.assertEqual(readiness.inputs_present, [])
        self.assertEqual(readiness.inputs_missing, ["sleep", "hrv", "rhr"])

    def test_isolated_missing_day_does_not_destroy_baselines(self) -> None:
        missing_gap_date = self.target_date - dt.timedelta(days=3)
        recovery_history = [
            self._recovery_row(
                local_date=current_date,
                hrv_sdnn_ms=55.0,
                resting_hr_bpm=50.0,
            )
            for current_date in self._history_dates(days=28)
            if current_date != missing_gap_date
        ]
        sleep_history = [
            self._sleep_row(local_date=current_date, total_sleep_sec=7 * 3600 + 1200)
            for current_date in self._history_dates(days=14)
            if current_date != missing_gap_date
        ]

        readiness = self.service.build_readiness(
            target_date=self.target_date,
            current_recovery_row=self._recovery_row(
                local_date=self.target_date,
                sleep_total_sec=7 * 3600 + 1800,
                hrv_sdnn_ms=57.0,
                resting_hr_bpm=49.0,
            ),
            recovery_history_rows=recovery_history,
            sleep_history_rows=sleep_history,
            load_rows=[],
            load_context_by_date={},
        )

        self.assertEqual(readiness.completeness_status, "complete")
        trace_by_name = {item.name: item for item in readiness.trace_summary}
        self.assertTrue(trace_by_name["sleep"].baseline_used)
        self.assertTrue(trace_by_name["hrv"].baseline_used)
        self.assertTrue(trace_by_name["rhr"].baseline_used)

    def test_recent_exertion_penalty_is_bounded(self) -> None:
        recovery_history = [
            self._recovery_row(
                local_date=current_date,
                hrv_sdnn_ms=52.0,
                resting_hr_bpm=51.0,
            )
            for current_date in self._history_dates(days=28)
        ]
        sleep_history = [
            self._sleep_row(local_date=current_date, total_sleep_sec=7 * 3600 + 1200)
            for current_date in self._history_dates(days=14)
        ]
        base_kwargs = dict(
            target_date=self.target_date,
            current_recovery_row=self._recovery_row(
                local_date=self.target_date,
                sleep_total_sec=7 * 3600 + 1800,
                hrv_sdnn_ms=56.0,
                resting_hr_bpm=49.0,
            ),
            recovery_history_rows=recovery_history,
            sleep_history_rows=sleep_history,
        )

        without_penalty = self.service.build_readiness(
            load_rows=[],
            load_context_by_date={},
            **base_kwargs,
        )
        high_load_rows = []
        for current_date in self._history_dates(days=28):
            load_value = 10.0
            if current_date >= self.target_date - dt.timedelta(days=7):
                load_value = 100.0
            high_load_rows.append((current_date, load_value))

        with_penalty = self.service.build_readiness(
            load_rows=high_load_rows,
            load_context_by_date={
                self.target_date - dt.timedelta(days=1): DailyLoadContext(
                    local_date=self.target_date - dt.timedelta(days=1),
                    load_present=True,
                    has_estimated_inputs=True,
                )
            },
            **base_kwargs,
        )

        self.assertIsNotNone(without_penalty.score)
        self.assertIsNotNone(with_penalty.score)
        score_delta = (without_penalty.score or 0) - (with_penalty.score or 0)
        self.assertGreaterEqual(score_delta, 0)
        self.assertLessEqual(score_delta, 5)
        self.assertTrue(with_penalty.has_estimated_context)
        self.assertEqual(with_penalty.trace_summary[-1].name, "recent_exertion")
        self.assertEqual(with_penalty.trace_summary[-1].effect, "negative")


if __name__ == "__main__":
    unittest.main()
