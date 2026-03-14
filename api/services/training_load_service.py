import datetime as dt
from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.core.config import Settings, get_settings
from api.repositories.load_repository import get_daily_load_rows, get_first_daily_load_date
from api.repositories.user_repository import get_or_create_default_user
from api.schemas.training_load import (
    TrainingLoadHistoryStatus,
    TrainingLoadItem,
    TrainingLoadResponse,
    TrainingLoadSemanticState,
    TrainingLoadSportFilter,
)
from api.services.local_date import resolve_local_date

FITNESS_WINDOW_DAYS = 42
FATIGUE_WINDOW_DAYS = 7
HISTORY_PARTIAL_DAYS = 14


@dataclass(frozen=True)
class LoadCapacitySemanticThresholds:
    below_capacity_upper_bound: float = 0.85
    within_range_upper_bound: float = 1.0
    near_limit_upper_bound: float = 1.15


LOAD_CAPACITY_THRESHOLDS = LoadCapacitySemanticThresholds()


@dataclass(frozen=True)
class TrainingLoadSnapshot:
    items: list[TrainingLoadItem]
    history_status: TrainingLoadHistoryStatus
    semantic_state: TrainingLoadSemanticState | None
    latest_load: float
    latest_capacity: float
    latest_fatigue: float


class TrainingLoadService:
    def __init__(self, db: Session, *, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def get_training_load(
        self,
        *,
        days: int,
        sport: TrainingLoadSportFilter,
        today_local: dt.date | None = None,
    ) -> TrainingLoadResponse:
        snapshot = self.get_training_load_snapshot(
            days=days,
            sport=sport,
            today_local=today_local,
        )
        return TrainingLoadResponse(
            items=snapshot.items,
            history_status=snapshot.history_status,
            semantic_state=snapshot.semantic_state,
            latest_load=snapshot.latest_load,
            latest_capacity=snapshot.latest_capacity,
        )

    def get_training_load_snapshot(
        self,
        *,
        days: int,
        sport: TrainingLoadSportFilter,
        today_local: dt.date | None = None,
    ) -> TrainingLoadSnapshot:
        user = get_or_create_default_user(self.db)
        if today_local is None:
            now_utc = dt.datetime.now(dt.UTC)
            today_local = resolve_local_date(
                instant=now_utc,
                user_timezone=user.timezone,
                fallback_timezone=self.settings.trimp_timezone_fallback,
            )

        from_date = today_local - dt.timedelta(days=days - 1)
        calculation_from_date = from_date - dt.timedelta(days=FITNESS_WINDOW_DAYS - 1)
        rows = get_daily_load_rows(
            self.db,
            user_id=user.id,
            from_date=calculation_from_date,
            to_date=today_local,
            sport_filter=sport,
            trimp_model_version=self.settings.trimp_active_model_version,
        )
        first_useful_date = get_first_daily_load_date(
            self.db,
            user_id=user.id,
            sport_filter=sport,
            trimp_model_version=self.settings.trimp_active_model_version,
        )

        history_status = self._resolve_history_status(
            today_local=today_local,
            first_useful_date=first_useful_date,
        )
        by_date = {row_date: trimp for row_date, trimp in rows}
        calculation_dates = [
            calculation_from_date + dt.timedelta(days=offset)
            for offset in range((today_local - calculation_from_date).days + 1)
        ]
        load_series = [by_date.get(current_date, 0.0) for current_date in calculation_dates]
        capacity_series = self._calculate_ema_series(load_series, window_days=FITNESS_WINDOW_DAYS)
        fatigue_series = self._calculate_ema_series(load_series, window_days=FATIGUE_WINDOW_DAYS)

        series_by_date = {
            current_date: {
                "load": load,
                "capacity": capacity,
                "fatigue": fatigue,
            }
            for current_date, load, capacity, fatigue in zip(
                calculation_dates,
                load_series,
                capacity_series,
                fatigue_series,
                strict=True,
            )
        }
        items = [
            TrainingLoadItem(
                date=current_date,
                load=series_by_date[current_date]["load"],
                capacity=series_by_date[current_date]["capacity"],
                trimp=series_by_date[current_date]["load"],
            )
            for current_date in (from_date + dt.timedelta(days=offset) for offset in range(days))
        ]
        latest_day = series_by_date[today_local]

        return TrainingLoadSnapshot(
            items=items,
            history_status=history_status,
            semantic_state=self._resolve_semantic_state(
                fatigue=latest_day["fatigue"],
                capacity=latest_day["capacity"],
                history_status=history_status,
            ),
            latest_load=latest_day["load"],
            latest_capacity=latest_day["capacity"],
            latest_fatigue=latest_day["fatigue"],
        )

    def _resolve_history_status(
        self,
        *,
        today_local: dt.date,
        first_useful_date: dt.date | None,
    ) -> TrainingLoadHistoryStatus:
        if first_useful_date is None:
            return "missing"

        history_days = max((today_local - first_useful_date).days + 1, 0)
        if history_days >= FITNESS_WINDOW_DAYS:
            return "available"
        if history_days >= HISTORY_PARTIAL_DAYS:
            return "partial"
        return "insufficient_history"

    def _resolve_semantic_state(
        self,
        *,
        fatigue: float,
        capacity: float,
        history_status: TrainingLoadHistoryStatus,
    ) -> TrainingLoadSemanticState | None:
        if history_status in {"missing", "insufficient_history"} or capacity <= 0:
            return None

        ratio = fatigue / capacity
        if ratio < LOAD_CAPACITY_THRESHOLDS.below_capacity_upper_bound:
            return "below_capacity"
        if ratio <= LOAD_CAPACITY_THRESHOLDS.within_range_upper_bound:
            return "within_range"
        if ratio <= LOAD_CAPACITY_THRESHOLDS.near_limit_upper_bound:
            return "near_limit"
        return "above_capacity"

    def _calculate_ema_series(self, values: list[float], *, window_days: int) -> list[float]:
        if not values:
            return []

        alpha = 2 / (window_days + 1)
        ema_series: list[float] = []
        current_ema = 0.0
        for value in values:
            current_ema = current_ema + alpha * (value - current_ema)
            ema_series.append(current_ema)
        return ema_series
