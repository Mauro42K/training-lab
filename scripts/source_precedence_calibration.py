#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

START_TOLERANCE_SEC = 120
END_TOLERANCE_SEC = 120
DURATION_TOLERANCE_SEC = 120
MAX_ABS_DISTANCE_DIFF_M = 100.0
MAX_REL_DISTANCE_DIFF = 0.03
MAX_ABS_ENERGY_DIFF_KCAL = 20.0
MAX_REL_ENERGY_DIFF = 0.10
MAX_ABS_HR_DIFF_BPM = 3.0

PAIR_PRIORITIES = [
    ("com.garmin.connect.mobile", "com.strava.stravaride"),
    ("com.rungap.RunGap", "com.strava.stravaride"),
]


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate source precedence on pure source conflicts.")
    parser.add_argument("--database-url-env", default="DATABASE_URL")
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--review-sample-csv", type=Path, required=True)
    parser.add_argument(
        "--sample-per-priority-pair",
        type=int,
        default=20,
        help="Rows per explicitly prioritized pair (default: 20).",
    )
    parser.add_argument(
        "--sample-per-secondary-pair",
        type=int,
        default=10,
        help="Rows per additional top pair (default: 10).",
    )
    parser.add_argument(
        "--secondary-pairs",
        type=int,
        default=3,
        help="Number of non-priority top pairs to include in the sample (default: 3).",
    )
    return parser.parse_args()


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def load_database_url(env_name: str) -> str:
    raw = os.environ.get(env_name)
    if not raw:
        raise SystemExit(f"Missing required environment variable: {env_name}")
    return normalize_database_url(raw)


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


def divergence_reasons(left: WorkoutRow, right: WorkoutRow) -> list[str]:
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


def classify_components(components: list[list[WorkoutRow]]) -> tuple[list[dict[str, Any]], int]:
    clusters: list[dict[str, Any]] = []
    manual_review_total = 0
    for index, component in enumerate(components, start=1):
        reasons: list[str] = []
        if len(component) > 2:
            reasons.append("cluster_size_gt_2")
        elif len(component) == 2:
            left, right = component
            reasons.extend(divergence_reasons(left, right))
            if left.source_bundle_id and right.source_bundle_id and left.source_bundle_id != right.source_bundle_id:
                reasons.append("conflicting_source_bundle_id")

        auto = len(component) == 2 and not reasons
        if not auto:
            manual_review_total += 1

        clusters.append(
            {
                "cluster_id": f"cluster-{index:04d}",
                "cluster_size": len(component),
                "user_id": component[0].user_id,
                "sport": component[0].sport,
                "reasons": sorted(set(reasons)),
                "members": [
                    {
                        "id": row.id,
                        "uuid": row.healthkit_workout_uuid,
                        "source_bundle_id": row.source_bundle_id,
                        "device_name": row.device_name,
                        "start": row.start.astimezone(UTC).isoformat(),
                        "end": row.end.astimezone(UTC).isoformat(),
                        "duration_sec": row.duration_sec,
                        "distance_m": row.distance_m,
                        "energy_kcal": row.energy_kcal,
                        "avg_hr_bpm": row.avg_hr_bpm,
                        "created_at": row.created_at.astimezone(UTC).isoformat(),
                        "updated_at": row.updated_at.astimezone(UTC).isoformat(),
                        "completeness_score": completeness_score(row),
                    }
                    for row in component
                ],
            }
        )
    return clusters, manual_review_total


def pair_key(cluster: dict[str, Any]) -> tuple[str, str]:
    bundles = [member["source_bundle_id"] or "NULL" for member in cluster["members"]]
    return tuple(sorted(bundles))


def top_pairs(clusters: list[dict[str, Any]], manual_review_total: int) -> list[dict[str, Any]]:
    pair_counts = Counter(pair_key(cluster) for cluster in clusters)
    pure_counts = Counter(
        pair_key(cluster)
        for cluster in clusters
        if cluster["cluster_size"] == 2 and cluster["reasons"] == ["conflicting_source_bundle_id"]
    )
    ordered = []
    for pair, count in pair_counts.most_common():
        ordered.append(
            {
                "source_pair": list(pair),
                "cluster_count": count,
                "pct_of_manual_review_clusters": round((count / manual_review_total) * 100, 2)
                if manual_review_total
                else 0.0,
                "pure_size2_source_conflict_clusters": pure_counts[pair],
            }
        )
    return ordered


def choose_review_pairs(summary_pairs: list[dict[str, Any]], secondary_pairs: int) -> list[tuple[str, str]]:
    chosen: list[tuple[str, str]] = []
    available = {tuple(item["source_pair"]) for item in summary_pairs}
    for pair in PAIR_PRIORITIES:
        if pair in available and pair not in chosen:
            chosen.append(pair)
    for item in summary_pairs:
        pair = tuple(item["source_pair"])
        if pair in chosen:
            continue
        if len(chosen) >= len(PAIR_PRIORITIES) + secondary_pairs:
            break
        chosen.append(pair)
    return chosen


