import datetime as dt
import unittest

from api.services.local_date import (
    normalize_timezone_name,
    resolve_authoritative_timezone_name,
    resolve_local_date,
    resolve_measurement_local_date,
    resolve_sleep_session_local_date,
)


class LocalDateDailyDomainsTests(unittest.TestCase):
    def test_normalize_timezone_name_rejects_invalid(self) -> None:
        self.assertIsNone(normalize_timezone_name("Mars/Olympus"))

    def test_resolve_authoritative_timezone_prefers_request(self) -> None:
        resolved = resolve_authoritative_timezone_name(
            request_timezone="America/Mexico_City",
            stored_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(resolved, "America/Mexico_City")

    def test_resolve_authoritative_timezone_falls_back_to_stored(self) -> None:
        resolved = resolve_authoritative_timezone_name(
            request_timezone="Invalid/Zone",
            stored_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(resolved, "America/New_York")

    def test_sleep_session_local_date_uses_end_at(self) -> None:
        start_at = dt.datetime(2026, 3, 2, 4, 30, tzinfo=dt.UTC)
        end_at = dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.UTC)
        local_date = resolve_sleep_session_local_date(
            start_at=start_at,
            end_at=end_at,
            user_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(local_date, dt.date(2026, 3, 2))

    def test_measurement_local_date_uses_measurement_instant(self) -> None:
        measured_at = dt.datetime(2026, 3, 2, 2, 0, tzinfo=dt.UTC)
        local_date = resolve_measurement_local_date(
            measured_at=measured_at,
            user_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(local_date, dt.date(2026, 3, 1))

    def test_resolve_local_date_handles_naive_datetime(self) -> None:
        instant = dt.datetime(2026, 3, 2, 5, 0)
        local_date = resolve_local_date(
            instant=instant,
            user_timezone="America/New_York",
            fallback_timezone="UTC",
        )
        self.assertEqual(local_date, dt.date(2026, 3, 2))


if __name__ == "__main__":
    unittest.main()
