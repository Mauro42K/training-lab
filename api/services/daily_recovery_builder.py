from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from api.repositories.daily_domains_repository import DailyRecoveryUpsert
from api.repositories.daily_recovery_repository import DailyLoadContext
from api.services.daily_domain_rules import (
    APPLE_HEALTH_PROVIDER,
    RECOVERY_SIGNAL_HRV,
    RECOVERY_SIGNAL_RHR,
    resolve_daily_recovery_completeness,
    resolve_primary_device_name,
)


@dataclass(frozen=True)
class _CanonicalSignal:
    signal_type: str
    signal_value: float
    measured_at: datetime
    source_count: int
    has_mixed_sources: bool
    source_bundle_id: str | None
    primary_device_name: str | None


class DailyRecoveryBuilder:
    def build_rows_for_dates(
        self,
        *,
        user_id,
        dates: Sequence[date],
        sleep_rows: Sequence[Any],
        signal_rows: Sequence[Any],
        activity_rows: Sequence[Any],
        load_context_by_date: dict[date, DailyLoadContext],
    ) -> list[DailyRecoveryUpsert]:
        sleep_by_date = {row.local_date: row for row in sleep_rows}
        activity_by_date = {row.local_date: row for row in activity_rows}
        signals_by_date = self._canonicalize_signals(signal_rows)

        rows: list[DailyRecoveryUpsert] = []
        for local_date in sorted(set(dates)):
            sleep_row = sleep_by_date.get(local_date)
            signal_map = signals_by_date.get(local_date, {})
            activity_row = activity_by_date.get(local_date)
            load_context = load_context_by_date.get(
                local_date,
                DailyLoadContext(local_date=local_date, load_present=False, has_estimated_inputs=False),
            )

            has_sleep = sleep_row is not None
            hrv_signal = signal_map.get(RECOVERY_SIGNAL_HRV)
            rhr_signal = signal_map.get(RECOVERY_SIGNAL_RHR)
            has_hrv = hrv_signal is not None
            has_rhr = rhr_signal is not None
            completeness = resolve_daily_recovery_completeness(
                has_sleep=has_sleep,
                has_hrv=has_hrv,
                has_rhr=has_rhr,
            )
            if completeness is None:
                continue

            inputs_present: list[str] = []
            inputs_missing: list[str] = []
            for name, present in (
                ("sleep", has_sleep),
                ("hrv", has_hrv),
                ("rhr", has_rhr),
                ("activity", activity_row is not None),
                ("load", load_context.load_present),
            ):
                if present:
                    inputs_present.append(name)
                else:
                    inputs_missing.append(name)

            provenance_rows = [row for row in (sleep_row, activity_row, hrv_signal, rhr_signal) if row is not None]
            source_bundle_ids = {
                getattr(row, "source_bundle_id", None)
                for row in provenance_rows
                if getattr(row, "source_bundle_id", None)
            }
            source_count = max(
                max((getattr(row, "source_count", 1) for row in provenance_rows), default=1),
                len(source_bundle_ids) or 1,
            )
            has_mixed_sources = any(
                bool(getattr(row, "has_mixed_sources", False))
                for row in provenance_rows
            ) or len(source_bundle_ids) > 1
            primary_device_name = resolve_primary_device_name(
                [getattr(row, "primary_device_name", None) for row in provenance_rows]
            )

            rows.append(
                DailyRecoveryUpsert(
                    user_id=user_id,
                    local_date=local_date,
                    sleep_total_sec=getattr(sleep_row, "total_sleep_sec", None),
                    hrv_sdnn_ms=hrv_signal.signal_value if hrv_signal is not None else None,
                    resting_hr_bpm=rhr_signal.signal_value if rhr_signal is not None else None,
                    activity_present=activity_row is not None,
                    load_present=load_context.load_present,
                    inputs_present=inputs_present,
                    inputs_missing=inputs_missing,
                    completeness_status=completeness,
                    has_estimated_inputs=load_context.has_estimated_inputs,
                    provider=APPLE_HEALTH_PROVIDER,
                    source_count=source_count,
                    has_mixed_sources=has_mixed_sources,
                    primary_device_name=primary_device_name,
                )
            )
        return rows

    def _canonicalize_signals(
        self,
        signal_rows: Sequence[Any],
    ) -> dict[date, dict[str, _CanonicalSignal]]:
        by_date: dict[date, dict[str, _CanonicalSignal]] = {}
        for row in signal_rows:
            date_map = by_date.setdefault(row.local_date, {})
            current = date_map.get(row.signal_type)
            if current is None or row.measured_at >= current.measured_at:
                date_map[row.signal_type] = _CanonicalSignal(
                    signal_type=row.signal_type,
                    signal_value=float(row.signal_value),
                    measured_at=row.measured_at,
                    source_count=getattr(row, "source_count", 1),
                    has_mixed_sources=bool(getattr(row, "has_mixed_sources", False)),
                    source_bundle_id=getattr(row, "source_bundle_id", None),
                    primary_device_name=getattr(row, "primary_device_name", None),
                )
        return by_date
