import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.schemas.daily_domains import (
    BodyMeasurementsDomainResponse,
    DailyActivityDomainResponse,
    DailyRecoveryDomainResponse,
    DailySleepDomainResponse,
    HomeSummaryResponse,
)
from api.services.daily_domains_query_service import DailyDomainsQueryService
from api.services.home_summary_service import HomeSummaryService

router = APIRouter()


def _validate_date_range(*, from_date: dt.date, to_date: dt.date) -> None:
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="from must be less than or equal to to",
        )


@router.get("/daily-domains/sleep", response_model=DailySleepDomainResponse)
def get_daily_sleep(
    db: Session = Depends(get_db),
    from_date: dt.date = Query(..., alias="from"),
    to_date: dt.date = Query(..., alias="to"),
) -> DailySleepDomainResponse:
    _validate_date_range(from_date=from_date, to_date=to_date)
    return DailyDomainsQueryService(db).get_sleep(from_date=from_date, to_date=to_date)


@router.get("/daily-domains/activity", response_model=DailyActivityDomainResponse)
def get_daily_activity(
    db: Session = Depends(get_db),
    from_date: dt.date = Query(..., alias="from"),
    to_date: dt.date = Query(..., alias="to"),
) -> DailyActivityDomainResponse:
    _validate_date_range(from_date=from_date, to_date=to_date)
    return DailyDomainsQueryService(db).get_activity(from_date=from_date, to_date=to_date)


@router.get("/daily-domains/recovery", response_model=DailyRecoveryDomainResponse)
def get_daily_recovery(
    db: Session = Depends(get_db),
    from_date: dt.date = Query(..., alias="from"),
    to_date: dt.date = Query(..., alias="to"),
) -> DailyRecoveryDomainResponse:
    _validate_date_range(from_date=from_date, to_date=to_date)
    return DailyDomainsQueryService(db).get_recovery(from_date=from_date, to_date=to_date)


@router.get("/daily-domains/body-measurements", response_model=BodyMeasurementsDomainResponse)
def get_body_measurements(
    db: Session = Depends(get_db),
    from_date: dt.date = Query(..., alias="from"),
    to_date: dt.date = Query(..., alias="to"),
) -> BodyMeasurementsDomainResponse:
    _validate_date_range(from_date=from_date, to_date=to_date)
    return DailyDomainsQueryService(db).get_body_measurements(from_date=from_date, to_date=to_date)


@router.get("/home/summary", response_model=HomeSummaryResponse)
def get_home_summary(
    db: Session = Depends(get_db),
    date: dt.date = Query(...),
) -> HomeSummaryResponse:
    return HomeSummaryService(db).get_summary(target_date=date)
