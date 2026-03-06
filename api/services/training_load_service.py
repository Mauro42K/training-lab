import datetime as dt

from sqlalchemy.orm import Session

from api.core.config import Settings, get_settings
from api.repositories.load_repository import get_daily_load_rows
from api.repositories.user_repository import get_or_create_default_user
from api.schemas.training_load import TrainingLoadItem, TrainingLoadResponse, TrainingLoadSportFilter
from api.services.local_date import resolve_local_date


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
        user = get_or_create_default_user(self.db)
        if today_local is None:
            now_utc = dt.datetime.now(dt.UTC)
            today_local = resolve_local_date(
                instant=now_utc,
                user_timezone=user.timezone,
                fallback_timezone=self.settings.trimp_timezone_fallback,
            )

        from_date = today_local - dt.timedelta(days=days - 1)
        rows = get_daily_load_rows(
            self.db,
            user_id=user.id,
            from_date=from_date,
            to_date=today_local,
            sport_filter=sport,
            trimp_model_version=self.settings.trimp_active_model_version,
        )
        by_date = {row_date: trimp for row_date, trimp in rows}

        items = [
            TrainingLoadItem(
                date=current_date,
                trimp=by_date.get(current_date, 0.0),
            )
            for current_date in (
                from_date + dt.timedelta(days=offset) for offset in range(days)
            )
        ]
        return TrainingLoadResponse(items=items)
