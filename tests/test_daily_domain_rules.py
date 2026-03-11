import datetime as dt
import unittest
import uuid

from api.repositories.daily_domains_repository import (
    BodyMeasurementSnapshot,
    RecoverySignalSnapshot,
    SleepSessionSnapshot,
)
from api.services.daily_domain_recompute_service import DailyDomainRecomputeService
from api.services.daily_domain_rules import (
    resolve_daily_activity_completeness,
    resolve_daily_recovery_completeness,
    resolve_primary_device_name,
)


class DailyDomainRulesTests(unittest.TestCase):
    def test_primary_device_name_requires_single_confident_value(self) -> None:
        self.assertEqual(resolve_primary_device_name(["Apple Watch"]), "Apple Watch")
        self.assertIsNone(resolve_primary_device_name(["Apple Watch", "iPhone"]))
        self.assertIsNone(resolve_primary_device_name([None, ""]))

    def test_daily_recovery_completeness(self) -> None:
        self.assertEqual(
            resolve_daily_recovery_completeness(has_sleep=True, has_hrv=True, has_rhr=True),
            "complete",
        )
        self.assertEqual(
            resolve_daily_recovery_completeness(has_sleep=True, has_hrv=False, has_rhr=False),
            "partial",
        )
        self.assertIsNone(
            resolve_daily_recovery_completeness(has_sleep=False, has_hrv=False, has_rhr=False)
        )

    def test_daily_activity_completeness(self) -> None:
        self.assertEqual(
            resolve_daily_activity_completeness(
                steps=8000,
                walking_running_distance_m=5400.0,
                active_energy_kcal=None,
            ),
            "complete",
        )
        self.assertEqual(
            resolve_daily_activity_completeness(
                steps=8000,
                walking_running_distance_m=None,
                active_energy_kcal=None,
            ),
            "partial",
        )
        self.assertEqual(
            resolve_daily_activity_completeness(
                steps=None,
                walking_running_distance_m=None,
                active_energy_kcal=450.0,
            ),
            "partial",
        )
        self.assertIsNone(
            resolve_daily_activity_completeness(
                steps=None,
                walking_running_distance_m=None,
                active_energy_kcal=None,
            )
        )

    def test_recompute_service_collects_affected_dates(self) -> None:
        service = DailyDomainRecomputeService()
        sleep_uuid = uuid.uuid4()
        signal_uuid = uuid.uuid4()
        measurement_uuid = uuid.uuid4()

        sleep_dates = service.collect_sleep_affected_dates(
            pre_snapshots={
                sleep_uuid: SleepSessionSnapshot(
                    row_id=1,
                    healthkit_sleep_uuid=sleep_uuid,
                    local_date=dt.date(2026, 3, 1),
                    start_at=dt.datetime(2026, 3, 1, 23, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 7, 0, tzinfo=dt.UTC),
                )
            },
            post_snapshots={
                sleep_uuid: SleepSessionSnapshot(
                    row_id=1,
                    healthkit_sleep_uuid=sleep_uuid,
                    local_date=dt.date(2026, 3, 2),
                    start_at=dt.datetime(2026, 3, 2, 0, 0, tzinfo=dt.UTC),
                    end_at=dt.datetime(2026, 3, 2, 8, 0, tzinfo=dt.UTC),
                )
            },
        )
        self.assertEqual(sleep_dates, {dt.date(2026, 3, 1), dt.date(2026, 3, 2)})

        signal_dates = service.collect_recovery_signal_affected_dates(
            pre_snapshots={
                signal_uuid: RecoverySignalSnapshot(
                    row_id=2,
                    healthkit_signal_uuid=signal_uuid,
                    signal_type="hrv_sdnn",
                    local_date=dt.date(2026, 3, 2),
                    measured_at=dt.datetime(2026, 3, 2, 9, 0, tzinfo=dt.UTC),
                    signal_value=42.0,
                )
            },
            post_snapshots={},
        )
        self.assertEqual(signal_dates, {dt.date(2026, 3, 2)})

        body_dates = service.collect_body_measurement_affected_dates(
            pre_snapshots={},
            post_snapshots={
                measurement_uuid: BodyMeasurementSnapshot(
                    row_id=3,
                    healthkit_measurement_uuid=measurement_uuid,
                    measurement_type="weight_kg",
                    local_date=dt.date(2026, 3, 3),
                    measured_at=dt.datetime(2026, 3, 3, 7, 0, tzinfo=dt.UTC),
                    measurement_value=70.2,
                )
            },
        )
        self.assertEqual(body_dates, {dt.date(2026, 3, 3)})


if __name__ == "__main__":
    unittest.main()
