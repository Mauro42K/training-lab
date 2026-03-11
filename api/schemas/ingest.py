import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

SportType = Literal["run", "bike", "strength", "walk", "other"]
BodyMeasurementType = Literal["weight_kg", "body_fat_pct", "lean_body_mass_kg"]
RecoverySignalType = Literal["hrv_sdnn", "resting_hr"]


class WorkoutIngestItem(BaseModel):
    healthkit_workout_uuid: UUID
    sport: SportType
    start: dt.datetime
    end: dt.datetime
    duration_sec: int = Field(ge=0, le=172800)
    avg_hr_bpm: float | None = Field(default=None, ge=20, le=260)
    distance_m: float | None = Field(default=None, ge=0, le=1_000_000)
    energy_kcal: float | None = Field(default=None, ge=0, le=100_000)
    source_bundle_id: str | None = Field(default=None, max_length=255)
    device_name: str | None = Field(default=None, max_length=255)
    is_deleted: bool = False

    @model_validator(mode="after")
    def validate_time_range(self) -> "WorkoutIngestItem":
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        return self


class WorkoutsIngestRequest(BaseModel):
    workouts: list[WorkoutIngestItem] = Field(min_length=1, max_length=5000)


class IngestWorkoutsResponse(BaseModel):
    inserted: int
    updated: int
    total_received: int
    idempotent_replay: bool = False


class SleepSessionIngestItem(BaseModel):
    healthkit_sleep_uuid: UUID
    start: dt.datetime
    end: dt.datetime
    category_value: str | None = Field(default=None, max_length=32)
    source_bundle_id: str | None = Field(default=None, max_length=255)
    source_count: int = Field(default=1, ge=1, le=100)
    has_mixed_sources: bool = False
    primary_device_name: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_time_range(self) -> "SleepSessionIngestItem":
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        return self


class SleepSessionsIngestRequest(BaseModel):
    timezone: str | None = Field(default=None, max_length=64)
    sleep_sessions: list[SleepSessionIngestItem] = Field(min_length=1, max_length=5000)


class IngestSleepSessionsResponse(BaseModel):
    inserted: int
    updated: int
    total_received: int
    rebuilt_dates: int
    invalidated_daily_recovery_dates: int
    idempotent_replay: bool = False


class DailyActivityIngestItem(BaseModel):
    bucket_start: dt.datetime
    steps: int | None = Field(default=None, ge=0, le=1_000_000)
    walking_running_distance_m: float | None = Field(default=None, ge=0, le=1_000_000)
    active_energy_kcal: float | None = Field(default=None, ge=0, le=100_000)
    source_bundle_id: str | None = Field(default=None, max_length=255)
    source_count: int = Field(default=1, ge=1, le=100)
    has_mixed_sources: bool = False
    primary_device_name: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_has_value(self) -> "DailyActivityIngestItem":
        if (
            self.steps is None
            and self.walking_running_distance_m is None
            and self.active_energy_kcal is None
        ):
            raise ValueError("at least one daily activity value must be provided")
        return self


class DailyActivityIngestRequest(BaseModel):
    timezone: str | None = Field(default=None, max_length=64)
    daily_activity: list[DailyActivityIngestItem] = Field(min_length=1, max_length=5000)


class IngestDailyActivityResponse(BaseModel):
    inserted: int
    updated: int
    total_received: int
    rebuilt_dates: int
    invalidated_daily_recovery_dates: int
    idempotent_replay: bool = False


class BodyMeasurementIngestItem(BaseModel):
    healthkit_measurement_uuid: UUID
    measurement_type: BodyMeasurementType
    measured_at: dt.datetime
    value: float = Field(ge=0, le=1_000_000)
    source_bundle_id: str | None = Field(default=None, max_length=255)
    source_count: int = Field(default=1, ge=1, le=100)
    has_mixed_sources: bool = False
    primary_device_name: str | None = Field(default=None, max_length=255)


class BodyMeasurementsIngestRequest(BaseModel):
    timezone: str | None = Field(default=None, max_length=64)
    body_measurements: list[BodyMeasurementIngestItem] = Field(min_length=1, max_length=5000)


class IngestBodyMeasurementsResponse(BaseModel):
    inserted: int
    updated: int
    total_received: int
    affected_dates: int
    canonicalized_dates: int
    idempotent_replay: bool = False


class RecoverySignalIngestItem(BaseModel):
    healthkit_signal_uuid: UUID
    signal_type: RecoverySignalType
    measured_at: dt.datetime
    value: float = Field(ge=0, le=1_000_000)
    source_bundle_id: str | None = Field(default=None, max_length=255)
    source_count: int = Field(default=1, ge=1, le=100)
    has_mixed_sources: bool = False
    primary_device_name: str | None = Field(default=None, max_length=255)


class RecoverySignalsIngestRequest(BaseModel):
    timezone: str | None = Field(default=None, max_length=64)
    recovery_signals: list[RecoverySignalIngestItem] = Field(min_length=1, max_length=5000)


class IngestRecoverySignalsResponse(BaseModel):
    inserted: int
    updated: int
    total_received: int
    rebuilt_dates: int
    rebuilt_daily_recovery_rows: int
    idempotent_replay: bool = False
