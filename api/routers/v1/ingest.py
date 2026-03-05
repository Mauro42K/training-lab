from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.schemas.ingest import IngestWorkoutsResponse, WorkoutsIngestRequest
from api.services.ingest_service import (
    IdempotencyConflictError,
    IngestService,
    PayloadLimitExceededError,
)

router = APIRouter()


@router.post("/ingest/workouts", response_model=IngestWorkoutsResponse)
def ingest_workouts(
    payload: WorkoutsIngestRequest,
    db: Session = Depends(get_db),
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key", max_length=255),
) -> IngestWorkoutsResponse:
    service = IngestService(db)
    try:
        return service.ingest_workouts(payload=payload, idempotency_key=x_idempotency_key)
    except IdempotencyConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PayloadLimitExceededError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
