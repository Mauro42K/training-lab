import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

TrainingLoadSportFilter = Literal["all", "run", "bike", "strength", "walk"]
TrainingLoadHistoryStatus = Literal["available", "partial", "insufficient_history", "missing"]
TrainingLoadSemanticState = Literal[
    "below_capacity",
    "within_range",
    "near_limit",
    "above_capacity",
]


class TrainingLoadItem(BaseModel):
    date: dt.date
    load: float = Field(ge=0)
    capacity: float = Field(ge=0)
    trimp: float = Field(ge=0)


class TrainingLoadResponse(BaseModel):
    items: list[TrainingLoadItem]
    history_status: TrainingLoadHistoryStatus
    semantic_state: TrainingLoadSemanticState | None = None
    latest_load: float = Field(ge=0)
    latest_capacity: float = Field(ge=0)
