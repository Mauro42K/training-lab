import datetime as dt
import unittest
from types import SimpleNamespace

from api.services.body_measurements_canonicalizer import BodyMeasurementsCanonicalizer


class BodyMeasurementsCanonicalizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.canonicalizer = BodyMeasurementsCanonicalizer()

    def _measurement(
        self,
        *,
        local_date: dt.date,
        measurement_type: str,
        measured_at: dt.datetime,
        measurement_value: float,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            local_date=local_date,
            measurement_type=measurement_type,
            measured_at=measured_at,
            measurement_value=measurement_value,
        )

    def test_uses_latest_valid_measurement_per_type(self) -> None:
        rows = self.canonicalizer.build_days(
            measurements=[
                self._measurement(
                    local_date=dt.date(2026, 3, 4),
                    measurement_type="weight_kg",
                    measured_at=dt.datetime(2026, 3, 4, 7, 0, tzinfo=dt.UTC),
                    measurement_value=71.0,
                ),
                self._measurement(
                    local_date=dt.date(2026, 3, 4),
                    measurement_type="weight_kg",
                    measured_at=dt.datetime(2026, 3, 4, 9, 0, tzinfo=dt.UTC),
                    measurement_value=70.6,
                ),
                self._measurement(
                    local_date=dt.date(2026, 3, 4),
                    measurement_type="body_fat_pct",
                    measured_at=dt.datetime(2026, 3, 4, 9, 5, tzinfo=dt.UTC),
                    measurement_value=18.1,
                ),
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].weight_kg, 70.6)
        self.assertEqual(rows[0].body_fat_pct, 18.1)

    def test_day_without_weight_is_not_emitted(self) -> None:
        rows = self.canonicalizer.build_days(
            measurements=[
                self._measurement(
                    local_date=dt.date(2026, 3, 4),
                    measurement_type="body_fat_pct",
                    measured_at=dt.datetime(2026, 3, 4, 9, 5, tzinfo=dt.UTC),
                    measurement_value=18.1,
                )
            ]
        )
        self.assertEqual(rows, [])

    def test_partial_body_composition_remains_nullable(self) -> None:
        rows = self.canonicalizer.build_days(
            measurements=[
                self._measurement(
                    local_date=dt.date(2026, 3, 4),
                    measurement_type="weight_kg",
                    measured_at=dt.datetime(2026, 3, 4, 9, 0, tzinfo=dt.UTC),
                    measurement_value=70.6,
                )
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0].body_fat_pct)
        self.assertIsNone(rows[0].lean_body_mass_kg)


if __name__ == "__main__":
    unittest.main()
