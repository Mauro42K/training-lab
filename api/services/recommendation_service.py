from api.schemas.daily_domains import (
    CoreMetricsSummaryItem,
    ReadinessExplainabilityItem,
    ReadinessSummaryItem,
    RecommendedState,
    RecommendedTodayItem,
)

LOW_CONFIDENCE_THRESHOLD = 0.70
HIGH_CONFIDENCE_THRESHOLD = 0.80
ELEVATED_EXERTION_RATIO_THRESHOLD = 1.0
SUPPORTED_CORE_METRICS_HISTORY_STATUSES = {"available", "partial"}

READINESS_REASON_TAGS: dict[str, str] = {
    "Recover": "readiness_low",
    "Moderate": "readiness_moderate",
    "Ready": "readiness_high",
}

READINESS_STATE_MAP: dict[str, RecommendedState] = {
    "Recover": "recuperar",
    "Moderate": "suave",
    "Ready": "estable",
}


def compute_recommended_today(
    readiness: ReadinessSummaryItem | None,
    core_metrics: CoreMetricsSummaryItem | None,
) -> RecommendedTodayItem:
    if readiness is None:
        return _no_data_recommendation(confidence=0.0)

    confidence = round(readiness.confidence, 2)
    reason_tags: list[str] = []

    if readiness.completeness_status == "missing" or readiness.label is None:
        return _no_data_recommendation(confidence=confidence)

    if readiness.completeness_status != "complete":
        reason_tags.append("primaries_missing")

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        reason_tags.append("confidence_low")

    readiness_reason_tag = READINESS_REASON_TAGS.get(readiness.label)
    if readiness_reason_tag is not None:
        reason_tags.append(readiness_reason_tag)

    exertion_elevated = _is_recent_exertion_elevated(readiness=readiness, core_metrics=core_metrics)
    if exertion_elevated:
        reason_tags.append("exertion_elevated")

    state = READINESS_STATE_MAP.get(readiness.label, "sin_datos")
    has_mixed_signals = (
        state == "estable"
        and (
            readiness.completeness_status != "complete"
            or "confidence_low" in reason_tags
            or exertion_elevated
        )
    )
    if has_mixed_signals:
        reason_tags.append("signals_mixed")

    if (
        state == "estable"
        and readiness.completeness_status == "complete"
        and confidence >= HIGH_CONFIDENCE_THRESHOLD
        and not exertion_elevated
        and not has_mixed_signals
    ):
        state = "exigente"

    return RecommendedTodayItem(
        state=state,
        confidence=confidence,
        reason_tags=_dedupe_tags(reason_tags),
        guidance_only=True,
    )


def _no_data_recommendation(*, confidence: float) -> RecommendedTodayItem:
    return RecommendedTodayItem(
        state="sin_datos",
        confidence=round(confidence, 2),
        reason_tags=["primaries_missing"],
        guidance_only=True,
    )


def _is_recent_exertion_elevated(
    *,
    readiness: ReadinessSummaryItem,
    core_metrics: CoreMetricsSummaryItem | None,
) -> bool:
    recent_exertion_item = _find_recent_exertion_item(readiness=readiness)
    if recent_exertion_item is not None:
        return recent_exertion_item.effect == "negative"
    return _is_core_metrics_exertion_elevated(core_metrics=core_metrics)


def _find_recent_exertion_item(
    *,
    readiness: ReadinessSummaryItem,
) -> ReadinessExplainabilityItem | None:
    if readiness.explainability is None:
        return None
    for item in readiness.explainability.items:
        if item.key == "recent_exertion":
            return item
    return None


def _is_core_metrics_exertion_elevated(
    *,
    core_metrics: CoreMetricsSummaryItem | None,
) -> bool:
    if core_metrics is None:
        return False
    if core_metrics.history_status not in SUPPORTED_CORE_METRICS_HISTORY_STATUSES:
        return False
    if core_metrics.fitness <= 0:
        return False
    exertion_ratio = core_metrics.fatigue / core_metrics.fitness
    return exertion_ratio > ELEVATED_EXERTION_RATIO_THRESHOLD


def _dedupe_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for tag in tags:
        if tag in seen:
            continue
        seen.add(tag)
        deduped.append(tag)
    return deduped
