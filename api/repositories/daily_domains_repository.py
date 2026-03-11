from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models import (
    BodyMeasurement,
    DailyActivity,
    DailyRecovery,
    DailySleepSummary,
    RecoverySignal,
    SleepSession,
)


@dataclass(frozen=True)
class SleepSessionSnapshot:
    row_id: int
    healthkit_sleep_uuid: UUID
    local_date: date
    start_at: datetime
    end_at: datetime


@dataclass(frozen=True)
class RecoverySignalSnapshot:
    row_id: int
    healthkit_signal_uuid: UUID
    signal_type: str
    local_date: date
    measured_at: datetime
    signal_value: float


@dataclass(frozen=True)
class BodyMeasurementSnapshot:
    row_id: int
    healthkit_measurement_uuid: UUID
    measurement_type: str
    local_date: date
    measured_at: datetime
    measurement_value: float


@dataclass(frozen=True)
class SleepSessionUpsert:
    healthkit_sleep_uuid: UUID
    user_id: UUID
    start_at: datetime
    end_at: datetime
    local_date: date
    category_value: str | None
    source_bundle_id: str | None
    provider: str
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None


@dataclass(frozen=True)
class RecoverySignalUpsert:
    healthkit_signal_uuid: UUID
    user_id: UUID
    signal_type: str
    measured_at: datetime
    local_date: date
    signal_value: float
    source_bundle_id: str | None
    provider: str
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None


@dataclass(frozen=True)
class BodyMeasurementUpsert:
    healthkit_measurement_uuid: UUID
    user_id: UUID
    measurement_type: str
    measured_at: datetime
    local_date: date
    measurement_value: float
    source_bundle_id: str | None
    provider: str
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None


@dataclass(frozen=True)
class DailySleepSummaryUpsert:
    user_id: UUID
    local_date: date
    total_sleep_sec: int
    main_sleep_start_at: datetime
    main_sleep_end_at: datetime
    main_sleep_duration_sec: int
    naps_count: int
    naps_total_sleep_sec: int
    completeness_status: str
    provider: str
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None


@dataclass(frozen=True)
class DailyActivityUpsert:
    user_id: UUID
    local_date: date
    steps: int | None
    walking_running_distance_m: float | None
    active_energy_kcal: float | None
    completeness_status: str
    provider: str
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None


@dataclass(frozen=True)
class DailyRecoveryUpsert:
    user_id: UUID
    local_date: date
    sleep_total_sec: int | None
    hrv_sdnn_ms: float | None
    resting_hr_bpm: float | None
    activity_present: bool
    load_present: bool
    inputs_present: list[str]
    inputs_missing: list[str]
    completeness_status: str
    has_estimated_inputs: bool
    provider: str
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None


def get_sleep_session_snapshots_by_uuids(
    db: Session,
    *,
    user_id: UUID,
    sleep_uuids: Sequence[UUID],
) -> dict[UUID, SleepSessionSnapshot]:
    if not sleep_uuids:
        return {}

    stmt = select(
        SleepSession.id,
        SleepSession.healthkit_sleep_uuid,
        SleepSession.local_date,
        SleepSession.start_at,
        SleepSession.end_at,
    ).where(
        SleepSession.user_id == user_id,
        SleepSession.healthkit_sleep_uuid.in_(list(sleep_uuids)),
    )
    rows = db.execute(stmt).all()
    return {
        row.healthkit_sleep_uuid: SleepSessionSnapshot(
            row_id=row.id,
            healthkit_sleep_uuid=row.healthkit_sleep_uuid,
            local_date=row.local_date,
            start_at=row.start_at,
            end_at=row.end_at,
        )
        for row in rows
    }


