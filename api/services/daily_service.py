import datetime as dt

from sqlalchemy.orm import Session

from api.repositories.user_repository import get_or_create_default_user
from api.repositories.workouts_repository import get_daily_aggregates
from api.schemas.daily import DailyItem, DailyResponse


class DailyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_daily(self, *, from_date: dt.date, to_date: dt.date) -> DailyResponse:
        user = get_or_create_default_user(self.db)
        rows = get_daily_aggregates(
            self.db,
            user_id=user.id,
            from_date=from_date,
            to_date=to_date,
        )
        items = [DailyItem(**row) for row in rows]
        return DailyResponse(items=items)
