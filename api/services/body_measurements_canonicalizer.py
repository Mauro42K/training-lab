from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from api.services.daily_domain_rules import (
    APPLE_HEALTH_PROVIDER,
    BODY_MEASUREMENT_BODY_FAT,
    BODY_MEASUREMENT_LEAN_MASS,
    BODY_MEASUREMENT_WEIGHT,
    resolve_primary_device_name,
)


@dataclass(frozen=True)
class CanonicalBodyMeasurementDay:
    local_date: date
    weight_kg: float
    body_fat_pct: float | None
    lean_body_mass_kg: float | None
    provider: str
    source_count: int
    has_mixed_sources: bool
    primary_device_name: str | None


class BodyMeasurementsCanonicalizer:
    def build_days(
        self,
        *,
        measurements: list[Any],
    ) -> list[CanonicalBodyMeasurementDay]:
        measurements_by_date: dict[date, list[Any]] = defaultdict(list)
        for measurement in measurements:
            measurements_by_date[measurement.local_date].append(measurement)

        days: list[CanonicalBodyMeasurementDay] = []
        for local_date in sorted(measurements_by_date):
            measurements_for_date = measurements_by_date[local_date]
            latest_by_type = self._pick_latest_by_type(measurements_for_date)
            weight = latest_by_type.get(BODY_MEASUREMENT_WEIGHT)
            if weight is None:
                continue
            body_fat = latest_by_type.get(BODY_MEASUREMENT_BODY_FAT)
            lean_mass = latest_by_type.get(BODY_MEASUREMENT_LEAN_MASS)
            selected_measurements = [value for value in latest_by_type.values()]
            source_bundle_ids = {
                getattr(item, "source_bundle_id", None)
                for item in measurements_for_date
                if getattr(item, "source_bundle_id", None)
            }
            days.append(
                CanonicalBodyMeasurementDay(
                    local_date=local_date,
                    weight_kg=float(weight.measurement_value),
                    body_fat_pct=(
                        float(body_fat.measurement_value)
                        if body_fat is not None
                        else None
                    ),
                    lean_body_mass_kg=(
                        float(lean_mass.measurement_value)
                        if lean_mass is not None
                        else None
                    ),
                    provider=APPLE_HEALTH_PROVIDER,
                    source_count=max(
                        max((getattr(item, "source_count", 1) for item in selected_measurements), default=1),
                        len(source_bundle_ids) or 1,
                    ),
                    has_mixed_sources=any(
                        bool(getattr(item, "has_mixed_sources", False))
                        for item in measurements_for_date
                    ) or len(source_bundle_ids) > 1,
                    primary_device_name=resolve_primary_device_name(
                        [getattr(item, "primary_device_name", None) for item in selected_measurements]
                    ),
                )
            )
        return days

    def _pick_latest_by_type(self, measurements: list[Any]) -> dict[str, Any]:
        latest_by_type: dict[str, Any] = {}
        for measurement in measurements:
            current = latest_by_type.get(measurement.measurement_type)
            measured_at = self._normalize_measured_at(measurement.measured_at)
            if current is None or measured_at >= self._normalize_measured_at(current.measured_at):
                latest_by_type[measurement.measurement_type] = measurement
        return latest_by_type

    def _normalize_measured_at(self, measured_at: datetime) -> datetime:
        if measured_at.tzinfo is None:
            return measured_at
        return measured_at.astimezone(UTC)
