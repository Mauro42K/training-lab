from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from api.repositories.daily_domains_repository import (
    BodyMeasurementSnapshot,
    RecoverySignalSnapshot,
    SleepSessionSnapshot,
    delete_daily_activity_rows_for_dates,
    delete_daily_recovery_rows_for_dates,
    delete_daily_sleep_summary_rows_for_dates,
)
from api.services.daily_domain_rules import merge_affected_dates


@dataclass(frozen=True)
class DailyDomainRecomputeSummary:
    deleted_daily_sleep_summary_rows: int
    deleted_daily_activity_rows: int
    deleted_daily_recovery_rows: int
    affected_dates: int


class DailyDomainRecomputeService:
    def collect_sleep_affected_dates(
        self,
        *,
        pre_snapshots: dict[UUID, SleepSessionSnapshot],
        post_snapshots: dict[UUID, SleepSessionSnapshot],
    ) -> set[date]:
        return merge_affected_dates(
            (snapshot.local_date for snapshot in pre_snapshots.values()),
            (snapshot.local_date for snapshot in post_snapshots.values()),
        )

    def collect_recovery_signal_affected_dates(
        self,
        *,
        pre_snapshots: dict[UUID, RecoverySignalSnapshot],
        post_snapshots: dict[UUID, RecoverySignalSnapshot],
    ) -> set[date]:
        return merge_affected_dates(
            (snapshot.local_date for snapshot in pre_snapshots.values()),
            (snapshot.local_date for snapshot in post_snapshots.values()),
        )

    def collect_body_measurement_affected_dates(
        self,
        *,
        pre_snapshots: dict[UUID, BodyMeasurementSnapshot],
        post_snapshots: dict[UUID, BodyMeasurementSnapshot],
    ) -> set[date]:
        return merge_affected_dates(
            (snapshot.local_date for snapshot in pre_snapshots.values()),
            (snapshot.local_date for snapshot in post_snapshots.values()),
        )

    def reset_daily_rows_for_dates(
        self,
        db: Session,
        *,
        user_id: UUID,
        dates: Sequence[date],
        include_sleep: bool = True,
        include_activity: bool = True,
        include_recovery: bool = True,
    ) -> DailyDomainRecomputeSummary:
        unique_dates = sorted(set(dates))
        deleted_sleep = 0
        deleted_activity = 0
        deleted_recovery = 0

        if include_sleep:
            deleted_sleep = delete_daily_sleep_summary_rows_for_dates(
                db,
                user_id=user_id,
                dates=unique_dates,
            )
        if include_activity:
            deleted_activity = delete_daily_activity_rows_for_dates(
                db,
                user_id=user_id,
                dates=unique_dates,
            )
        if include_recovery:
            deleted_recovery = delete_daily_recovery_rows_for_dates(
                db,
                user_id=user_id,
                dates=unique_dates,
            )

        return DailyDomainRecomputeSummary(
            deleted_daily_sleep_summary_rows=deleted_sleep,
            deleted_daily_activity_rows=deleted_activity,
            deleted_daily_recovery_rows=deleted_recovery,
            affected_dates=len(unique_dates),
        )
