from collections.abc import Iterable, Sequence
from datetime import date
from typing import Literal

CompletenessStatus = Literal["complete", "partial"]

APPLE_HEALTH_PROVIDER = "apple_health"
RECOVERY_SIGNAL_HRV = "hrv_sdnn"
RECOVERY_SIGNAL_RHR = "resting_hr"
BODY_MEASUREMENT_WEIGHT = "weight_kg"
BODY_MEASUREMENT_BODY_FAT = "body_fat_pct"
BODY_MEASUREMENT_LEAN_MASS = "lean_body_mass_kg"


def resolve_primary_device_name(device_names: Sequence[str | None]) -> str | None:
    normalized = {
        item.strip()
        for item in device_names
        if item is not None and item.strip() != ""
    }
    if len(normalized) != 1:
        return None
    return next(iter(normalized))


def resolve_daily_recovery_completeness(
    *,
    has_sleep: bool,
    has_hrv: bool,
    has_rhr: bool,
) -> CompletenessStatus | None:
    if not (has_sleep or has_hrv or has_rhr):
        return None
    if has_sleep and has_hrv and has_rhr:
        return "complete"
    return "partial"


def resolve_daily_activity_completeness(
    *,
    steps: int | None,
    walking_running_distance_m: float | None,
    active_energy_kcal: float | None,
) -> CompletenessStatus | None:
    has_steps = steps is not None
    has_distance = walking_running_distance_m is not None
    has_energy = active_energy_kcal is not None
    if not (has_steps or has_distance or has_energy):
        return None
    if has_steps and has_distance:
        return "complete"
    return "partial"


def merge_affected_dates(*date_groups: Iterable[date]) -> set[date]:
    merged: set[date] = set()
    for group in date_groups:
        merged.update(group)
    return merged
