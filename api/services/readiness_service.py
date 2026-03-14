import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from api.core.config import Settings, get_settings
from api.repositories.daily_recovery_repository import (
    DailyLoadContext,
    get_daily_load_context_for_dates,
    get_daily_recovery_by_date,
    get_daily_recovery_range,
)
from api.repositories.daily_sleep_repository import get_daily_sleep_summary_range
from api.repositories.load_repository import get_daily_load_rows
from api.schemas.daily_domains import ReadinessSummaryItem, ReadinessTraceInput


@dataclass(frozen=True)
class ReadinessModelConfig:
    model_version: int = 1
    score_anchor: float = 65.0
    sleep_weight: float = 0.40
    hrv_weight: float = 0.35
    rhr_weight: float = 0.25
    hrv_baseline_window_days: int = 28
    rhr_baseline_window_days: int = 28
    sleep_baseline_preferred_days: int = 7
    sleep_baseline_fallback_days: int = 14
    sleep_baseline_min_observations: int = 4
    ready_threshold: int = 75
    moderate_threshold: int = 50
    sleep_ratio_scale: float = 120.0
    hrv_ratio_scale: float = 100.0
    rhr_ratio_scale: float = 140.0
    complete_confidence: float = 0.93
    partial_confidence: float = 0.72
    insufficient_confidence: float = 0.42
    missing_confidence: float = 0.0
    missing_baseline_penalty: float = 0.10
    estimated_context_penalty: float = 0.05
    insufficient_score_regression: float = 0.45
    recent_exertion_penalty_cap: float = 5.0
    recent_exertion_penalty_scale: float = 10.0

    @property
    def driver_weights(self) -> dict[str, float]:
        return {
            "sleep": self.sleep_weight,
            "hrv": self.hrv_weight,
            "rhr": self.rhr_weight,
        }


@dataclass(frozen=True)
class _DriverEvaluation:
    name: str
    present: bool
    baseline_used: bool
    score: float | None
    effect: str