def get_recovery_signal_snapshots_by_uuids(
    db: Session,
    *,
    user_id: UUID,
    signal_uuids: Sequence[UUID],
) -> dict[UUID, RecoverySignalSnapshot]:
    if not signal_uuids:
        return {}

    stmt = select(
        RecoverySignal.id,
        RecoverySignal.healthkit_signal_uuid,
        RecoverySignal.signal_type,
        RecoverySignal.local_date,
        RecoverySignal.measured_at,
        RecoverySignal.signal_value,
    ).where(
        RecoverySignal.user_id == user_id,
        RecoverySignal.healthkit_signal_uuid.in_(list(signal_uuids)),
    )
    rows = db.execute(stmt).all()
    return {
        row.healthkit_signal_uuid: RecoverySignalSnapshot(
            row_id=row.id,
            healthkit_signal_uuid=row.healthkit_signal_uuid,
            signal_type=row.signal_type,
            local_date=row.local_date,
            measured_at=row.measured_at,
            signal_value=float(row.signal_value),
        )
        for row in rows
    }


def get_body_measurement_snapshots_by_uuids(
    db: Session,
    *,
    user_id: UUID,
    measurement_uuids: Sequence[UUID],
) -> dict[UUID, BodyMeasurementSnapshot]:
    if not measurement_uuids:
        return {}

    stmt = select(
        BodyMeasurement.id,
        BodyMeasurement.healthkit_measurement_uuid,
        BodyMeasurement.measurement_type,
        BodyMeasurement.local_date,
        BodyMeasurement.measured_at,
        BodyMeasurement.measurement_value,
    ).where(
        BodyMeasurement.user_id == user_id,
        BodyMeasurement.healthkit_measurement_uuid.in_(list(measurement_uuids)),
    )
    rows = db.execute(stmt).all()
    return {
        row.healthkit_measurement_uuid: BodyMeasurementSnapshot(
            row_id=row.id,
            healthkit_measurement_uuid=row.healthkit_measurement_uuid,
            measurement_type=row.measurement_type,
            local_date=row.local_date,
            measured_at=row.measured_at,
            measurement_value=float(row.measurement_value),
        )
        for row in rows
    }


def upsert_sleep_sessions(db: Session, *, rows: Sequence[SleepSessionUpsert]) -> tuple[int, int]:
    if not rows:
        return (0, 0)

    uuids = [row.healthkit_sleep_uuid for row in rows]
    existing_stmt = select(SleepSession.healthkit_sleep_uuid).where(
        SleepSession.user_id == rows[0].user_id,
        SleepSession.healthkit_sleep_uuid.in_(uuids),
    )
    existing = set(db.execute(existing_stmt).scalars().all())
    insert_stmt = pg_insert(SleepSession).values(
        [
            {
                "healthkit_sleep_uuid": row.healthkit_sleep_uuid,
                "user_id": row.user_id,
                "start_at": row.start_at,
                "end_at": row.end_at,
                "local_date": row.local_date,
                "category_value": row.category_value,
                "source_bundle_id": row.source_bundle_id,
                "provider": row.provider,
                "source_count": row.source_count,
                "has_mixed_sources": row.has_mixed_sources,
                "primary_device_name": row.primary_device_name,
            }
            for row in rows
        ]
    )
    db.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["user_id", "healthkit_sleep_uuid"],
            set_={
                "start_at": insert_stmt.excluded.start_at,
                "end_at": insert_stmt.excluded.end_at,
                "local_date": insert_stmt.excluded.local_date,
                "category_value": insert_stmt.excluded.category_value,
                "source_bundle_id": insert_stmt.excluded.source_bundle_id,
                "provider": insert_stmt.excluded.provider,
                "source_count": insert_stmt.excluded.source_count,
                "has_mixed_sources": insert_stmt.excluded.has_mixed_sources,
                "primary_device_name": insert_stmt.excluded.primary_device_name,
                "updated_at": func.now(),
            },
        )
    )
    updated = len(existing.intersection(uuids))
    inserted = len(rows) - updated
    return (inserted, updated)


