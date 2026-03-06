import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

TrainingLoadSportFilter = Literal["all", "run", "bike", "strength", "walk"]


class TrainingLoadItem(BaseModel):
    date: dt.date
    trimp: float = Field(ge=0)


class TrainingLoadResponse(BaseModel):
    items: list[TrainingLoadItem]
