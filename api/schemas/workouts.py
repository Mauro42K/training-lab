import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

SportType = Literal["run", "bike", "strength", "walk", "other"]


class WorkoutOut(BaseModel):
    healthkit_workout_uuid: UUID
    sport: SportType
    start: dt.datetime
    end: dt.datetime
    duration_sec: int = Field(ge=0)
    distance_m: float | None = Field(default=None, ge=0)
    energy_kcal: float | None = Field(default=None, ge=0)
    source_bundle_id: str | None = None
    device_name: str | None = None


class WorkoutsResponse(BaseModel):
    items: list[WorkoutOut]
