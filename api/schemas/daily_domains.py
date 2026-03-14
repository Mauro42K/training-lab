import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.training_load import TrainingLoadHistoryStatus

CompletenessStatus = Literal["complete", "partial"]
ReadinessCompletenessStatus = Literal["complete", "partial", "insufficient", "missing"]
ReadinessLabel = Literal["Ready", "Moderate", "Recover"]


class DailySleepDomainItem(BaseModel):
    date: dt.date
    total_sleep_sec: int = Field(ge=0)
    main_sleep_duration_sec: int = Field(ge=0)
    naps_count: int = Field(ge=0)
    naps_total_sleep_sec: int = Field(ge=0)
    completeness_status: CompletenessStatus
    provider: str
    source_count: int = Field(ge=1)
    has_mixed_sources: bool
    primary_device_name: str | None = None


class DailyActivityDomainItem(BaseModel):
    date: dt.date
    steps: int | None = Field(default=None, ge=0)
    walking_running_distance_m: float | None = Field(default=None, ge=0)
    active_energy_kcal: float | None = Field(default=None, ge=0)
    completeness_status: CompletenessStatus
    provider: str
    source_count: int = Field(ge=1)
    has_mixed_sources: bool
    primary_device_name: str | None = None


class DailyRecoveryDomainItem(BaseModel):
    date: dt.date
    sleep_total_sec: int | None = Field(default=None, ge=0)
    hrv_sdnn_ms: float | None = Field(default=None, ge=0)
    resting_hr_bpm: float | None = Field(default=None, ge=0)
    activity_present: bool
    load_present: bool
    inputs_present: list[str]
    inputs_missing: list[str]
    completeness_status: CompletenessStatus
    has_estimated_inputs: bool
    provider: str
    source_count: int = Field(ge=1)
    has_mixed_sources: bool
    primary_device_name: str | None = None


class ReadinessTraceInput(BaseModel):
    name: str
    role: Literal["primary", "context"]
    present: bool
    baseline_used: bool
    effect: Literal["positive", "neutral", "negative", "not_used"]


class ReadinessSummaryItem(BaseModel):
    score: int | None = Field(default=None, ge=0, le=100)
    label: ReadinessLabel | None = None
    confidence: float = Field(ge=0, le=1)
    completeness_status: ReadinessCompletenessStatus
    inputs_present: list[str]
    inputs_missing: list[str]
    model_version: int = Field(ge=1)
    has_estimated_context: bool
    trace_summary: list[ReadinessTraceInput]


class CoreMetricsSummaryItem(BaseModel):
    seven_day_load: float = Field(ge=0)
    fitness: float = Field(ge=0)
    fatigue: float = Field(ge=0)
    history_status: TrainingLoadHistoryStatus


class BodyMeasurementsDomainItem(BaseModel):
    date: dt.date
    weight_kg: float = Field(ge=0)
    body_fat_pct: float | None = Field(default=None, ge=0)
    lean_body_mass_kg: float | None = Field(default=None, ge=0)
    provider: str
    source_count: int = Field(ge=1)
    has_mixed_sources: bool
    primary_device_name: str | None = None


class DailySleepDomainResponse(BaseModel):
    items: list[DailySleepDomainItem]


class DailyActivityDomainResponse(BaseModel):
    items: list[DailyActivityDomainItem]


class DailyRecoveryDomainResponse(BaseModel):
    items: list[DailyRecoveryDomainItem]


class BodyMeasurementsDomainResponse(BaseModel):
    items: list[BodyMeasurementsDomainItem]


class HomeSummaryResponse(BaseModel):
    date: dt.date
    sleep: DailySleepDomainItem | None = None
    activity: DailyActivityDomainItem | None = None
    recovery: DailyRecoveryDomainItem | None = None
    body_measurements: BodyMeasurementsDomainItem | None = None
    readiness: ReadinessSummaryItem | None = None
    core_metrics: CoreMetricsSummaryItem | None = None
