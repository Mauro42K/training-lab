import datetime as dt

from sqlalchemy.orm import Session

from api.repositories.body_measurements_repository import get_body_measurements_for_dates
from api.repositories.daily_activity_repository import get_daily_activity_by_date
from api.repositories.daily_recovery_repository import get_daily_recovery_by_date
from api.repositories.daily_sleep_repository import get_daily_sleep_summary_by_date
from api.repositories.user_repository import get_or_create_default_user
from api.schemas.daily_domains import (
    BodyMeasurementsDomainItem,
    DailyActivityDomainItem,
    DailyRecoveryDomainItem,
    DailySleepDomainItem,
    HomeSummaryResponse,
)
from api.services.body_measurements_canonicalizer import BodyMeasurementsCanonicalizer


class HomeSummaryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self, *, target_date: dt.date) -> HomeSummaryResponse:
        user = get_or_create_default_user(self.db)
        sleep_row = get_daily_sleep_summary_by_date(
            self.db,
            user_id=user.id,
            target_date=target_date,
        )
        activity_row = get_daily_activity_by_date(
            self.db,
            user_id=user.id,
            target_date=target_date,
        )
        recovery_row = get_daily_recovery_by_date(
            self.db,
            user_id=user.id,
            target_date=target_date,
        )
        body_days = BodyMeasurementsCanonicalizer().build_days(
            measurements=get_body_measurements_for_dates(
                self.db,
                user_id=user.id,
                dates=[target_date],
            )
        )
        body_day = body_days[0] if body_days else None

        return HomeSummaryResponse(
            date=target_date,
            sleep=(
                DailySleepDomainItem(
                    date=sleep_row.local_date,
                    total_sleep_sec=sleep_row.total_sleep_sec,
                    main_sleep_duration_sec=sleep_row.main_sleep_duration_sec,
                    naps_count=sleep_row.naps_count,
                    naps_total_sleep_sec=sleep_row.naps_total_sleep_sec,
                    completeness_status=sleep_row.completeness_status,
                    provider=sleep_row.provider,
                    source_count=sleep_row.source_count,
                    has_mixed_sources=sleep_row.has_mixed_sources,
                    primary_device_name=sleep_row.primary_device_name,
                )
                if sleep_row is not None
                else None
            ),
            activity=(
                DailyActivityDomainItem(
                    date=activity_row.local_date,
                    steps=activity_row.steps,
                    walking_running_distance_m=activity_row.walking_running_distance_m,
                    active_energy_kcal=activity_row.active_energy_kcal,
                    completeness_status=activity_row.completeness_status,
                    provider=activity_row.provider,
                    source_count=activity_row.source_count,
                    has_mixed_sources=activity_row.has_mixed_sources,
                    primary_device_name=activity_row.primary_device_name,
                )
                if activity_row is not None
                else None
            ),
            recovery=(
                DailyRecoveryDomainItem(
                    date=recovery_row.local_date,
                    sleep_total_sec=recovery_row.sleep_total_sec,
                    hrv_sdnn_ms=recovery_row.hrv_sdnn_ms,
                    resting_hr_bpm=recovery_row.resting_hr_bpm,
                    activity_present=recovery_row.activity_present,
                    load_present=recovery_row.load_present,
                    inputs_present=list(recovery_row.inputs_present),
                    inputs_missing=list(recovery_row.inputs_missing),
                    completeness_status=recovery_row.completeness_status,
                    has_estimated_inputs=recovery_row.has_estimated_inputs,
                    provider=recovery_row.provider,
                    source_count=recovery_row.source_count,
                    has_mixed_sources=recovery_row.has_mixed_sources,
                    primary_device_name=recovery_row.primary_device_name,
                )
                if recovery_row is not None
                else None
            ),
            body_measurements=(
                BodyMeasurementsDomainItem(
                    date=body_day.local_date,
                    weight_kg=body_day.weight_kg,
                    body_fat_pct=body_day.body_fat_pct,
                    lean_body_mass_kg=body_day.lean_body_mass_kg,
                    provider=body_day.provider,
                    source_count=body_day.source_count,
                    has_mixed_sources=body_day.has_mixed_sources,
                    primary_device_name=body_day.primary_device_name,
                )
                if body_day is not None
                else None
            ),
        )
