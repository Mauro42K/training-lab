from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.schemas.ingest import (
    BodyMeasurementsIngestRequest,
    DailyActivityIngestRequest,
    IngestBodyMeasurementsResponse,
    IngestDailyActivityResponse,
    IngestRecoverySignalsResponse,
    IngestSleepSessionsResponse,
    IngestWorkoutsResponse,
    RecoverySignalsIngestRequest,
    SleepSessionsIngestRequest,
    WorkoutsIngestRequest,
)
from api.services.body_measurements_ingest_service import BodyMeasurementsIngestService
from api.services.daily_activity_ingest_service import DailyActivityIngestService
from api.services.ingest_service import (
    IdempotencyConflictError,
    IngestService,
    PayloadLimitExceededError,
)
from api.services.recovery_signals_ingest_service import RecoverySignalsIngestService
from api.services.sleep_ingest_service import SleepIngestService

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


@router.post("/ingest/sleep", response_model=IngestSleepSessionsResponse)
def ingest_sleep_sessions(
    payload: SleepSessionsIngestRequest,
    db: Session = Depends(get_db),
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key", max_length=255),
) -> IngestSleepSessionsResponse:
    service = SleepIngestService(db)
    try:
        return service.ingest_sleep_sessions(payload=payload, idempotency_key=x_idempotency_key)
    except IdempotencyConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PayloadLimitExceededError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/ingest/daily-activity", response_model=IngestDailyActivityResponse)
def ingest_daily_activity(
    payload: DailyActivityIngestRequest,
    db: Session = Depends(get_db),
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key", max_length=255),
) -> IngestDailyActivityResponse:
    service = DailyActivityIngestService(db)
    try:
        return service.ingest_daily_activity(payload=payload, idempotency_key=x_idempotency_key)
    except IdempotencyConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PayloadLimitExceededError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/ingest/body-measurements", response_model=IngestBodyMeasurementsResponse)
def ingest_body_measurements(
    payload: BodyMeasurementsIngestRequest,
    db: Session = Depends(get_db),
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key", max_length=255),
) -> IngestBodyMeasurementsResponse:
    service = BodyMeasurementsIngestService(db)
    try:
        return service.ingest_body_measurements(payload=payload, idempotency_key=x_idempotency_key)
    except IdempotencyConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PayloadLimitExceededError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/ingest/recovery-signals", response_model=IngestRecoverySignalsResponse)
def ingest_recovery_signals(
    payload: RecoverySignalsIngestRequest,
    db: Session = Depends(get_db),
    x_idempotency_key: str = Header(..., alias="X-Idempotency-Key", max_length=255),
) -> IngestRecoverySignalsResponse:
    service = RecoverySignalsIngestService(db)
    try:
        return service.ingest_recovery_signals(payload=payload, idempotency_key=x_idempotency_key)
    except IdempotencyConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PayloadLimitExceededError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
