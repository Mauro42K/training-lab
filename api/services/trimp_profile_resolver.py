from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from api.core.config import Settings


@dataclass(frozen=True)
class TrimpPhysiologyProfile:
    hr_rest_bpm: int
    hr_max_bpm: int
    source: Literal["defaults", "user_profile"]


class TrimpPhysiologyResolver:
    """Resolves physiological parameters for TRIMP calculation."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve_for_user(self, *, user_id: UUID | None) -> TrimpPhysiologyProfile:
        _ = user_id
        # Phase 4: no persisted physiological profile yet, so we always use
        # centralized global defaults from Settings.
        profile = TrimpPhysiologyProfile(
            hr_rest_bpm=self.settings.trimp_hr_rest_default,
            hr_max_bpm=self.settings.trimp_hr_max_default,
            source="defaults",
        )
        if profile.hr_max_bpm <= profile.hr_rest_bpm:
            raise ValueError("Invalid TRIMP HR defaults: hr_max must be greater than hr_rest")
        return profile
