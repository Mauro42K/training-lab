#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import bindparam, create_engine, text

START_TOLERANCE_SEC = 120
END_TOLERANCE_SEC = 120
DURATION_TOLERANCE_SEC = 120
MAX_ABS_DISTANCE_DIFF_M = 100.0
MAX_REL_DISTANCE_DIFF = 0.03
MAX_ABS_ENERGY_DIFF_KCAL = 20.0
MAX_REL_ENERGY_DIFF = 0.10
MAX_ABS_HR_DIFF_BPM = 3.0
DEFAULT_DSN_ENV = "DATABASE_URL"


@dataclass(slots=True)
class WorkoutRow:
    id: int
    user_id: str
    healthkit_workout_uuid: str
    sport: str
    start: datetime
    end: datetime
    duration_sec: int
    avg_hr_bpm: float | None
    distance_m: float | None
    energy_kcal: float | None
    source_bundle_id: str | None
    device_name: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class ClusterRecord:
    cluster_id: str
    user_id: str
    sport: str
    member_ids: list[int]
    member_uuids: list[str]
    cluster_size: int
    start_min: str
    start_max: str
    end_min: str
    end_max: str
    auto_cleanup_eligible: bool
    reasons: list[str]
    winner_id: int | None
    winner_rule: str | None
    source_bundle_ids: list[str]
    device_names: list[str]
    completeness_scores: dict[int, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only audit of probable historical duplicate workouts."
    )
    parser.add_argument(
        "--database-url-env",
        default=DEFAULT_DSN_ENV,
        help=f"Environment variable that contains the database URL (default: {DEFAULT_DSN_ENV}).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional JSON file path for the full audit output.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV file path for per-cluster output.",
    )
    parser.add_argument(
        "--policy-json",
        type=Path,
        default=None,
        help="Optional source precedence policy JSON file.",
    )
    return parser.parse_args()


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def load_policy(path: Path | None) -> dict[tuple[str, str], dict[str, Any]]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    pairs = raw.get("pairs", [])
    policy: dict[tuple[str, str], dict[str, Any]] = {}
    for item in pairs:
        left = item["left"]
        right = item["right"]
        policy[tuple(sorted((left, right)))] = item
    return policy


def load_database_url(env_name: str) -> str:
    raw = os.environ.get(env_name)
    if not raw:
        raise SystemExit(f"Missing required environment variable: {env_name}")
    return normalize_database_url(raw)


def to_utc_iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def maybe_float(value: Any) -> float | None:
    return None if value is None else float(value)