def upsert_recovery_signals(db: Session, *, rows: Sequence[RecoverySignalUpsert]) -> tuple[int, int]:
    if not rows:
        return (0, 0)
    uuids = [row.healthkit_signal_uuid for row in rows]
    existing_stmt = select(RecoverySignal.healthkit_signal_uuid).where(
        RecoverySignal.user_id == rows[0].user_id,
        RecoverySignal.healthkit_signal_uuid.in_(uuids),
    )
    existing = set(db.execute(existing_stmt).scalars().all())
    insert_stmt = pg_insert(RecoverySignal).values(
        [
            {
                "healthkit_signal_uuid": row.healthkit_signal_uuid,
                "user_id": row.user_id,
                "signal_type": row.signal_type,
                "measured_at": row.measured_at,
                "local_date": row.local_date,
                "signal_value": row.signal_value,
                "source_bundle_id": row.source_bundle_id,
                "provider": row.provider,
                "source_count": row.source_count,
                "has_mixed_sources": row.has_mixed_sources,
                "primary_device_name": row.primary_device_name,
            }
            for row in rows
        ]
    )
    db.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["user_id", "healthkit_signal_uuid"],
            set_={
                "signal_type": insert_stmt.excluded.signal_type,
                "measured_at": insert_stmt.excluded.measured_at,
                "local_date": insert_stmt.excluded.local_date,
                "signal_value": insert_stmt.excluded.signal_value,
                "source_bundle_id": insert_stmt.excluded.source_bundle_id,
                "provider": insert_stmt.excluded.provider,
                "source_count": insert_stmt.excluded.source_count,
                "has_mixed_sources": insert_stmt.excluded.has_mixed_sources,
                "primary_device_name": insert_stmt.excluded.primary_device_name,
                "updated_at": func.now(),
            },
        )
    )
    updated = len(existing.intersection(uuids))
    inserted = len(rows) - updated
    return (inserted, updated)


def upsert_body_measurements(db: Session, *, rows: Sequence[BodyMeasurementUpsert]) -> tuple[int, int]:
    if not rows:
        return (0, 0)
    uuids = [row.healthkit_measurement_uuid for row in rows]
    existing_stmt = select(BodyMeasurement.healthkit_measurement_uuid).where(
        BodyMeasurement.user_id == rows[0].user_id,
        BodyMeasurement.healthkit_measurement_uuid.in_(uuids),
    )
    existing = set(db.execute(existing_stmt).scalars().all())
    insert_stmt = pg_insert(BodyMeasurement).values(
        [
            {
                "healthkit_measurement_uuid": row.healthkit_measurement_uuid,
                "user_id": row.user_id,
                "measurement_type": row.measurement_type,
                "measured_at": row.measured_at,
                "local_date": row.local_date,
                "measurement_value": row.measurement_value,
                "source_bundle_id": row.source_bundle_id,
                "provider": row.provider,
                "source_count": row.source_count,
                "has_mixed_sources": row.has_mixed_sources,
                "primary_device_name": row.primary_device_name,
            }
            for row in rows
        ]
    )
    db.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["user_id", "healthkit_measurement_uuid"],
            set_={
                "measurement_type": insert_stmt.excluded.measurement_type,
                "measured_at": insert_stmt.excluded.measured_at,
                "local_date": insert_stmt.excluded.local_date,
                "measurement_value": insert_stmt.excluded.measurement_value,
                "source_bundle_id": insert_stmt.excluded.source_bundle_id,
                "provider": insert_stmt.excluded.provider,
                "source_count": insert_stmt.excluded.source_count,
                "has_mixed_sources": insert_stmt.excluded.has_mixed_sources,
                "primary_device_name": insert_stmt.excluded.primary_device_name,
                "updated_at": func.now(),
            },
        )
    )
    updated = len(existing.intersection(uuids))
    inserted = len(rows) - updated
    return (inserted, updated)


def upsert_daily_sleep_summary_rows(db: Session, *, rows: Sequence[DailySleepSummaryUpsert]) -> None:
    if not rows:
        return
    insert_stmt = pg_insert(DailySleepSummary).values([row.__dict__ for row in rows])
    db.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["user_id", "local_date"],
            set_={
                "total_sleep_sec": insert_stmt.excluded.total_sleep_sec,
                "main_sleep_start_at": insert_stmt.excluded.main_sleep_start_at,
                "main_sleep_end_at": insert_stmt.excluded.main_sleep_end_at,
                "main_sleep_duration_sec": insert_stmt.excluded.main_sleep_duration_sec,
                "naps_count": insert_stmt.excluded.naps_count,
                "naps_total_sleep_sec": insert_stmt.excluded.naps_total_sleep_sec,
                "completeness_status": insert_stmt.excluded.completeness_status,
                "provider": insert_stmt.excluded.provider,
                "source_count": insert_stmt.excluded.source_count,
                "has_mixed_sources": insert_stmt.excluded.has_mixed_sources,
                "primary_device_name": insert_stmt.excluded.primary_device_name,
                "updated_at": func.now(),
            },
        )
    )


