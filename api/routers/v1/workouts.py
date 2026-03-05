import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.schemas.workouts import WorkoutsResponse
from api.services.workouts_service import WorkoutsService

SportType = Literal["run", "bike", "strength", "walk", "other"]

router = APIRouter()


@router.get("/workouts", response_model=WorkoutsResponse)
def list_workouts(
    db: Session = Depends(get_db),
    from_dt: dt.datetime = Query(..., alias="from"),
    to_dt: dt.datetime = Query(..., alias="to"),
    sport: SportType | None = Query(default=None),
) -> WorkoutsResponse:
    if from_dt > to_dt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="from must be less than or equal to to",
        )
    service = WorkoutsService(db)
    return service.list_workouts(from_dt=from_dt, to_dt=to_dt, sport=sport)
