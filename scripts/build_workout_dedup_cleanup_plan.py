#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC
from pathlib import Path
from typing import Any

from sqlalchemy import select

from api.core.config import get_settings
from api.db.models import Workout
from api.db.session import SessionLocal
from api.repositories.user_repository import get_or_create_default_user
from api.services.local_date import resolve_local_date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a keep/remove cleanup plan from duplicate audit output.")
    parser.add_argument("--audit-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    return parser.parse_args()


def serialize_workout(workout: Workout) -> dict[str, Any]:
    return {
        "id": workout.id,
        "healthkit_workout_uuid": str(workout.healthkit_workout_uuid),
        "sport": workout.sport,
        "start_utc": workout.start.astimezone(UTC).isoformat(),
        "end_utc": workout.end.astimezone(UTC).isoformat(),
        "duration_sec": workout.duration_sec,
        "avg_hr_bpm": workout.avg_hr_bpm,
        "distance_m": workout.distance_m,
        "energy_kcal": workout.energy_kcal,
        "source_bundle_id": workout.source_bundle_id,
        "device_name": workout.device_name,
        "created_at_utc": workout.created_at.astimezone(UTC).isoformat(),
        "updated_at_utc": workout.updated_at.astimezone(UTC).isoformat(),
    }


def main() -> int:
    args = parse_args()
    audit = json.loads(args.audit_json.read_text(encoding="utf-8"))
    eligible_clusters = [cluster for cluster in audit["clusters"] if cluster["auto_cleanup_eligible"]]
    settings = get_settings()

    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        involved_ids = sorted({item_id for cluster in eligible_clusters for item_id in cluster["member_ids"]})
        workouts = db.execute(select(Workout).where(Workout.id.in_(involved_ids))).scalars().all()
        workouts_by_id = {workout.id: workout for workout in workouts}

        plan_items: list[dict[str, Any]] = []
        affected_dates: set[str] = set()

        for cluster in eligible_clusters:
            winner_id = cluster["winner_id"]
            if winner_id is None:
                raise RuntimeError(f"Eligible cluster {cluster['cluster_id']} has no winner_id")

            keep = workouts_by_id[winner_id]
            remove_ids = [item_id for item_id in cluster["member_ids"] if item_id != winner_id]
            remove_rows = [workouts_by_id[item_id] for item_id in remove_ids]
            local_dates = sorted(
                {
                    str(
                        resolve_local_date(
                            instant=row.start,
                            user_timezone=user.timezone,
                            fallback_timezone=settings.trimp_timezone_fallback,
                        )
                    )
                    for row in [keep, *remove_rows]
                }
            )
            affected_dates.update(local_dates)

            plan_items.append(
                {
                    "cluster_id": cluster["cluster_id"],
                    "user_id": cluster["user_id"],
                    "sport": cluster["sport"],
                    "eligibility_basis": cluster["winner_rule"],
                    "reason_basis": (
                        "source_precedence_policy"
                        if cluster["winner_rule"] == "source_precedence_policy"
                        else "baseline_auto_cleanup_rule"
                    ),
                    "affected_local_dates": local_dates,
                    "keep": serialize_workout(keep),
                    "remove": [serialize_workout(row) for row in remove_rows],
                }
            )

        plan = {
            "generated_at_utc": __import__("datetime").datetime.now(tz=UTC).isoformat(),
            "user_id": str(user.id),
            "user_timezone": user.timezone,
            "summary": {
                "eligible_cluster_count": len(plan_items),
                "keep_workout_count": len(plan_items),
                "remove_workout_count": sum(len(item["remove"]) for item in plan_items),
                "affected_local_date_count": len(affected_dates),
                "affected_local_dates": sorted(affected_dates),
                "source_precedence_policy_clusters": sum(
                    1 for item in plan_items if item["eligibility_basis"] == "source_precedence_policy"
                ),
            },
            "items": plan_items,
        }
    finally:
        db.close()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "cluster_id",
                "user_id",
                "sport",
                "eligibility_basis",
                "reason_basis",
                "affected_local_dates",
                "keep_workout_id",
                "keep_uuid",
                "keep_source_bundle_id",
                "remove_workout_ids",
                "remove_uuids",
                "remove_source_bundle_ids",
            ],
        )
        writer.writeheader()
        for item in plan["items"]:
            writer.writerow(
                {
                    "cluster_id": item["cluster_id"],
                    "user_id": item["user_id"],
                    "sport": item["sport"],
                    "eligibility_basis": item["eligibility_basis"],
                    "reason_basis": item["reason_basis"],
                    "affected_local_dates": json.dumps(item["affected_local_dates"]),
                    "keep_workout_id": item["keep"]["id"],
                    "keep_uuid": item["keep"]["healthkit_workout_uuid"],
                    "keep_source_bundle_id": item["keep"]["source_bundle_id"],
                    "remove_workout_ids": json.dumps([row["id"] for row in item["remove"]]),
                    "remove_uuids": json.dumps([row["healthkit_workout_uuid"] for row in item["remove"]]),
                    "remove_source_bundle_ids": json.dumps([row["source_bundle_id"] for row in item["remove"]]),
                }
            )

    print(json.dumps(plan["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