def sort_cluster_for_review(cluster: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    left, right = sorted(
        cluster["members"],
        key=lambda member: (
            member["source_bundle_id"] or "",
            member["start"],
            member["id"],
        ),
    )
    return left, right


def write_review_sample(
    path: Path,
    prioritized_clusters: dict[tuple[str, str], list[dict[str, Any]]],
    pair_order: list[tuple[str, str]],
    sample_per_priority_pair: int,
    sample_per_secondary_pair: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "pair_rank",
                "source_pair",
                "cluster_id",
                "sport",
                "user_id",
                "left_id",
                "left_uuid",
                "left_source_bundle_id",
                "left_device_name",
                "left_start",
                "left_end",
                "left_duration_sec",
                "left_distance_m",
                "left_energy_kcal",
                "left_avg_hr_bpm",
                "left_created_at",
                "left_completeness_score",
                "right_id",
                "right_uuid",
                "right_source_bundle_id",
                "right_device_name",
                "right_start",
                "right_end",
                "right_duration_sec",
                "right_distance_m",
                "right_energy_kcal",
                "right_avg_hr_bpm",
                "right_created_at",
                "right_completeness_score",
                "start_diff_sec",
                "end_diff_sec",
                "duration_diff_sec",
                "review_note",
            ],
        )
        writer.writeheader()
        for rank, pair in enumerate(pair_order, start=1):
            clusters = prioritized_clusters[pair]
            limit = sample_per_priority_pair if pair in PAIR_PRIORITIES else sample_per_secondary_pair
            for cluster in clusters[:limit]:
                left, right = sort_cluster_for_review(cluster)
                writer.writerow(
                    {
                        "pair_rank": rank,
                        "source_pair": " vs ".join(pair),
                        "cluster_id": cluster["cluster_id"],
                        "sport": cluster["sport"],
                        "user_id": cluster["user_id"],
                        "left_id": left["id"],
                        "left_uuid": left["uuid"],
                        "left_source_bundle_id": left["source_bundle_id"],
                        "left_device_name": left["device_name"],
                        "left_start": left["start"],
                        "left_end": left["end"],
                        "left_duration_sec": left["duration_sec"],
                        "left_distance_m": left["distance_m"],
                        "left_energy_kcal": left["energy_kcal"],
                        "left_avg_hr_bpm": left["avg_hr_bpm"],
                        "left_created_at": left["created_at"],
                        "left_completeness_score": left["completeness_score"],
                        "right_id": right["id"],
                        "right_uuid": right["uuid"],
                        "right_source_bundle_id": right["source_bundle_id"],
                        "right_device_name": right["device_name"],
                        "right_start": right["start"],
                        "right_end": right["end"],
                        "right_duration_sec": right["duration_sec"],
                        "right_distance_m": right["distance_m"],
                        "right_energy_kcal": right["energy_kcal"],
                        "right_avg_hr_bpm": right["avg_hr_bpm"],
                        "right_created_at": right["created_at"],
                        "right_completeness_score": right["completeness_score"],
                        "start_diff_sec": abs(
                            datetime.fromisoformat(right["start"]) - datetime.fromisoformat(left["start"])
                        ).total_seconds(),
                        "end_diff_sec": abs(
                            datetime.fromisoformat(right["end"]) - datetime.fromisoformat(left["end"])
                        ).total_seconds(),
                        "duration_diff_sec": abs(right["duration_sec"] - left["duration_sec"]),
                        "review_note": "",
                    }
                )


def main() -> int:
    args = parse_args()
    database_url = load_database_url(args.database_url_env)
    workouts = fetch_workouts(database_url)
    clusters, manual_review_total = classify_components(connected_components(workouts, build_adjacency(workouts)))

    pure_source_conflicts = [
        cluster
        for cluster in clusters
        if cluster["cluster_size"] == 2 and cluster["reasons"] == ["conflicting_source_bundle_id"]
    ]
    summary_pairs = top_pairs(pure_source_conflicts, manual_review_total)
    review_pairs = choose_review_pairs(summary_pairs, args.secondary_pairs)
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for cluster in pure_source_conflicts:
        by_pair[pair_key(cluster)].append(cluster)

    for pair_clusters in by_pair.values():
        pair_clusters.sort(key=lambda cluster: cluster["members"][0]["start"])

    summary = {
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "manual_review_clusters_total": manual_review_total,
        "pure_size2_source_conflict_clusters": len(pure_source_conflicts),
        "review_pairs_selected": [list(pair) for pair in review_pairs],
        "top_source_conflicts": summary_pairs,
    }

    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_review_sample(
        args.review_sample_csv,
        by_pair,
        review_pairs,
        args.sample_per_priority_pair,
        args.sample_per_secondary_pair,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
