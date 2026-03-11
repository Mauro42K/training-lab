import datetime as dt
import unittest
import uuid
from types import SimpleNamespace

from api.repositories.daily_recovery_repository import DailyLoadContext
from api.services.daily_recovery_builder import DailyRecoveryBuilder


class DailyRecoveryBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = DailyRecoveryBuilder()
        self.user_id = uuid.uuid4()

    def _sleep_row(self, *, local_date: dt.date, total_sleep_sec: int = 8 * 3600) -> SimpleNamespace:
        return SimpleNamespace(
            local_date=local_date,
            total_sleep_sec=total_sleep_sec,
            source_count=1,
            has_mixed_sources=False,
            source_bundle_id="com.apple.health",
            primary_device_name="Apple Watch",
        )

    def _signal_row(
        self,
        *,
        local_date: dt.date,
        signal_type: str,
        value: float,
        measured_at: dt.datetime,
        primary_device_name: str | None = "Apple Watch",
    ) -> SimpleNamespace:
        return SimpleNamespace(
            local_date=local_date,
            signal_type=signal_type,
            signal_value=value,
            measured_at=measured_at,
            source_count=1,
            has_mixed_sources=False,
            source_bundle_id="com.apple.health",
            primary_device_name=primary_device_name,
        )

    def _activity_row(self, *, local_date: dt.date) -> SimpleNamespace:
        return SimpleNamespace(
            local_date=local_date,
            source_count=1,
            has_mixed_sources=False,
            source_bundle_id="com.apple.health",
            primary_device_name="Apple Watch",
        )

    def test_complete_requires_sleep_hrv_and_rhr(self) -> None:
        local_date = dt.date(2026, 3, 5)
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates=[local_date],
            sleep_rows=[self._sleep_row(local_date=local_date)],
            signal_rows=[
                self._signal_row(
                    local_date=local_date,
                    signal_type="hrv_sdnn",
                    value=55.0,
                    measured_at=dt.datetime(2026, 3, 5, 7, 0, tzinfo=dt.UTC),
                ),
                self._signal_row(
                    local_date=local_date,
                    signal_type="resting_hr",
                    value=49.0,
                    measured_at=dt.datetime(2026, 3, 5, 7, 5, tzinfo=dt.UTC),
                ),
            ],
            activity_rows=[self._activity_row(local_date=local_date)],
            load_context_by_date={
                local_date: DailyLoadContext(
                    local_date=local_date,
                    load_present=True,
                    has_estimated_inputs=False,
                )
            },
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].completeness_status, "complete")
        self.assertEqual(rows[0].inputs_present, ["sleep", "hrv", "rhr", "activity", "load"])

    def test_partial_emits_when_only_sleep_exists(self) -> None:
        local_date = dt.date(2026, 3, 5)
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates=[local_date],
            sleep_rows=[self._sleep_row(local_date=local_date)],
            signal_rows=[],
            activity_rows=[],
            load_context_by_date={},
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].completeness_status, "partial")
        self.assertIn("sleep", rows[0].inputs_present)
        self.assertIn("hrv", rows[0].inputs_missing)
        self.assertIn("rhr", rows[0].inputs_missing)

    def test_missing_emits_no_row_when_only_activity_and_load_exist(self) -> None:
        local_date = dt.date(2026, 3, 5)
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates=[local_date],
            sleep_rows=[],
            signal_rows=[],
            activity_rows=[self._activity_row(local_date=local_date)],
            load_context_by_date={
                local_date: DailyLoadContext(
                    local_date=local_date,
                    load_present=True,
                    has_estimated_inputs=True,
                )
            },
        )
        self.assertEqual(rows, [])

    def test_uses_last_signal_measurement_per_type(self) -> None:
        local_date = dt.date(2026, 3, 5)
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates=[local_date],
            sleep_rows=[],
            signal_rows=[
                self._signal_row(
                    local_date=local_date,
                    signal_type="hrv_sdnn",
                    value=42.0,
                    measured_at=dt.datetime(2026, 3, 5, 7, 0, tzinfo=dt.UTC),
                ),
                self._signal_row(
                    local_date=local_date,
                    signal_type="hrv_sdnn",
                    value=47.0,
                    measured_at=dt.datetime(2026, 3, 5, 8, 0, tzinfo=dt.UTC),
                ),
                self._signal_row(
                    local_date=local_date,
                    signal_type="resting_hr",
                    value=51.0,
                    measured_at=dt.datetime(2026, 3, 5, 8, 5, tzinfo=dt.UTC),
                ),
            ],
            activity_rows=[],
            load_context_by_date={},
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].hrv_sdnn_ms, 47.0)
        self.assertEqual(rows[0].resting_hr_bpm, 51.0)

    def test_load_estimated_sets_flag_without_scoring(self) -> None:
        local_date = dt.date(2026, 3, 5)
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates=[local_date],
            sleep_rows=[self._sleep_row(local_date=local_date)],
            signal_rows=[],
            activity_rows=[],
            load_context_by_date={
                local_date: DailyLoadContext(
                    local_date=local_date,
                    load_present=True,
                    has_estimated_inputs=True,
                )
            },
        )
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].has_estimated_inputs)


if __name__ == "__main__":
    unittest.main()
