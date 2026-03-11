import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'America/New_York'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False, server_default=text("'default'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (
        UniqueConstraint("user_id", "healthkit_workout_uuid", name="uq_workouts_user_hk_uuid"),
        CheckConstraint(
            "sport IN ('run','bike','strength','walk','other')",
            name="workouts_sport_allowed",
        ),
        CheckConstraint(
            "avg_hr_bpm IS NULL OR (avg_hr_bpm >= 20 AND avg_hr_bpm <= 260)",
            name="workouts_avg_hr_bpm_range",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    healthkit_workout_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    sport: Mapped[str] = mapped_column(String(16), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_hr_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_kcal: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_bundle_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class IngestIdempotency(Base):
    __tablename__ = "ingest_idempotency"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_ingest_idempotency_user_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class WorkoutLoad(Base):
    __tablename__ = "workout_load"
    __table_args__ = (
        UniqueConstraint(
            "workout_id",
            "trimp_model_version",
            name="uq_workout_load_workout_model_version",
        ),
        CheckConstraint(
            "sport IN ('run','bike','strength','walk','other')",
            name="workout_load_sport_allowed",
        ),
        CheckConstraint(
            "trimp_source IN ('real','estimated')",
            name="workout_load_trimp_source_allowed",
        ),
        CheckConstraint("trimp_value >= 0", name="workout_load_trimp_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workout_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workouts.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    sport: Mapped[str] = mapped_column(String(16), nullable=False)
    trimp_value: Mapped[float] = mapped_column(Float, nullable=False)
    trimp_source: Mapped[str] = mapped_column(String(16), nullable=False)
    trimp_model_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    trimp_method: Mapped[str] = mapped_column(String(64), nullable=False)
    hr_rest_bpm_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_max_bpm_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intensity_factor_used: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DailyLoad(Base):
    __tablename__ = "daily_load"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "date",
            "sport_filter",
            "trimp_model_version",
            name="uq_daily_load_user_date_filter_model",
        ),
        CheckConstraint(
            "sport_filter IN ('all','run','bike','strength','walk')",
            name="daily_load_sport_filter_allowed",
        ),
        CheckConstraint("trimp_total >= 0", name="daily_load_trimp_non_negative"),
        CheckConstraint("sessions_count >= 0", name="daily_load_sessions_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    sport_filter: Mapped[str] = mapped_column(String(16), nullable=False)
    trimp_total: Mapped[float] = mapped_column(Float, nullable=False)
    sessions_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    trimp_model_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class BackfillJobState(Base):
    __tablename__ = "backfill_job_state"
    __table_args__ = (
        UniqueConstraint(
            "job_name",
            "trimp_model_version",
            name="uq_backfill_job_state_job_name_model_version",
        ),
        CheckConstraint("last_cursor_id >= 0", name="backfill_job_state_cursor_non_negative"),
        CheckConstraint("workouts_scanned >= 0", name="backfill_job_state_scanned_non_negative"),
        CheckConstraint("workouts_persisted >= 0", name="backfill_job_state_persisted_non_negative"),
        CheckConstraint(
            "workouts_excluded_or_deleted >= 0",
            name="backfill_job_state_excluded_non_negative",
        ),
        CheckConstraint(
            "affected_dates_rebuilt >= 0",
            name="backfill_job_state_dates_rebuilt_non_negative",
        ),
        CheckConstraint("batches_completed >= 0", name="backfill_job_state_batches_non_negative"),
        CheckConstraint(
            "status IN ('idle','running','completed','failed')",
            name="backfill_job_state_status_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)
    trimp_model_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'idle'"))
    last_cursor_id: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    workouts_scanned: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    workouts_persisted: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    workouts_excluded_or_deleted: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text("0"),
    )
    affected_dates_rebuilt: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text("0"),
    )
    batches_completed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SleepSession(Base):
    __tablename__ = "sleep_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "healthkit_sleep_uuid", name="uq_sleep_sessions_user_hk_uuid"),
        CheckConstraint("end_at >= start_at", name="sleep_sessions_time_range"),
        CheckConstraint("provider = 'apple_health'", name="sleep_sessions_provider_allowed"),
        CheckConstraint("source_count >= 1", name="sleep_sessions_source_count_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    healthkit_sleep_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    category_value: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_bundle_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'apple_health'"))
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    has_mixed_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    primary_device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class RecoverySignal(Base):
    __tablename__ = "recovery_signals"
    __table_args__ = (
        UniqueConstraint("user_id", "healthkit_signal_uuid", name="uq_recovery_signals_user_hk_uuid"),
        CheckConstraint(
            "signal_type IN ('hrv_sdnn','resting_hr')",
            name="recovery_signals_type_allowed",
        ),
        CheckConstraint("signal_value >= 0", name="recovery_signals_value_non_negative"),
        CheckConstraint("provider = 'apple_health'", name="recovery_signals_provider_allowed"),
        CheckConstraint("source_count >= 1", name="recovery_signals_source_count_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    healthkit_signal_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    signal_value: Mapped[float] = mapped_column(Float, nullable=False)
    source_bundle_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'apple_health'"))
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    has_mixed_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    primary_device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "healthkit_measurement_uuid",
            name="uq_body_measurements_user_hk_uuid",
        ),
        CheckConstraint(
            "measurement_type IN ('weight_kg','body_fat_pct','lean_body_mass_kg')",
            name="body_measurements_type_allowed",
        ),
        CheckConstraint("measurement_value >= 0", name="body_measurements_value_non_negative"),
        CheckConstraint("provider = 'apple_health'", name="body_measurements_provider_allowed"),
        CheckConstraint("source_count >= 1", name="body_measurements_source_count_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    healthkit_measurement_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    measurement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    measurement_value: Mapped[float] = mapped_column(Float, nullable=False)
    source_bundle_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'apple_health'"))
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    has_mixed_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    primary_device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DailySleepSummary(Base):
    __tablename__ = "daily_sleep_summary"
    __table_args__ = (
        UniqueConstraint("user_id", "local_date", name="uq_daily_sleep_summary_user_date"),
        CheckConstraint(
            "completeness_status IN ('complete','partial')",
            name="daily_sleep_summary_completeness_allowed",
        ),
        CheckConstraint("total_sleep_sec >= 0", name="daily_sleep_summary_total_non_negative"),
        CheckConstraint(
            "main_sleep_duration_sec >= 0",
            name="daily_sleep_summary_main_duration_non_negative",
        ),
        CheckConstraint("naps_count >= 0", name="daily_sleep_summary_naps_count_non_negative"),
        CheckConstraint(
            "naps_total_sleep_sec >= 0",
            name="daily_sleep_summary_naps_total_non_negative",
        ),
        CheckConstraint(
            "main_sleep_end_at >= main_sleep_start_at",
            name="daily_sleep_summary_main_sleep_range",
        ),
        CheckConstraint("provider = 'apple_health'", name="daily_sleep_summary_provider_allowed"),
        CheckConstraint("source_count >= 1", name="daily_sleep_summary_source_count_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_sleep_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    main_sleep_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    main_sleep_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    main_sleep_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    naps_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    naps_total_sleep_sec: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    completeness_status: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'apple_health'"))
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    has_mixed_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    primary_device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DailyActivity(Base):
    __tablename__ = "daily_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "local_date", name="uq_daily_activity_user_date"),
        CheckConstraint(
            "completeness_status IN ('complete','partial')",
            name="daily_activity_completeness_allowed",
        ),
        CheckConstraint("steps IS NULL OR steps >= 0", name="daily_activity_steps_non_negative"),
        CheckConstraint(
            "walking_running_distance_m IS NULL OR walking_running_distance_m >= 0",
            name="daily_activity_distance_non_negative",
        ),
        CheckConstraint(
            "active_energy_kcal IS NULL OR active_energy_kcal >= 0",
            name="daily_activity_energy_non_negative",
        ),
        CheckConstraint(
            "(steps IS NOT NULL OR walking_running_distance_m IS NOT NULL OR active_energy_kcal IS NOT NULL)",
            name="daily_activity_has_value",
        ),
        CheckConstraint("provider = 'apple_health'", name="daily_activity_provider_allowed"),
        CheckConstraint("source_count >= 1", name="daily_activity_source_count_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    walking_running_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    active_energy_kcal: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness_status: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'apple_health'"))
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    has_mixed_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    primary_device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DailyRecovery(Base):
    __tablename__ = "daily_recovery"
    __table_args__ = (
        UniqueConstraint("user_id", "local_date", name="uq_daily_recovery_user_date"),
        CheckConstraint(
            "completeness_status IN ('complete','partial')",
            name="daily_recovery_completeness_allowed",
        ),
        CheckConstraint(
            "sleep_total_sec IS NULL OR sleep_total_sec >= 0",
            name="daily_recovery_sleep_total_non_negative",
        ),
        CheckConstraint(
            "hrv_sdnn_ms IS NULL OR hrv_sdnn_ms >= 0",
            name="daily_recovery_hrv_non_negative",
        ),
        CheckConstraint(
            "resting_hr_bpm IS NULL OR resting_hr_bpm >= 0",
            name="daily_recovery_rhr_non_negative",
        ),
        CheckConstraint(
            "(sleep_total_sec IS NOT NULL OR hrv_sdnn_ms IS NOT NULL OR resting_hr_bpm IS NOT NULL)",
            name="daily_recovery_requires_physiological_input",
        ),
        CheckConstraint("provider = 'apple_health'", name="daily_recovery_provider_allowed"),
        CheckConstraint("source_count >= 1", name="daily_recovery_source_count_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_total_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hrv_sdnn_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    resting_hr_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    load_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    inputs_present: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    inputs_missing: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    completeness_status: Mapped[str] = mapped_column(String(16), nullable=False)
    has_estimated_inputs: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'apple_health'"))
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    has_mixed_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    primary_device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
