import math
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from api.core.config import Settings, get_settings
from api.services.trimp_profile_resolver import TrimpPhysiologyProfile, TrimpPhysiologyResolver

TrimpSource = Literal["real", "estimated", "excluded"]


@dataclass(frozen=True)
class TrimpWorkoutInput:
    sport: str
    duration_sec: int
    avg_hr_bpm: float | None


@dataclass(frozen=True)
class TrimpEngineResult:
    trimp_value: float
    trimp_source: TrimpSource
    trimp_method: str
    trimp_model_version: int
    hr_rest_bpm_used: int | None
    hr_max_bpm_used: int | None
    intensity_factor_used: float | None
    is_computed: bool
    is_excluded: bool


class TrimpV1BanisterHRRStrategy:
    SUPPORTED_SPORTS = frozenset({"run", "bike", "strength", "walk"})

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def calculate(
        self,
        *,
        workout: TrimpWorkoutInput,
        profile: TrimpPhysiologyProfile,
    ) -> TrimpEngineResult:
        sport = workout.sport.lower().strip()
        duration_min = max(workout.duration_sec, 0) / 60.0

        if sport not in self.SUPPORTED_SPORTS:
            return TrimpEngineResult(
                trimp_value=0.0,
                trimp_source="excluded",
                trimp_method=self.settings.trimp_active_method,
                trimp_model_version=self.settings.trimp_active_model_version,
                hr_rest_bpm_used=None,
                hr_max_bpm_used=None,
                intensity_factor_used=None,
                is_computed=False,
                is_excluded=True,
            )

        if workout.avg_hr_bpm is not None:
            hr_range = profile.hr_max_bpm - profile.hr_rest_bpm
            hrr = (workout.avg_hr_bpm - profile.hr_rest_bpm) / hr_range
            hrr = max(0.0, min(1.0, hrr))
            intensity_component = 0.64 * math.exp(1.92 * hrr)
            trimp_value = duration_min * hrr * intensity_component
            return TrimpEngineResult(
                trimp_value=trimp_value,
                trimp_source="real",
                trimp_method=self.settings.trimp_active_method,
                trimp_model_version=self.settings.trimp_active_model_version,
                hr_rest_bpm_used=profile.hr_rest_bpm,
                hr_max_bpm_used=profile.hr_max_bpm,
                intensity_factor_used=None,
                is_computed=True,
                is_excluded=False,
            )

        factor = self.settings.trimp_sport_factors[sport]
        trimp_value = duration_min * factor
        return TrimpEngineResult(
            trimp_value=trimp_value,
            trimp_source="estimated",
            trimp_method=self.settings.trimp_active_method,
            trimp_model_version=self.settings.trimp_active_model_version,
            hr_rest_bpm_used=None,
            hr_max_bpm_used=None,
            intensity_factor_used=factor,
            is_computed=True,
            is_excluded=False,
        )


class TrimpEngineService:
    """Single entrypoint for TRIMP computation across the backend."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        profile_resolver: TrimpPhysiologyResolver | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.profile_resolver = profile_resolver or TrimpPhysiologyResolver(self.settings)
        self.strategy = TrimpV1BanisterHRRStrategy(self.settings)

    def calculate_for_workout(
        self,
        *,
        user_id: UUID | None,
        sport: str,
        duration_sec: int,
        avg_hr_bpm: float | None,
    ) -> TrimpEngineResult:
        profile = self.profile_resolver.resolve_for_user(user_id=user_id)
        workout = TrimpWorkoutInput(
            sport=sport,
            duration_sec=duration_sec,
            avg_hr_bpm=avg_hr_bpm,
        )
        return self.strategy.calculate(workout=workout, profile=profile)
