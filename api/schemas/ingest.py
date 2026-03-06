import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

SportType = Literal["run", "bike", "strength", "walk", "other"]


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
