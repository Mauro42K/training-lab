#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from datetime import UTC
from pathlib import Path

from sqlalchemy import select

from api.db.models import DailyLoad, DailyRecovery, Workout, WorkoutLoad
from api.db.session import SessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a before/after snapshot for a workout dedupe cleanup plan.")
    parser.add_argument("--plan-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--label", default="snapshot")
    return parser.parse_args()


def serialize_workout(workout: Workout) -> dict:
    return {
        "id": workout.id,
        "user_id": str(workout.user_id),
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
        "is_deleted": workout.is_deleted,
    }


def serialize_workout_load(row: WorkoutLoad) -> dict:
    return {
        "id": row.id,
        "workout_id": row.workout_id,
        "user_id": str(row.user_id),
        "local_date": str(row.local_date),
        "sport": row.sport,
        "trimp_value": row.trimp_value,
        "trimp_source": row.trimp_source,
        "trimp_model_version": row.trimp_model_version,
    }


def serialize_daily_load(row: DailyLoad) -> dict:
    return {
        "id": row.id,
        "user_id": str(row.user_id),
        "date": str(row.date),
        "sport_filter": row.sport_filter,
        "trimp_total": row.trimp_total,
        "sessions_count": row.sessions_count,
        "trimp_model_version": row.trimp_model_version,
    }


def serialize_daily_recovery(row: DailyRecovery) -> dict:
    return {
        "id": row.id,
        "user_id": str(row.user_id),
        "local_date": str(row.local_date),
        "completeness": row.completeness,
        "sleep_present": row.sleep_present,
        "hrv_present": row.hrv_present,
        "rhr_present": row.rhr_present,
        "activity_present": row.activity_present,
        "load_present": row.load_present,
    }


def main() -> int:
    args = parse_args()
    plan = json.loads(args.plan_json.read_text(encoding="utf-8"))
    user_id = plan["user_id"]
    keep_ids = [item["keep"]["id"] for item in plan["items"]]
    remove_ids = [row["id"] for item in plan["items"] for row in item["remove"]]
    involved_ids = sorted(set(keep_ids + remove_ids))
    affected_dates = sorted({date.fromisoformat(item) for item in plan["summary"]["affected_local_dates"]})

    db = SessionLocal()
    try:
        workouts = db.execute(select(Workout).where(Workout.id.in_(involved_ids)).order_by(Workout.id.asc())).scalars().all()
        workout_load_rows = (
            db.execute(select(WorkoutLoad).where(WorkoutLoad.workout_id.in_(involved_ids)).order_by(WorkoutLoad.id.asc()))
            .scalars()
            .all()
        )
        daily_load_rows = (
            db.execute(
                select(DailyLoad)
                .where(
                    DailyLoad.user_id == user_id,
                    DailyLoad.date.in_(affected_dates),
                )
                .order_by(DailyLoad.date.asc(), DailyLoad.sport_filter.asc())
            )
            .scalars()
            .all()
        )
        daily_recovery_rows = (
            db.execute(
                select(DailyRecovery)
                .where(
                    DailyRecovery.user_id == user_id,
                    DailyRecovery.local_date.in_(affected_dates),
                )
                .order_by(DailyRecovery.local_date.asc())
            )
            .scalars()
            .all()
        )
    finally:
        db.close()

    snapshot = {
        "label": args.label,
        "generated_at_utc": __import__("datetime").datetime.now(tz=UTC).isoformat(),
        "user_id": user_id,
        "counts": {
            "keep_ids": len(keep_ids),
            "remove_ids": len(remove_ids),
            "workouts_found": len(workouts),
            "workout_load_rows": len(workout_load_rows),
            "daily_load_rows": len(daily_load_rows),
            "daily_recovery_rows": len(daily_recovery_rows),
            "affected_local_dates": len(affected_dates),
        },
        "affected_local_dates": [str(item) for item in affected_dates],
        "keep_ids": keep_ids,
        "remove_ids": remove_ids,
        "workouts": [serialize_workout(row) for row in workouts],
        "workout_load_rows": [serialize_workout_load(row) for row in workout_load_rows],
        "daily_load_rows": [serialize_daily_load(row) for row in daily_load_rows],
        "daily_recovery_rows": [serialize_daily_recovery(row) for row in daily_recovery_rows],
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(snapshot["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
