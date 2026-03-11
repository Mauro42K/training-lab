from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from api.core.config import Settings, get_settings
from api.repositories.daily_domains_repository import (
    DailySleepSummaryUpsert,
    SleepSessionSnapshot,
    get_sleep_session_snapshots_by_uuids,
    get_sleep_session_snapshots_for_summary_dates,
    upsert_daily_sleep_summary_rows,
)
from api.services.daily_domain_recompute_service import DailyDomainRecomputeService
from api.services.daily_recovery_recompute_service import DailyRecoveryRecomputeService
from api.services.sleep_summary_builder import SleepSummaryBuilder


@dataclass(frozen=True)
class SleepRecomputeSummary:
    rebuilt_daily_sleep_summary_rows: int
    invalidated_daily_recovery_dates: int
    rebuilt_dates: int


class SleepRecomputeService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        daily_recompute_service: DailyDomainRecomputeService | None = None,
        summary_builder: SleepSummaryBuilder | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.daily_recompute_service = daily_recompute_service or DailyDomainRecomputeService()
        self.summary_builder = summary_builder or SleepSummaryBuilder()
        self.daily_recovery_recompute_service = DailyRecoveryRecomputeService(settings=self.settings)

    def recompute_for_sleep_uuids(
        self,
        db: Session,
        *,
        user_id: UUID,
        user_timezone: str | None,
        sleep_uuids: Sequence[UUID],
        pre_snapshots: dict[UUID, SleepSessionSnapshot],
    ) -> SleepRecomputeSummary:
        if not sleep_uuids:
            return SleepRecomputeSummary(
                rebuilt_daily_sleep_summary_rows=0,
                invalidated_daily_recovery_dates=0,
                rebuilt_dates=0,
            )

        post_snapshots = get_sleep_session_snapshots_by_uuids(
            db,
            user_id=user_id,
            sleep_uuids=sleep_uuids,
        )
        affected_dates = self.daily_recompute_service.collect_sleep_affected_dates(
            pre_snapshots=pre_snapshots,
            post_snapshots=post_snapshots,
        )
        reset_summary = self.daily_recompute_service.reset_daily_rows_for_dates(
            db,
            user_id=user_id,
            dates=sorted(affected_dates),
            include_sleep=True,
            include_activity=False,
            include_recovery=True,
        )
        sleep_sessions = get_sleep_session_snapshots_for_summary_dates(
            db,
            user_id=user_id,
            dates=sorted(affected_dates),
        )
        summary_rows: list[DailySleepSummaryUpsert] = self.summary_builder.build_rows_for_dates(
            user_id=user_id,
            dates=affected_dates,
            sleep_sessions=sleep_sessions,
            user_timezone=user_timezone,
            fallback_timezone=self.settings.trimp_timezone_fallback,
        )
        upsert_daily_sleep_summary_rows(db, rows=summary_rows)
        self.daily_recovery_recompute_service.recompute_for_dates(
            db,
            user_id=user_id,
            dates=sorted(affected_dates),
        )
        return SleepRecomputeSummary(
            rebuilt_daily_sleep_summary_rows=len(summary_rows),
            invalidated_daily_recovery_dates=reset_summary.deleted_daily_recovery_rows,
            rebuilt_dates=len(affected_dates),
        )
