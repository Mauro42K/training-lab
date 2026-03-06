#!/usr/bin/env python3
import argparse

from api.db.session import SessionLocal
from api.services.trimp_backfill_service import DEFAULT_BACKFILL_JOB_NAME, TrimpBackfillService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill workout_load and daily_load in batches.")
    parser.add_argument("--batch-size", type=int, default=500, help="Rows per batch (default: 500).")
    parser.add_argument("--max-batches", type=int, default=None, help="Optional cap for batches in this run.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset job cursor/state/metrics only. Does not delete persisted load tables.",
    )
    parser.add_argument(
        "--job-name",
        type=str,
        default=DEFAULT_BACKFILL_JOB_NAME,
        help=f"Backfill job name (default: {DEFAULT_BACKFILL_JOB_NAME}).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db = SessionLocal()
    try:
        service = TrimpBackfillService()
        summary = service.run(
            db,
            batch_size=args.batch_size,
            max_batches=args.max_batches,
            reset=args.reset,
            job_name=args.job_name,
        )
    finally:
        db.close()

    print(
        "job_name={job_name} status={status} last_cursor_id={last_cursor_id} "
        "workouts_scanned={workouts_scanned} workouts_persisted={workouts_persisted} "
        "workouts_excluded_or_deleted={workouts_excluded_or_deleted} "
        "affected_dates_rebuilt={affected_dates_rebuilt} batches_completed={batches_completed}".format(
            job_name=summary.job_name,
            status=summary.status,
            last_cursor_id=summary.last_cursor_id,
            workouts_scanned=summary.workouts_scanned,
            workouts_persisted=summary.workouts_persisted,
            workouts_excluded_or_deleted=summary.workouts_excluded_or_deleted,
            affected_dates_rebuilt=summary.affected_dates_rebuilt,
            batches_completed=summary.batches_completed,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
