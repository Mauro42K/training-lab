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
from api.schemas.daily_domains import (
    ReadinessExplainability,
    ReadinessExplainabilityItem,
    ReadinessSummaryItem,
    ReadinessTraceInput,
)


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
class _ExplainabilityEvaluation:
    key: str
    role: str
    status: str
    present: bool
    baseline_used: bool
    display_value: str | None
    display_unit: str | None
    baseline_value: str | None
    baseline_unit: str | None
    short_reason: str
    score: float | None
    effect: str


@dataclass(frozen=True)
class _RecentExertionSummary:
    recent_total: float
    weekly_reference: float | None
    penalty: float
    is_baseline_sufficient: bool


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
        recent_exertion_summary = self._recent_exertion_summary(
            target_date=target_date,
            load_rows=load_rows,
        )
        explainability_items = self._build_explainability_items(
            target_date=target_date,
            current_recovery_row=current_recovery_row,
            recovery_history_rows=recovery_history_rows,
            sleep_history_rows=sleep_history_rows,
            load_context_by_date=load_context_by_date,
            recent_exertion_summary=recent_exertion_summary,
        )
        primary_evaluations = [
            evaluation for evaluation in explainability_items if evaluation.role == "primary_driver"
        ]
        inputs_present = [evaluation.key for evaluation in primary_evaluations if evaluation.present]
        inputs_missing = [evaluation.key for evaluation in primary_evaluations if not evaluation.present]
        completeness_status = self._resolve_completeness_status(len(inputs_present))
        has_estimated_context = any(
            context.has_estimated_inputs for context in load_context_by_date.values()
        )

        raw_score = self._aggregate_primary_score(evaluations=primary_evaluations)
        score = None
        label = None
        context_penalty = recent_exertion_summary.penalty
        if raw_score is not None:
            if completeness_status == "insufficient":
                raw_score = self.config.score_anchor + (
                    (raw_score - self.config.score_anchor) * self.config.insufficient_score_regression
                )
            score = int(round(self._clamp(raw_score - context_penalty, lower=0, upper=100)))
            label = self._resolve_label(score)

        confidence = self._resolve_confidence(
            completeness_status=completeness_status,
            evaluations=primary_evaluations,
            has_estimated_context=has_estimated_context,
        )

        trace_summary = [
            ReadinessTraceInput(
                name=evaluation.key,
                role="primary" if evaluation.role == "primary_driver" else "context",
                present=evaluation.present,
                baseline_used=evaluation.baseline_used,
                effect=evaluation.effect,  # type: ignore[arg-type]
            )
            for evaluation in explainability_items
        ]

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
            explainability=ReadinessExplainability(
                completeness_status=completeness_status,
                confidence=confidence,
                model_version=self.config.model_version,
                items=[
                    ReadinessExplainabilityItem(
                        key=evaluation.key,
                        role=evaluation.role,  # type: ignore[arg-type]
                        status=evaluation.status,  # type: ignore[arg-type]
                        effect=evaluation.effect,  # type: ignore[arg-type]
                        display_value=evaluation.display_value,
                        display_unit=evaluation.display_unit,
                        baseline_value=evaluation.baseline_value,
                        baseline_unit=evaluation.baseline_unit,
                        is_baseline_sufficient=evaluation.baseline_used,
                        short_reason=evaluation.short_reason,
                    )
                    for evaluation in explainability_items
                ],
            ),
        )

    def _build_explainability_items(
        self,
        *,
        target_date: dt.date,
        current_recovery_row: Any | None,
        recovery_history_rows: Sequence[Any],
        sleep_history_rows: Sequence[Any],
        load_context_by_date: dict[dt.date, DailyLoadContext],
        recent_exertion_summary: _RecentExertionSummary,
    ) -> list[_ExplainabilityEvaluation]:
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
            self._primary_explainability_evaluation(
                key="sleep",
                current_value=sleep_current,
                baseline_value=sleep_baseline,
                score=sleep_score,
                baseline_used=sleep_baseline_used,
                anchor=anchor,
            ),
            self._primary_explainability_evaluation(
                key="hrv",
                current_value=hrv_current,
                baseline_value=hrv_baseline,
                score=hrv_score,
                baseline_used=hrv_baseline_used,
                anchor=anchor,
            ),
            self._primary_explainability_evaluation(
                key="rhr",
                current_value=rhr_current,
                baseline_value=rhr_baseline,
                score=rhr_score,
                baseline_used=rhr_baseline_used,
                anchor=anchor,
            ),
            self._recent_exertion_explainability_evaluation(
                load_context_by_date=load_context_by_date,
                recent_exertion_summary=recent_exertion_summary,
            ),
        ]

    def _primary_explainability_evaluation(
        self,
        *,
        key: str,
        current_value: float | int | None,
        baseline_value: float | None,
        score: float | None,
        baseline_used: bool,
        anchor: float,
    ) -> _ExplainabilityEvaluation:
        if current_value is None:
            return _ExplainabilityEvaluation(
                key=key,
                role="primary_driver",
                status="missing",
                present=False,
                baseline_used=False,
                display_value=None,
                display_unit=self._display_unit(key),
                baseline_value=self._format_value(key, baseline_value),
                baseline_unit=self._baseline_unit(key),
                short_reason=self._short_reason(
                    key=key,
                    status="missing",
                    effect="not_used",
                    baseline_used=False,
                ),
                score=None,
                effect="not_used",
            )
        if score is None:
            return _ExplainabilityEvaluation(
                key=key,
                role="primary_driver",
                status="measured",
                present=True,
                baseline_used=False,
                display_value=self._format_value(key, current_value),
                display_unit=self._display_unit(key),
                baseline_value=self._format_value(key, baseline_value),
                baseline_unit=self._baseline_unit(key),
                short_reason=self._short_reason(
                    key=key,
                    status="measured",
                    effect="neutral",
                    baseline_used=False,
                ),
                score=anchor,
                effect="neutral",
            )
        if score > anchor + 1:
            effect = "positive"
        elif score < anchor - 1:
            effect = "negative"
        else:
            effect = "neutral"
        return _ExplainabilityEvaluation(
            key=key,
            role="primary_driver",
            status="measured",
            present=True,
            baseline_used=baseline_used,
            display_value=self._format_value(key, current_value),
            display_unit=self._display_unit(key),
            baseline_value=self._format_value(key, baseline_value),
            baseline_unit=self._baseline_unit(key),
            short_reason=self._short_reason(
                key=key,
                status="measured",
                effect=effect,
                baseline_used=baseline_used,
            ),
            score=score,
            effect=effect,
        )

    def _recent_exertion_explainability_evaluation(
        self,
        *,
        load_context_by_date: dict[dt.date, DailyLoadContext],
        recent_exertion_summary: _RecentExertionSummary,
    ) -> _ExplainabilityEvaluation:
        present = any(context.load_present for context in load_context_by_date.values())
        has_estimated_inputs = any(
            context.load_present and context.has_estimated_inputs
            for context in load_context_by_date.values()
        )
        if not present:
            return _ExplainabilityEvaluation(
                key="recent_exertion",
                role="secondary_context",
                status="missing",
                present=False,
                baseline_used=False,
                display_value=None,
                display_unit="load",
                baseline_value=None,
                baseline_unit="load",
                short_reason=self._short_reason(
                    key="recent_exertion",
                    status="missing",
                    effect="not_used",
                    baseline_used=False,
                ),
                score=None,
                effect="not_used",
            )

        status = "estimated" if has_estimated_inputs else "measured"
        baseline_used = recent_exertion_summary.is_baseline_sufficient
        if recent_exertion_summary.penalty > 0:
            effect = "negative"
        elif baseline_used:
            effect = "neutral"
        else:
            effect = "not_used"

        return _ExplainabilityEvaluation(
            key="recent_exertion",
            role="secondary_context",
            status=status,
            present=True,
            baseline_used=baseline_used,
            display_value=self._format_value("recent_exertion", recent_exertion_summary.recent_total),
            display_unit="load",
            baseline_value=self._format_value("recent_exertion", recent_exertion_summary.weekly_reference),
            baseline_unit="load",
            short_reason=self._short_reason(
                key="recent_exertion",
                status=status,
                effect=effect,
                baseline_used=baseline_used,
            ),
            score=None,
            effect=effect,
        )

    def _aggregate_primary_score(
        self,
        *,
        evaluations: Sequence[_ExplainabilityEvaluation],
    ) -> float | None:
        weighted_total = 0.0
        weight_total = 0.0
        for evaluation in evaluations:
            if not evaluation.present or evaluation.score is None:
                continue
            weight = self.config.driver_weights[evaluation.key]
            weighted_total += evaluation.score * weight
            weight_total += weight
        if weight_total <= 0:
            return None
        return weighted_total / weight_total

    def _resolve_confidence(
        self,
        *,
        completeness_status: str,
        evaluations: Sequence[_ExplainabilityEvaluation],
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

    def _recent_exertion_summary(
        self,
        *,
        target_date: dt.date,
        load_rows: Sequence[tuple[dt.date, float]],
    ) -> _RecentExertionSummary:
        if not load_rows:
            return _RecentExertionSummary(
                recent_total=0.0,
                weekly_reference=None,
                penalty=0.0,
                is_baseline_sufficient=False,
            )

        by_date = {row_date: load for row_date, load in load_rows}
        history_end = target_date - dt.timedelta(days=1)
        recent_dates = self._date_window(end_date=history_end, days=7)
        reference_dates = self._date_window(end_date=history_end, days=28)
        recent_total = sum(by_date.get(current_date, 0.0) for current_date in recent_dates)
        reference_total = sum(by_date.get(current_date, 0.0) for current_date in reference_dates)
        if reference_total <= 0 or recent_total <= 0:
            return _RecentExertionSummary(
                recent_total=recent_total,
                weekly_reference=(reference_total / 4) if reference_total > 0 else None,
                penalty=0.0,
                is_baseline_sufficient=False,
            )

        weekly_reference = reference_total / 4
        ratio = recent_total / weekly_reference if weekly_reference > 0 else 0.0
        if ratio <= 1:
            return _RecentExertionSummary(
                recent_total=recent_total,
                weekly_reference=weekly_reference,
                penalty=0.0,
                is_baseline_sufficient=True,
            )

        penalty = (ratio - 1) * self.config.recent_exertion_penalty_scale
        return _RecentExertionSummary(
            recent_total=recent_total,
            weekly_reference=weekly_reference,
            penalty=round(min(penalty, self.config.recent_exertion_penalty_cap), 2),
            is_baseline_sufficient=True,
        )

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

    def _format_value(self, key: str, value: float | int | None) -> str | None:
        if value is None:
            return None
        if key == "sleep":
            total_minutes = int(round(float(value) / 60))
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"{hours}h"
            return f"{hours}h {minutes}m"
        return str(int(round(float(value))))

    def _display_unit(self, key: str) -> str | None:
        if key == "hrv":
            return "ms"
        if key == "rhr":
            return "bpm"
        if key == "recent_exertion":
            return "load"
        return None

    def _baseline_unit(self, key: str) -> str | None:
        return self._display_unit(key)

    def _short_reason(
        self,
        *,
        key: str,
        status: str,
        effect: str,
        baseline_used: bool,
    ) -> str:
        if status == "missing":
            return {
                "sleep": "Sleep missing today.",
                "hrv": "HRV missing today.",
                "rhr": "RHR missing today.",
                "recent_exertion": "Exertion unavailable.",
            }[key]

        if not baseline_used:
            return {
                "sleep": "Sleep is still finding usual range.",
                "hrv": "HRV baseline is still building.",
                "rhr": "RHR baseline is still building.",
                "recent_exertion": "Exertion context is still building.",
            }[key]

        if key == "sleep":
            return {
                "positive": "Sleep ran above usual.",
                "neutral": "Sleep held near usual.",
                "negative": "Sleep ran below usual.",
                "not_used": "Sleep held near usual.",
            }[effect]
        if key == "hrv":
            return {
                "positive": "HRV rose above usual.",
                "neutral": "HRV held near baseline.",
                "negative": "HRV dipped below usual.",
                "not_used": "HRV held near baseline.",
            }[effect]
        if key == "rhr":
            return {
                "positive": "RHR stayed below usual.",
                "neutral": "RHR held near baseline.",
                "negative": "RHR ran above usual.",
                "not_used": "RHR held near baseline.",
            }[effect]
        return {
            "positive": "Exertion stayed light.",
            "neutral": "Exertion stayed in range.",
            "negative": "Exertion stayed elevated.",
            "not_used": "Exertion stayed in range.",
        }[effect]

    def _date_window(self, *, end_date: dt.date, days: int) -> list[dt.date]:
        if days <= 0:
            return []
        return [
            end_date - dt.timedelta(days=offset)
            for offset in range(days - 1, -1, -1)
        ]

    def _clamp(self, value: float, *, lower: float, upper: float) -> float:
        return min(max(value, lower), upper)
