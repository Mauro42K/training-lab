from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from api.core.config import Settings, get_settings
from api.repositories.daily_activity_repository import get_daily_activity_rows_for_dates
from api.repositories.daily_recovery_repository import (
    get_daily_load_context_for_dates,
    get_recovery_signals_for_dates,
)
from api.repositories.daily_sleep_repository import get_daily_sleep_summary_rows_for_dates
from api.repositories.daily_domains_repository import (
    upsert_daily_recovery_rows,
)
from api.services.daily_domain_recompute_service import DailyDomainRecomputeService
from api.services.daily_recovery_builder import DailyRecoveryBuilder


@dataclass(frozen=True)
class DailyRecoveryRecomputeSummary:
    rebuilt_daily_recovery_rows: int
    rebuilt_dates: int


class DailyRecoveryRecomputeService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        daily_recompute_service: DailyDomainRecomputeService | None = None,
        builder: DailyRecoveryBuilder | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.daily_recompute_service = daily_recompute_service or DailyDomainRecomputeService()
        self.builder = builder or DailyRecoveryBuilder()

    def recompute_for_dates(
        self,
        db: Session,
        *,
        user_id: UUID,
        dates: Sequence[date],
    ) -> DailyRecoveryRecomputeSummary:
        unique_dates = sorted(set(dates))
        if not unique_dates:
            return DailyRecoveryRecomputeSummary(
                rebuilt_daily_recovery_rows=0,
                rebuilt_dates=0,
            )

        self.daily_recompute_service.reset_daily_rows_for_dates(
            db,
            user_id=user_id,
            dates=unique_dates,
            include_sleep=False,
            include_activity=False,
            include_recovery=True,
        )
        sleep_rows = get_daily_sleep_summary_rows_for_dates(
            db,
            user_id=user_id,
            dates=unique_dates,
        )
        signal_rows = get_recovery_signals_for_dates(
            db,
            user_id=user_id,
            dates=unique_dates,
        )
        activity_rows = get_daily_activity_rows_for_dates(
            db,
            user_id=user_id,
            dates=unique_dates,
        )
        load_context_by_date = get_daily_load_context_for_dates(
            db,
            user_id=user_id,
            dates=unique_dates,
            trimp_model_version=self.settings.trimp_active_model_version,
        )
        rows = self.builder.build_rows_for_dates(
            user_id=user_id,
            dates=unique_dates,
            sleep_rows=sleep_rows,
            signal_rows=signal_rows,
            activity_rows=activity_rows,
            load_context_by_date=load_context_by_date,
        )
        upsert_daily_recovery_rows(db, rows=rows)
        return DailyRecoveryRecomputeSummary(
            rebuilt_daily_recovery_rows=len(rows),
            rebuilt_dates=len(unique_dates),
        )
