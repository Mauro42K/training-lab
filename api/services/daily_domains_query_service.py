import datetime as dt

from sqlalchemy.orm import Session

from api.repositories.body_measurements_repository import get_body_measurements_range
from api.repositories.daily_activity_repository import get_daily_activity_range
from api.repositories.daily_recovery_repository import get_daily_recovery_range
from api.repositories.daily_sleep_repository import get_daily_sleep_summary_range
from api.repositories.user_repository import get_or_create_default_user
from api.schemas.daily_domains import (
    BodyMeasurementsDomainItem,
    BodyMeasurementsDomainResponse,
    DailyActivityDomainItem,
    DailyActivityDomainResponse,
    DailyRecoveryDomainItem,
    DailyRecoveryDomainResponse,
    DailySleepDomainItem,
    DailySleepDomainResponse,
)
from api.services.body_measurements_canonicalizer import BodyMeasurementsCanonicalizer


class DailyDomainsQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_sleep(self, *, from_date: dt.date, to_date: dt.date) -> DailySleepDomainResponse:
        user = get_or_create_default_user(self.db)
        rows = get_daily_sleep_summary_range(
            self.db,
            user_id=user.id,
            from_date=from_date,
            to_date=to_date,
        )
        return DailySleepDomainResponse(
            items=[
                DailySleepDomainItem(
                    date=row.local_date,
                    total_sleep_sec=row.total_sleep_sec,
                    main_sleep_duration_sec=row.main_sleep_duration_sec,
                    naps_count=row.naps_count,
                    naps_total_sleep_sec=row.naps_total_sleep_sec,
                    completeness_status=row.completeness_status,
                    provider=row.provider,
                    source_count=row.source_count,
                    has_mixed_sources=row.has_mixed_sources,
                    primary_device_name=row.primary_device_name,
                )
                for row in rows
            ]
        )

    def get_activity(self, *, from_date: dt.date, to_date: dt.date) -> DailyActivityDomainResponse:
        user = get_or_create_default_user(self.db)
        rows = get_daily_activity_range(
            self.db,
            user_id=user.id,
            from_date=from_date,
            to_date=to_date,
        )
        return DailyActivityDomainResponse(
            items=[
                DailyActivityDomainItem(
                    date=row.local_date,
                    steps=row.steps,
                    walking_running_distance_m=row.walking_running_distance_m,
                    active_energy_kcal=row.active_energy_kcal,
                    completeness_status=row.completeness_status,
                    provider=row.provider,
                    source_count=row.source_count,
                    has_mixed_sources=row.has_mixed_sources,
                    primary_device_name=row.primary_device_name,
                )
                for row in rows
            ]
        )

    def get_recovery(self, *, from_date: dt.date, to_date: dt.date) -> DailyRecoveryDomainResponse:
        user = get_or_create_default_user(self.db)
        rows = get_daily_recovery_range(
            self.db,
            user_id=user.id,
            from_date=from_date,
            to_date=to_date,
        )
        return DailyRecoveryDomainResponse(
            items=[
                DailyRecoveryDomainItem(
                    date=row.local_date,
                    sleep_total_sec=row.sleep_total_sec,
                    hrv_sdnn_ms=row.hrv_sdnn_ms,
                    resting_hr_bpm=row.resting_hr_bpm,
                    activity_present=row.activity_present,
                    load_present=row.load_present,
                    inputs_present=list(row.inputs_present),
                    inputs_missing=list(row.inputs_missing),
                    completeness_status=row.completeness_status,
                    has_estimated_inputs=row.has_estimated_inputs,
                    provider=row.provider,
                    source_count=row.source_count,
                    has_mixed_sources=row.has_mixed_sources,
                    primary_device_name=row.primary_device_name,
                )
                for row in rows
            ]
        )

    def get_body_measurements(
        self,
        *,
        from_date: dt.date,
        to_date: dt.date,
    ) -> BodyMeasurementsDomainResponse:
        user = get_or_create_default_user(self.db)
        measurements = get_body_measurements_range(
            self.db,
            user_id=user.id,
            from_date=from_date,
            to_date=to_date,
        )
        canonical_days = BodyMeasurementsCanonicalizer().build_days(measurements=measurements)
        return BodyMeasurementsDomainResponse(
            items=[
                BodyMeasurementsDomainItem(
                    date=day.local_date,
                    weight_kg=day.weight_kg,
                    body_fat_pct=day.body_fat_pct,
                    lean_body_mass_kg=day.lean_body_mass_kg,
                    provider=day.provider,
                    source_count=day.source_count,
                    has_mixed_sources=day.has_mixed_sources,
                    primary_device_name=day.primary_device_name,
                )
                for day in canonical_days
            ]
        )