def fetch_workouts(database_url: str) -> list[WorkoutRow]:
    engine = create_engine(database_url, future=True)
    stmt = text(
        """
        SELECT
            id,
            user_id::text AS user_id,
            healthkit_workout_uuid::text AS healthkit_workout_uuid,
            sport,
            start,
            "end",
            duration_sec,
            avg_hr_bpm,
            distance_m,
            energy_kcal,
            source_bundle_id,
            device_name,
            created_at,
            updated_at
        FROM workouts
        WHERE is_deleted = false
        ORDER BY user_id, sport, start, id
        """
    )
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        rows = conn.execute(stmt).mappings().all()
    engine.dispose()
    return [
        WorkoutRow(
            id=int(row["id"]),
            user_id=row["user_id"],
            healthkit_workout_uuid=row["healthkit_workout_uuid"],
            sport=row["sport"],
            start=row["start"],
            end=row["end"],
            duration_sec=int(row["duration_sec"]),
            avg_hr_bpm=maybe_float(row["avg_hr_bpm"]),
            distance_m=maybe_float(row["distance_m"]),
            energy_kcal=maybe_float(row["energy_kcal"]),
            source_bundle_id=row["source_bundle_id"],
            device_name=row["device_name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


def fetch_base_coverage(database_url: str) -> dict[str, Any]:
    engine = create_engine(database_url, future=True)
    stmt = text(
        """
        SELECT
            COUNT(*)::bigint AS total_rows,
            COUNT(DISTINCT user_id)::bigint AS distinct_users,
            COUNT(*) FILTER (WHERE is_deleted = true)::bigint AS deleted_rows,
            COUNT(*) FILTER (WHERE source_bundle_id IS NOT NULL)::bigint AS with_source_bundle_id,
            COUNT(*) FILTER (WHERE device_name IS NOT NULL)::bigint AS with_device_name,
            COUNT(*) FILTER (WHERE avg_hr_bpm IS NOT NULL)::bigint AS with_avg_hr_bpm,
            COUNT(*) FILTER (WHERE distance_m IS NOT NULL)::bigint AS with_distance_m,
            COUNT(*) FILTER (WHERE energy_kcal IS NOT NULL)::bigint AS with_energy_kcal
        FROM workouts
        """
    )
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        row = conn.execute(stmt).mappings().one()
    engine.dispose()
    return {key: int(value) for key, value in row.items()}


def build_adjacency(workouts: list[WorkoutRow]) -> dict[int, set[int]]:
    adjacency: dict[int, set[int]] = defaultdict(set)
    grouped: dict[tuple[str, str], list[WorkoutRow]] = defaultdict(list)
    for workout in workouts:
        grouped[(workout.user_id, workout.sport)].append(workout)

    for group_rows in grouped.values():
        group_rows.sort(key=lambda row: (row.start, row.id))
        for index, left in enumerate(group_rows):
            for right in group_rows[index + 1 :]:
                if (right.start - left.start).total_seconds() > START_TOLERANCE_SEC:
                    break
                if left.healthkit_workout_uuid == right.healthkit_workout_uuid:
                    continue
                end_close = abs((right.end - left.end).total_seconds()) <= END_TOLERANCE_SEC
                duration_close = abs(right.duration_sec - left.duration_sec) <= DURATION_TOLERANCE_SEC
                if end_close or duration_close:
                    adjacency[left.id].add(right.id)
                    adjacency[right.id].add(left.id)
    return adjacency


def connected_components(workouts: list[WorkoutRow], adjacency: dict[int, set[int]]) -> list[list[WorkoutRow]]:
    workout_by_id = {workout.id: workout for workout in workouts}
    seen: set[int] = set()
    components: list[list[WorkoutRow]] = []
    for workout_id, neighbors in adjacency.items():
        if workout_id in seen or not neighbors:
            continue
        stack = [workout_id]
        component_ids: list[int] = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component_ids.append(current)
            stack.extend(adjacency[current] - seen)
        components.append(sorted((workout_by_id[item_id] for item_id in component_ids), key=lambda row: (row.start, row.id)))
    return components


def relative_threshold(value_a: float, value_b: float, *, abs_cap: float, rel_cap: float) -> float:
    return max(abs_cap, max(abs(value_a), abs(value_b)) * rel_cap)


def metric_diverges(left: WorkoutRow, right: WorkoutRow) -> list[str]:
    reasons: list[str] = []
    if left.distance_m is not None and right.distance_m is not None:
        if abs(left.distance_m - right.distance_m) > relative_threshold(
            left.distance_m,
            right.distance_m,
            abs_cap=MAX_ABS_DISTANCE_DIFF_M,
            rel_cap=MAX_REL_DISTANCE_DIFF,
        ):
            reasons.append("distance_divergence")
    if left.energy_kcal is not None and right.energy_kcal is not None:
        if abs(left.energy_kcal - right.energy_kcal) > relative_threshold(
            left.energy_kcal,
            right.energy_kcal,
            abs_cap=MAX_ABS_ENERGY_DIFF_KCAL,
            rel_cap=MAX_REL_ENERGY_DIFF,
        ):
            reasons.append("energy_divergence")
    if left.avg_hr_bpm is not None and right.avg_hr_bpm is not None:
        if abs(left.avg_hr_bpm - right.avg_hr_bpm) > MAX_ABS_HR_DIFF_BPM:
            reasons.append("hr_divergence")
    return reasons


def completeness_score(workout: WorkoutRow) -> int:
    return int(workout.source_bundle_id is not None) + int(workout.device_name is not None) + int(
        workout.avg_hr_bpm is not None
    ) + int(workout.distance_m is not None) + int(workout.energy_kcal is not None)


def choose_winner(
    component: list[WorkoutRow],
    *,
    source_policy: dict[tuple[str, str], dict[str, Any]],
) -> tuple[int | None, str | None, list[str]]:
    reasons: list[str] = []
    if len(component) != 2:
        return (None, None, ["cluster_size_gt_2"])

    left, right = component
    reasons.extend(metric_diverges(left, right))
    if left.source_bundle_id and right.source_bundle_id and left.source_bundle_id != right.source_bundle_id:
        pair = tuple(sorted((left.source_bundle_id, right.source_bundle_id)))
        policy_item = source_policy.get(pair)
        if policy_item is not None and policy_item.get("preferred") in {left.source_bundle_id, right.source_bundle_id}:
            preferred = policy_item["preferred"]
            winner_id = left.id if left.source_bundle_id == preferred else right.id
            return (winner_id, "source_precedence_policy", sorted(set(reasons)))
        reasons.append("conflicting_source_bundle_id")
        return (None, None, sorted(set(reasons)))

    if left.source_bundle_id and not right.source_bundle_id:
        return (left.id, "source_bundle_id_present", sorted(set(reasons)))
    if right.source_bundle_id and not left.source_bundle_id:
        return (right.id, "source_bundle_id_present", sorted(set(reasons)))

    if left.device_name and not right.device_name:
        return (left.id, "device_name_present", sorted(set(reasons)))
    if right.device_name and not left.device_name:
        return (right.id, "device_name_present", sorted(set(reasons)))

    left_score = completeness_score(left)
    right_score = completeness_score(right)
    if left_score > right_score:
        return (left.id, "metadata_completeness", sorted(set(reasons)))
    if right_score > left_score:
        return (right.id, "metadata_completeness", sorted(set(reasons)))

    left_created = left.created_at.astimezone(UTC)
    right_created = right.created_at.astimezone(UTC)
    if left_created < right_created:
        return (left.id, "oldest_created_at_tiebreaker", sorted(set(reasons)))
    if right_created < left_created:
        return (right.id, "oldest_created_at_tiebreaker", sorted(set(reasons)))

    winner = left.id if left.id < right.id else right.id
    return (winner, "lowest_id_tiebreaker", sorted(set(reasons)))


def classify_components(
    components: list[list[WorkoutRow]],
    *,
    source_policy: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[ClusterRecord], Counter[str]]:
    records: list[ClusterRecord] = []
    exclusion_reasons: Counter[str] = Counter()

    for index, component in enumerate(components, start=1):
        winner_id, winner_rule, preexisting_reasons = choose_winner(
            component,
            source_policy=source_policy,
        )
        reasons = list(preexisting_reasons)
        if len(component) == 2 and winner_id is not None and not reasons:
            auto_cleanup_eligible = True
        else:
            auto_cleanup_eligible = False
            if not reasons:
                reasons.append("manual_review_required")
        for reason in reasons:
            exclusion_reasons[reason] += 1

        records.append(
            ClusterRecord(
                cluster_id=f"cluster-{index:04d}",
                user_id=component[0].user_id,
                sport=component[0].sport,
                member_ids=[row.id for row in component],
                member_uuids=[row.healthkit_workout_uuid for row in component],
                cluster_size=len(component),
                start_min=to_utc_iso(min(row.start for row in component)),
                start_max=to_utc_iso(max(row.start for row in component)),
                end_min=to_utc_iso(min(row.end for row in component)),
                end_max=to_utc_iso(max(row.end for row in component)),
                auto_cleanup_eligible=auto_cleanup_eligible,
                reasons=sorted(set(reasons)),
                winner_id=winner_id if auto_cleanup_eligible else None,
                winner_rule=winner_rule if auto_cleanup_eligible else None,
                source_bundle_ids=sorted({row.source_bundle_id for row in component if row.source_bundle_id}),
                device_names=sorted({row.device_name for row in component if row.device_name}),
                completeness_scores={row.id: completeness_score(row) for row in component},
            )
        )

    return records, exclusion_reasons


def summarize_source_patterns(clusters: list[ClusterRecord], workout_lookup: dict[int, WorkoutRow]) -> list[dict[str, Any]]:
    pair_counts: Counter[tuple[str, str]] = Counter()
    for cluster in clusters:
        bundles = []
        for workout_id in cluster.member_ids:
            bundle = workout_lookup[workout_id].source_bundle_id or "NULL"
            bundles.append(bundle)
        pair_counts[tuple(sorted(bundles))] += 1
    return [
        {"source_bundle_pattern": list(pattern), "cluster_count": count}
        for pattern, count in pair_counts.most_common(10)
    ]


def detect_cross_sport_near_matches(workouts: list[WorkoutRow]) -> list[dict[str, Any]]:
    grouped: dict[str, list[WorkoutRow]] = defaultdict(list)
    for workout in workouts:
        grouped[workout.user_id].append(workout)

    findings: list[dict[str, Any]] = []
    for user_rows in grouped.values():
        user_rows.sort(key=lambda row: (row.start, row.id))
        for index, left in enumerate(user_rows):
            for right in user_rows[index + 1 :]:
                if (right.start - left.start).total_seconds() > START_TOLERANCE_SEC:
                    break
                if left.sport == right.sport:
                    continue
                end_close = abs((right.end - left.end).total_seconds()) <= END_TOLERANCE_SEC
                duration_close = abs(right.duration_sec - left.duration_sec) <= DURATION_TOLERANCE_SEC
                if end_close or duration_close:
                    findings.append(
                        {
                            "user_id": left.user_id,
                            "left_id": left.id,
                            "right_id": right.id,
                            "left_sport": left.sport,
                            "right_sport": right.sport,
                            "start_diff_sec": abs((right.start - left.start).total_seconds()),
                            "end_diff_sec": abs((right.end - left.end).total_seconds()),
                            "duration_diff_sec": abs(right.duration_sec - left.duration_sec),
                        }
                    )
    return findings


def fetch_downstream_counts(database_url: str, candidate_ids: list[int], user_date_pairs: set[tuple[str, str]]) -> dict[str, Any]:
    if not candidate_ids:
        return {
            "workout_load_rows": 0,
            "workout_load_distinct_dates": 0,
            "daily_load_rows": 0,
            "daily_load_distinct_user_dates": 0,
            "legacy_daily_distinct_user_dates": 0,
            "daily_recovery_rows": 0,
        }

    engine = create_engine(database_url, future=True)
    ids_stmt = bindparam("candidate_ids", expanding=True)
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))

        workout_load_rows = conn.execute(
            text(
                """
                SELECT local_date
                FROM workout_load
                WHERE workout_id IN :candidate_ids
                """
            ).bindparams(ids_stmt),
            {"candidate_ids": candidate_ids},
        ).mappings().all()

        affected_pairs = list(user_date_pairs)
        if affected_pairs:
            user_ids = sorted({user_id for user_id, _ in affected_pairs})
            local_dates = sorted({local_date for _, local_date in affected_pairs})
            user_ids_stmt = bindparam("user_ids", expanding=True)
            local_dates_stmt = bindparam("local_dates", expanding=True)

            daily_load_rows = conn.execute(
                text(
                    """
                    SELECT user_id::text AS user_id, date::text AS local_date
                    FROM daily_load
                    WHERE user_id IN :user_ids
                      AND date IN :local_dates
                    """
                ).bindparams(user_ids_stmt, local_dates_stmt),
                {"user_ids": user_ids, "local_dates": local_dates},
            ).mappings().all()

            recovery_rows = conn.execute(
                text(
                    """
                    SELECT user_id::text AS user_id, local_date::text AS local_date
                    FROM daily_recovery
                    WHERE user_id IN :user_ids
                      AND local_date IN :local_dates
                    """
                ).bindparams(user_ids_stmt, local_dates_stmt),
                {"user_ids": user_ids, "local_dates": local_dates},
            ).mappings().all()
        else:
            daily_load_rows = []
            recovery_rows = []

    engine.dispose()
    affected_pair_set = set(affected_pairs)
    daily_load_filtered = [
        row
        for row in daily_load_rows
        if (row["user_id"], row["local_date"]) in affected_pair_set
    ]
    recovery_filtered = [
        row
        for row in recovery_rows
        if (row["user_id"], row["local_date"]) in affected_pair_set
    ]
    return {
        "workout_load_rows": len(workout_load_rows),
        "workout_load_distinct_dates": len({str(row["local_date"]) for row in workout_load_rows}),
        "daily_load_rows": len(daily_load_filtered),
        "daily_load_distinct_user_dates": len({(row["user_id"], row["local_date"]) for row in daily_load_filtered}),
        "legacy_daily_distinct_user_dates": len(user_date_pairs),
        "daily_recovery_rows": len(recovery_filtered),
    }


def build_report(
    workouts: list[WorkoutRow],
    coverage: dict[str, Any],
    *,
    source_policy: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    adjacency = build_adjacency(workouts)
    components = connected_components(workouts, adjacency)
    clusters, exclusion_reasons = classify_components(components, source_policy=source_policy)
    workout_lookup = {workout.id: workout for workout in workouts}

    candidate_ids = sorted({item_id for cluster in clusters for item_id in cluster.member_ids})
    user_date_pairs = {
        (workout_lookup[item_id].user_id, workout_lookup[item_id].start.date().isoformat()) for item_id in candidate_ids
    }
    auto_candidate_ids = sorted(
        {
            item_id
            for cluster in clusters
            if cluster.auto_cleanup_eligible
            for item_id in cluster.member_ids
        }
    )
    auto_user_date_pairs = {
        (workout_lookup[item_id].user_id, workout_lookup[item_id].start.date().isoformat())
        for item_id in auto_candidate_ids
    }
    cross_sport_findings = detect_cross_sport_near_matches(workouts)

    report = {
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "audit_parameters": {
            "start_tolerance_sec": START_TOLERANCE_SEC,
            "end_tolerance_sec": END_TOLERANCE_SEC,
            "duration_tolerance_sec": DURATION_TOLERANCE_SEC,
            "distance_abs_threshold_m": MAX_ABS_DISTANCE_DIFF_M,
            "distance_rel_threshold": MAX_REL_DISTANCE_DIFF,
            "energy_abs_threshold_kcal": MAX_ABS_ENERGY_DIFF_KCAL,
            "energy_rel_threshold": MAX_REL_ENERGY_DIFF,
            "avg_hr_abs_threshold_bpm": MAX_ABS_HR_DIFF_BPM,
            "notes": [
                "probable duplicate cluster does not imply delete candidate",
                "oldest created_at is only a stable technical tiebreaker, not a semantic quality signal",
                "distance/energy/hr thresholds are auditable defaults for this report, not eternal truth",
            ],
        },
        "source_precedence_policy": {
            "enabled": bool(source_policy),
            "pair_count": len(source_policy),
            "pairs": [
                {
                    "pair": list(pair),
                    "preferred": item.get("preferred"),
                    "confidence": item.get("confidence"),
                }
                for pair, item in sorted(source_policy.items())
            ],
        },
        "coverage": {
            **coverage,
            "active_rows": coverage["total_rows"] - coverage["deleted_rows"],
            "source_bundle_coverage_ratio": round(
                coverage["with_source_bundle_id"] / coverage["total_rows"], 4
            )
            if coverage["total_rows"]
            else 0.0,
            "device_name_coverage_ratio": round(coverage["with_device_name"] / coverage["total_rows"], 4)
            if coverage["total_rows"]
            else 0.0,
        },
        "probable_clusters_summary": {
            "users_affected": len({cluster.user_id for cluster in clusters}),
            "candidate_clusters": len(clusters),
            "candidate_rows": len(candidate_ids),
            "auto_cleanup_eligible_clusters": sum(1 for cluster in clusters if cluster.auto_cleanup_eligible),
            "auto_cleanup_eligible_rows": len(auto_candidate_ids),
            "manual_review_clusters": sum(1 for cluster in clusters if not cluster.auto_cleanup_eligible),
            "manual_review_rows": len(candidate_ids) - len(auto_candidate_ids),
            "source_policy_eligible_clusters": sum(
                1 for cluster in clusters if cluster.auto_cleanup_eligible and cluster.winner_rule == "source_precedence_policy"
            ),
            "source_policy_eligible_rows": sum(
                cluster.cluster_size
                for cluster in clusters
                if cluster.auto_cleanup_eligible and cluster.winner_rule == "source_precedence_policy"
            ),
            "cluster_size_distribution": dict(Counter(cluster.cluster_size for cluster in clusters)),
            "date_range_utc": {
                "start_min": min((cluster.start_min for cluster in clusters), default=None),
                "start_max": max((cluster.start_max for cluster in clusters), default=None),
            },
            "sports_distribution": dict(Counter(cluster.sport for cluster in clusters)),
            "manual_review_reasons": dict(exclusion_reasons),
        },
        "sport_consistency_audit": {
            "cross_sport_near_match_pairs": len(cross_sport_findings),
            "sample_pairs": cross_sport_findings[:10],
        },
        "source_identity_patterns": summarize_source_patterns(clusters, workout_lookup),
        "clusters": [asdict(cluster) for cluster in clusters],
        "top_clusters": [asdict(cluster) for cluster in clusters[:25]],
        "candidate_workout_ids": candidate_ids,
        "auto_cleanup_eligible_workout_ids": auto_candidate_ids,
        "user_date_pairs": sorted(user_date_pairs),
        "auto_cleanup_user_date_pairs": sorted(auto_user_date_pairs),
    }
    return report


def write_csv(path: Path, clusters: list[ClusterRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "cluster_id",
                "user_id",
                "sport",
                "cluster_size",
                "member_ids",
                "member_uuids",
                "auto_cleanup_eligible",
                "reasons",
                "winner_id",
                "winner_rule",
                "source_bundle_ids",
                "device_names",
                "start_min",
                "start_max",
                "end_min",
                "end_max",
            ],
        )
        writer.writeheader()
        for cluster in clusters:
            writer.writerow(
                {
                    "cluster_id": cluster.cluster_id,
                    "user_id": cluster.user_id,
                    "sport": cluster.sport,
                    "cluster_size": cluster.cluster_size,
                    "member_ids": json.dumps(cluster.member_ids),
                    "member_uuids": json.dumps(cluster.member_uuids),
                    "auto_cleanup_eligible": cluster.auto_cleanup_eligible,
                    "reasons": json.dumps(cluster.reasons),
                    "winner_id": cluster.winner_id,
                    "winner_rule": cluster.winner_rule,
                    "source_bundle_ids": json.dumps(cluster.source_bundle_ids),
                    "device_names": json.dumps(cluster.device_names),
                    "start_min": cluster.start_min,
                    "start_max": cluster.start_max,
                    "end_min": cluster.end_min,
                    "end_max": cluster.end_max,
                }
            )


def main() -> int:
    args = parse_args()
    database_url = load_database_url(args.database_url_env)
    source_policy = load_policy(args.policy_json)
    workouts = fetch_workouts(database_url)
    coverage = fetch_base_coverage(database_url)
    report = build_report(workouts, coverage, source_policy=source_policy)

    downstream_all = fetch_downstream_counts(
        database_url,
        report["candidate_workout_ids"],
        set(tuple(item) for item in report["user_date_pairs"]),
    )
    downstream_auto = fetch_downstream_counts(
        database_url,
        report["auto_cleanup_eligible_workout_ids"],
        set(tuple(item) for item in report["auto_cleanup_user_date_pairs"]),
    )
    report["blast_radius"] = {
        "all_probable_clusters": downstream_all,
        "auto_cleanup_eligible_only": downstream_auto,
    }

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    if args.output_csv is not None:
        csv_clusters = [
            ClusterRecord(**cluster_data)  # type: ignore[arg-type]
            for cluster_data in report["clusters"]
        ]
        write_csv(args.output_csv, csv_clusters)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
