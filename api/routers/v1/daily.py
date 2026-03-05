import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.schemas.daily import DailyResponse
from api.services.daily_service import DailyService

router = APIRouter()


@router.get("/daily", response_model=DailyResponse)
def get_daily(
    db: Session = Depends(get_db),
    from_date: dt.date = Query(..., alias="from"),
    to_date: dt.date = Query(..., alias="to"),
) -> DailyResponse:
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="from must be less than or equal to to",
        )
    service = DailyService(db)
    return service.get_daily(from_date=from_date, to_date=to_date)