class ReadinessService:
    def __init__(
        self,
        db: Session,
        *,
        settings: Settings | None = None,
        config: ReadinessModelConfig | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.config = config or ReadinessModelConfig()

    def get_readiness(
        self,
        *,
        user_id: UUID,
        target_date: dt.date,
        current_recovery_row: Any | None = None,
    ) -> ReadinessSummaryItem:
        current_row = current_recovery_row or get_daily_recovery_by_date(
            self.db,
            user_id=user_id,
            target_date=target_date,
        )
        history_end = target_date - dt.timedelta(days=1)
        history_start = target_date - dt.timedelta(days=self.config.hrv_baseline_window_days)

        recovery_history = (
            get_daily_recovery_range(
                self.db,
                user_id=user_id,
                from_date=history_start,
                to_date=history_end,
            )
            if history_end >= history_start
            else []
        )
        sleep_history = (
            get_daily_sleep_summary_range(
                self.db,
                user_id=user_id,
                from_date=target_date - dt.timedelta(days=self.config.sleep_baseline_fallback_days),
                to_date=history_end,
            )
            if history_end >= target_date - dt.timedelta(days=self.config.sleep_baseline_fallback_days)
            else []
        )
        load_rows = (
            get_daily_load_rows(
                self.db,
                user_id=user_id,
                from_date=target_date - dt.timedelta(days=self.config.hrv_baseline_window_days),
                to_date=history_end,
                sport_filter="all",
                trimp_model_version=self.settings.trimp_active_model_version,
            )
            if history_end >= target_date - dt.timedelta(days=self.config.hrv_baseline_window_days)
            else []
        )
        recent_load_dates = self._date_window(
            end_date=history_end,
            days=7,
        )
        load_context_by_date = get_daily_load_context_for_dates(
            self.db,
            user_id=user_id,
            dates=recent_load_dates,
            trimp_model_version=self.settings.trimp_active_model_version,
        )

        return self.build_readiness(
            target_date=target_date,
            current_recovery_row=current_row,
            recovery_history_rows=recovery_history,
            sleep_history_rows=sleep_history,
            load_rows=load_rows,
            load_context_by_date=load_context_by_date,
        )

    def build_readiness(
        self,
        *,
        target_date: dt.date,
        current_recovery_row: Any | None,
        recovery_history_rows: Sequence[Any],
        sleep_history_rows: Sequence[Any],
        load_rows: Sequence[tuple[dt.date, float]],
        load_context_by_date: dict[dt.date, DailyLoadContext],
    ) -> ReadinessSummaryItem:
        evaluations = self._evaluate_primary_inputs(
            target_date=target_date,
            current_recovery_row=current_recovery_row,
            recovery_history_rows=recovery_history_rows,
            sleep_history_rows=sleep_history_rows,
        )
        inputs_present = [evaluation.name for evaluation in evaluations if evaluation.present]
        inputs_missing = [evaluation.name for evaluation in evaluations if not evaluation.present]
        completeness_status = self._resolve_completeness_status(len(inputs_present))
        has_estimated_context = any(
            context.has_estimated_inputs for context in load_context_by_date.values()
        )

        raw_score = self._aggregate_primary_score(evaluations=evaluations)
        score = None
        label = None
        context_penalty = 0.0
        if raw_score is not None:
            if completeness_status == "insufficient":
                raw_score = self.config.score_anchor + (
                    (raw_score - self.config.score_anchor) * self.config.insufficient_score_regression
                )
            context_penalty = self._recent_exertion_penalty(
                target_date=target_date,
                load_rows=load_rows,
            )
            score = int(round(self._clamp(raw_score - context_penalty, lower=0, upper=100)))
            label = self._resolve_label(score)

        confidence = self._resolve_confidence(
            completeness_status=completeness_status,
            evaluations=evaluations,
            has_estimated_context=has_estimated_context,
        )

        trace_summary = [
            ReadinessTraceInput(
                name=evaluation.name,
                role="primary",
                present=evaluation.present,
                baseline_used=evaluation.baseline_used,
                effect=evaluation.effect,  # type: ignore[arg-type]
            )
            for evaluation in evaluations
        ]
        trace_summary.append(
            ReadinessTraceInput(
                name="recent_exertion",
                role="context",
                present=bool(load_rows),
                baseline_used=bool(load_rows),
                effect="negative" if context_penalty > 0 else ("neutral" if load_rows else "not_used"),
            )
        )

        return ReadinessSummaryItem(
            score=score,
            label=label,
            confidence=confidence,
            completeness_status=completeness_status,
            inputs_present=inputs_present,
            inputs_missing=inputs_missing,
            model_version=self.config.model_version,
            has_estimated_context=has_estimated_context,
            trace_summary=trace_summary,
        )

    def _evaluate_primary_inputs(
        self,
        *,
        target_date: dt.date,
        current_recovery_row: Any | None,
        recovery_history_rows: Sequence[Any],
        sleep_history_rows: Sequence[Any],
    ) -> list[_DriverEvaluation]:
        anchor = self.config.score_anchor
        sleep_current = getattr(current_recovery_row, "sleep_total_sec", None)
        sleep_baseline = self._sleep_baseline_seconds(
            sleep_history_rows,
            target_date=target_date,
        )
        sleep_score, sleep_baseline_used = self._score_against_baseline(
            current_value=sleep_current,
            baseline_value=sleep_baseline,
            ratio_scale=self.config.sleep_ratio_scale,
            invert=False,
        )

        hrv_current = getattr(current_recovery_row, "hrv_sdnn_ms", None)
        hrv_baseline = self._mean_valid_values(
            recovery_history_rows,
            attr_name="hrv_sdnn_ms",
            target_date=target_date,
            window_days=self.config.hrv_baseline_window_days,
        )
        hrv_score, hrv_baseline_used = self._score_against_baseline(
            current_value=hrv_current,
            baseline_value=hrv_baseline,
            ratio_scale=self.config.hrv_ratio_scale,
            invert=False,
        )

        rhr_current = getattr(current_recovery_row, "resting_hr_bpm", None)
        rhr_baseline = self._mean_valid_values(
            recovery_history_rows,
            attr_name="resting_hr_bpm",
            target_date=target_date,
            window_days=self.config.rhr_baseline_window_days,
        )
        rhr_score, rhr_baseline_used = self._score_against_baseline(
            current_value=rhr_current,
            baseline_value=rhr_baseline,
            ratio_scale=self.config.rhr_ratio_scale,
            invert=True,
        )

        return [
            self._driver_evaluation("sleep", sleep_current, sleep_score, sleep_baseline_used, anchor),
            self._driver_evaluation("hrv", hrv_current, hrv_score, hrv_baseline_used, anchor),
            self._driver_evaluation("rhr", rhr_current, rhr_score, rhr_baseline_used, anchor),
        ]

    def _driver_evaluation(
        self,
        name: str,
        current_value: float | int | None,
        score: float | None,
        baseline_used: bool,
        anchor: float,
    ) -> _DriverEvaluation:
        if current_value is None:
            return _DriverEvaluation(
                name=name,
                present=False,
                baseline_used=False,
                score=None,
                effect="not_used",
            )
        if score is None:
            return _DriverEvaluation(
                name=name,
                present=True,
                baseline_used=False,
                score=anchor,
                effect="neutral",
            )
        if score > anchor + 1:
            effect = "positive"
        elif score < anchor - 1:
            effect = "negative"
        else:
            effect = "neutral"
        return _DriverEvaluation(
            name=name,
            present=True,
            baseline_used=baseline_used,
            score=score,
            effect=effect,
        )

    def _aggregate_primary_score(
        self,
        *,
        evaluations: Sequence[_DriverEvaluation],
    ) -> float | None:
        weighted_total = 0.0
        weight_total = 0.0
        for evaluation in evaluations:
            if not evaluation.present or evaluation.score is None:
                continue
            weight = self.config.driver_weights[evaluation.name]
            weighted_total += evaluation.score * weight
            weight_total += weight
        if weight_total <= 0:
            return None
        return weighted_total / weight_total

    def _resolve_confidence(
        self,
        *,
        completeness_status: str,
        evaluations: Sequence[_DriverEvaluation],
        has_estimated_context: bool,
    ) -> float:
        if completeness_status == "complete":
            confidence = self.config.complete_confidence
        elif completeness_status == "partial":
            confidence = self.config.partial_confidence
        elif completeness_status == "insufficient":
            confidence = self.config.insufficient_confidence
        else:
            confidence = self.config.missing_confidence

        for evaluation in evaluations:
            if evaluation.present and not evaluation.baseline_used:
                confidence -= self.config.missing_baseline_penalty
        if has_estimated_context:
            confidence -= self.config.estimated_context_penalty
        return round(self._clamp(confidence, lower=0, upper=1), 2)

    def _recent_exertion_penalty(
        self,
        *,
        target_date: dt.date,
        load_rows: Sequence[tuple[dt.date, float]],
    ) -> float:
        if not load_rows:
            return 0.0

        by_date = {row_date: load for row_date, load in load_rows}
        history_end = target_date - dt.timedelta(days=1)
        recent_dates = self._date_window(end_date=history_end, days=7)
        reference_dates = self._date_window(end_date=history_end, days=28)
        recent_total = sum(by_date.get(current_date, 0.0) for current_date in recent_dates)
        reference_total = sum(by_date.get(current_date, 0.0) for current_date in reference_dates)
        if reference_total <= 0 or recent_total <= 0:
            return 0.0

        weekly_reference = reference_total / 4
        ratio = recent_total / weekly_reference if weekly_reference > 0 else 0.0
        if ratio <= 1:
            return 0.0

        penalty = (ratio - 1) * self.config.recent_exertion_penalty_scale
        return round(min(penalty, self.config.recent_exertion_penalty_cap), 2)

    def _score_against_baseline(
        self,
        *,
        current_value: float | int | None,
        baseline_value: float | None,
        ratio_scale: float,
        invert: bool,
    ) -> tuple[float | None, bool]:
        if current_value is None:
            return (None, False)
        if baseline_value is None or baseline_value <= 0:
            return (self.config.score_anchor, False)

        delta_ratio = (float(current_value) - baseline_value) / baseline_value
        adjusted_ratio = -delta_ratio if invert else delta_ratio
        score = self.config.score_anchor + (adjusted_ratio * ratio_scale)
        return (self._clamp(score, lower=0, upper=100), True)

    def _sleep_baseline_seconds(
        self,
        sleep_history_rows: Sequence[Any],
        *,
        target_date: dt.date,
    ) -> float | None:
        preferred = self._valid_values(
            sleep_history_rows,
            attr_name="total_sleep_sec",
            target_date=target_date,
            window_days=self.config.sleep_baseline_preferred_days,
        )
        if len(preferred) >= self.config.sleep_baseline_min_observations:
            return sum(preferred) / len(preferred)
        fallback = self._valid_values(
            sleep_history_rows,
            attr_name="total_sleep_sec",
            target_date=target_date,
            window_days=self.config.sleep_baseline_fallback_days,
        )
        if not fallback:
            return None
        return sum(fallback) / len(fallback)

    def _mean_valid_values(
        self,
        rows: Sequence[Any],
        *,
        attr_name: str,
        target_date: dt.date,
        window_days: int,
    ) -> float | None:
        values = self._valid_values(
            rows,
            attr_name=attr_name,
            target_date=target_date,
            window_days=window_days,
        )
        if not values:
            return None
        return sum(values) / len(values)

    def _valid_values(
        self,
        rows: Sequence[Any],
        *,
        attr_name: str,
        target_date: dt.date,
        window_days: int,
    ) -> list[float]:
        if not rows:
            return []
        window_start = target_date - dt.timedelta(days=window_days)
        values: list[float] = []
        for row in rows:
            local_date = getattr(row, "local_date", None)
            if local_date is None or local_date < window_start or local_date >= target_date:
                continue
            raw_value = getattr(row, attr_name, None)
            if raw_value is None:
                continue
            value = float(raw_value)
            if value < 0:
                continue
            values.append(value)
        return values

    def _resolve_completeness_status(self, present_count: int) -> str:
        if present_count >= 3:
            return "complete"
        if present_count == 2:
            return "partial"
        if present_count == 1:
            return "insufficient"
        return "missing"

    def _resolve_label(self, score: int) -> str:
        if score >= self.config.ready_threshold:
            return "Ready"
        if score >= self.config.moderate_threshold:
            return "Moderate"
        return "Recover"

    def _date_window(self, *, end_date: dt.date, days: int) -> list[dt.date]:
        if days <= 0:
            return []
        return [
            end_date - dt.timedelta(days=offset)
            for offset in range(days - 1, -1, -1)
        ]

    def _clamp(self, value: float, *, lower: float, upper: float) -> float:
        return min(max(value, lower), upper)
