import datetime as dt
from typing import Literal

from sqlalchemy.orm import Session

from api.repositories.user_repository import get_or_create_default_user
from api.repositories.workouts_repository import get_workouts
from api.schemas.workouts import WorkoutOut, WorkoutsResponse

SportType = Literal["run", "bike", "strength", "walk", "other"]


class WorkoutsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_workouts(
        self,
        *,
        from_dt: dt.datetime,
        to_dt: dt.datetime,
        sport: SportType | None,
    ) -> WorkoutsResponse:
        user = get_or_create_default_user(self.db)
        workouts = get_workouts(
            self.db,
            user_id=user.id,
            from_dt=from_dt,
            to_dt=to_dt,
            sport=sport,
        )
        items = [
            WorkoutOut(
                healthkit_workout_uuid=workout.healthkit_workout_uuid,
                sport=workout.sport,
                start=workout.start,
                end=workout.end,
                duration_sec=workout.duration_sec,
                distance_m=workout.distance_m,
                energy_kcal=workout.energy_kcal,
                source_bundle_id=workout.source_bundle_id,
                device_name=workout.device_name,
            )
            for workout in workouts
        ]
        return WorkoutsResponse(items=items)
