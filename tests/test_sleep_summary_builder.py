import datetime as dt
import unittest
import uuid
from types import SimpleNamespace

from api.services.sleep_summary_builder import SleepSummaryBuilder


class SleepSummaryBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SleepSummaryBuilder()
        self.user_id = uuid.uuid4()

    def _session(
        self,
        *,
        start_at: dt.datetime,
        end_at: dt.datetime,
        source_bundle_id: str | None = "com.apple.health",
        source_count: int = 1,
        has_mixed_sources: bool = False,
        primary_device_name: str | None = "Apple Watch",
    ) -> SimpleNamespace:
        return SimpleNamespace(
            start_at=start_at,
            end_at=end_at,
            source_bundle_id=source_bundle_id,
            source_count=source_count,
            has_mixed_sources=has_mixed_sources,
            primary_device_name=primary_device_name,
        )

    def test_builds_complete_summary_for_overnight_sleep(self) -> None:
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates={dt.date(2026, 3, 2)},
            sleep_sessions=[
                self._session(
                    start_at=dt.datetime(2026, 3, 2, 4, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.UTC),
                )
            ],
            user_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].local_date, dt.date(2026, 3, 2))
        self.assertEqual(rows[0].completeness_status, "complete")
        self.assertEqual(rows[0].main_sleep_duration_sec, 8 * 3600)

    def test_merges_multiple_nocturnal_blocks(self) -> None:
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates={dt.date(2026, 3, 2)},
            sleep_sessions=[
                self._session(
                    start_at=dt.datetime(2026, 3, 2, 4, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 7, 0, tzinfo=dt.UTC),
                ),
                self._session(
                    start_at=dt.datetime(2026, 3, 2, 7, 20, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 10, 0, tzinfo=dt.UTC),
                ),
            ],
            user_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].main_sleep_duration_sec, int(6 * 3600))

    def test_builds_nap_count(self) -> None:
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates={dt.date(2026, 3, 2)},
            sleep_sessions=[
                self._session(
                    start_at=dt.datetime(2026, 3, 2, 4, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.UTC),
                ),
                self._session(
                    start_at=dt.datetime(2026, 3, 2, 18, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 18, 45, tzinfo=dt.UTC),
                ),
            ],
            user_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(rows[0].naps_count, 1)
        self.assertEqual(rows[0].naps_total_sleep_sec, 45 * 60)

    def test_fallback_main_sleep_is_partial(self) -> None:
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates={dt.date(2026, 3, 2)},
            sleep_sessions=[
                self._session(
                    start_at=dt.datetime(2026, 3, 2, 9, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 11, 0, tzinfo=dt.UTC),
                )
            ],
            user_timezone="UTC",
            fallback_timezone="UTC",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].completeness_status, "partial")

    def test_no_summary_without_qualifying_main_sleep(self) -> None:
        rows = self.builder.build_rows_for_dates(
            user_id=self.user_id,
            dates={dt.date(2026, 3, 2)},
            sleep_sessions=[
                self._session(
                    start_at=dt.datetime(2026, 3, 2, 17, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 17, 30, tzinfo=dt.UTC),
                )
            ],
            user_timezone="UTC",
            fallback_timezone="UTC",
        )
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
