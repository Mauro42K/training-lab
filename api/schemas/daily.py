import datetime as dt

from pydantic import BaseModel, Field


class DailyItem(BaseModel):
    date: dt.date
    workouts_count: int = Field(ge=0)
    duration_sec_total: int = Field(ge=0)
    distance_m_total: float = Field(ge=0)
    energy_kcal_total: float = Field(ge=0)


class DailyResponse(BaseModel):
    items: list[DailyItem]
