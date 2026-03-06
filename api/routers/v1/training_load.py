from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.schemas.training_load import TrainingLoadResponse, TrainingLoadSportFilter
from api.services.training_load_service import TrainingLoadService

router = APIRouter()


@router.get("/training-load", response_model=TrainingLoadResponse)
def get_training_load(
    db: Session = Depends(get_db),
    days: int = Query(default=28, ge=1, le=90),
    sport: TrainingLoadSportFilter = Query(default="all"),
) -> TrainingLoadResponse:
    service = TrainingLoadService(db)
    return service.get_training_load(days=days, sport=sport)
