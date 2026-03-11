#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, date
from pathlib import Path

from sqlalchemy import delete, select

from api.core.config import get_settings
from api.db.models import Workout, WorkoutLoad
from api.db.session import SessionLocal
from api.repositories.load_repository import rebuild_daily_load_for_dates
from api.services.daily_recovery_recompute_service import DailyRecoveryRecomputeService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute physical duplicate cleanup for an approved keep/remove plan.")
    parser.add_argument("--plan-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = json.loads(args.plan_json.read_text(encoding="utf-8"))
    user_id = plan["user_id"]
    remove_ids = sorted({row["id"] for item in plan["items"] for row in item["remove"]})
    keep_ids = sorted({item["keep"]["id"] for item in plan["items"]})
    affected_dates = sorted({date.fromisoformat(item) for item in plan["summary"]["affected_local_dates"]})
    settings = get_settings()

    db = SessionLocal()
    try:
        existing_remove_rows = db.execute(
            select(Workout.id).where(
                Workout.user_id == user_id,
                Workout.id.in_(remove_ids),
            )
        ).scalars().all()
        if len(existing_remove_rows) != len(remove_ids):
            raise RuntimeError(
                f"Expected {len(remove_ids)} removable workouts, found {len(existing_remove_rows)} before cleanup."
            )

        keep_rows = db.execute(
            select(Workout.id).where(
                Workout.user_id == user_id,
                Workout.id.in_(keep_ids),
            )
        ).scalars().all()
        if len(keep_rows) != len(keep_ids):
            raise RuntimeError(
                f"Expected {len(keep_ids)} keep workouts, found {len(keep_rows)} before cleanup."
            )

        delete_workout_load_stmt = delete(WorkoutLoad).where(
            WorkoutLoad.user_id == user_id,
            WorkoutLoad.workout_id.in_(remove_ids),
            WorkoutLoad.trimp_model_version == settings.trimp_active_model_version,
        )
        delete_workouts_stmt = delete(Workout).where(
            Workout.user_id == user_id,
            Workout.id.in_(remove_ids),
        )

        deleted_workout_load_rows = db.execute(delete_workout_load_stmt).rowcount or 0
        deleted_workouts = db.execute(delete_workouts_stmt).rowcount or 0

        rebuild_daily_load_for_dates(
            db,
            user_id=user_id,
            dates=affected_dates,
            trimp_model_version=settings.trimp_active_model_version,
        )
        recovery_summary = DailyRecoveryRecomputeService(settings=settings).recompute_for_dates(
            db,
            user_id=user_id,
            dates=affected_dates,
        )

        result = {
            "executed_at_utc": __import__("datetime").datetime.now(tz=UTC).isoformat(),
            "dry_run": args.dry_run,
            "user_id": user_id,
            "deleted_workouts": deleted_workouts,
            "deleted_workout_load_rows": deleted_workout_load_rows,
            "affected_local_dates": [str(item) for item in affected_dates],
            "rebuilt_daily_load_dates": len(affected_dates),
            "rebuilt_daily_recovery_rows": recovery_summary.rebuilt_daily_recovery_rows,
            "rebuilt_daily_recovery_dates": recovery_summary.rebuilt_dates,
        }

        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