def get_sleep_session_snapshots_for_summary_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Sequence[date],
) -> list[SleepSession]:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return []

    window_start = min(unique_dates) - timedelta(days=1)
    window_end = max(unique_dates)
    stmt = (
        select(SleepSession)
        .where(
            SleepSession.user_id == user_id,
            SleepSession.local_date >= window_start,
            SleepSession.local_date <= window_end,
        )
        .order_by(SleepSession.start_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def upsert_daily_activity_rows(db: Session, *, rows: Sequence[DailyActivityUpsert]) -> None:
    if not rows:
        return
    insert_stmt = pg_insert(DailyActivity).values([row.__dict__ for row in rows])
    db.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["user_id", "local_date"],
            set_={
                "steps": insert_stmt.excluded.steps,
                "walking_running_distance_m": insert_stmt.excluded.walking_running_distance_m,
                "active_energy_kcal": insert_stmt.excluded.active_energy_kcal,
                "completeness_status": insert_stmt.excluded.completeness_status,
                "provider": insert_stmt.excluded.provider,
                "source_count": insert_stmt.excluded.source_count,
                "has_mixed_sources": insert_stmt.excluded.has_mixed_sources,
                "primary_device_name": insert_stmt.excluded.primary_device_name,
                "updated_at": func.now(),
            },
        )
    )


def get_existing_daily_activity_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Sequence[date],
) -> set[date]:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return set()

    stmt = select(DailyActivity.local_date).where(
        DailyActivity.user_id == user_id,
        DailyActivity.local_date.in_(unique_dates),
    )
    return set(db.execute(stmt).scalars().all())


def upsert_daily_recovery_rows(db: Session, *, rows: Sequence[DailyRecoveryUpsert]) -> None:
    if not rows:
        return
    insert_stmt = pg_insert(DailyRecovery).values([row.__dict__ for row in rows])
    db.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["user_id", "local_date"],
            set_={
                "sleep_total_sec": insert_stmt.excluded.sleep_total_sec,
                "hrv_sdnn_ms": insert_stmt.excluded.hrv_sdnn_ms,
                "resting_hr_bpm": insert_stmt.excluded.resting_hr_bpm,
                "activity_present": insert_stmt.excluded.activity_present,
                "load_present": insert_stmt.excluded.load_present,
                "inputs_present": insert_stmt.excluded.inputs_present,
                "inputs_missing": insert_stmt.excluded.inputs_missing,
                "completeness_status": insert_stmt.excluded.completeness_status,
                "has_estimated_inputs": insert_stmt.excluded.has_estimated_inputs,
                "provider": insert_stmt.excluded.provider,
                "source_count": insert_stmt.excluded.source_count,
                "has_mixed_sources": insert_stmt.excluded.has_mixed_sources,
                "primary_device_name": insert_stmt.excluded.primary_device_name,
                "updated_at": func.now(),
            },
        )
    )


def delete_daily_sleep_summary_rows_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Iterable[date],
) -> int:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return 0
    result = db.execute(
        delete(DailySleepSummary).where(
            DailySleepSummary.user_id == user_id,
            DailySleepSummary.local_date.in_(unique_dates),
        )
    )
    return int(result.rowcount or 0)


def delete_daily_activity_rows_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Iterable[date],
) -> int:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return 0
    result = db.execute(
        delete(DailyActivity).where(
            DailyActivity.user_id == user_id,
            DailyActivity.local_date.in_(unique_dates),
        )
    )
    return int(result.rowcount or 0)


def delete_daily_recovery_rows_for_dates(
    db: Session,
    *,
    user_id: UUID,
    dates: Iterable[date],
) -> int:
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return 0
    result = db.execute(
        delete(DailyRecovery).where(
            DailyRecovery.user_id == user_id,
            DailyRecovery.local_date.in_(unique_dates),
        )
    )
    return int(result.rowcount or 0)
