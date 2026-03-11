# Phase 4.4.1 — Staging Cleanup Execution (Block 5)

## Status
- Date: 2026-03-11 (America/Mexico_City)
- Environment: staging only
- Mode: targeted cleanup + bounded recompute
- Production writes: none

## Scope
- execute the first targeted cleanup only over the currently eligible subset
- keep full before/after traceability
- recompute only the affected downstream windows
- validate that the eligible subset disappears without touching manual-review clusters

This block does **not**:
- touch production
- expand the subset beyond the approved policy
- clean manual-review clusters
- perform a full rebuild

## Cleanup subset frozen for this execution

Eligibility gate used:
- clusters from `phase4_4_1_duplicate_audit_with_policy.json`
- `cluster_size = 2`
- no extra divergence reasons
- approved source precedence policy applied

Explicitly excluded:
- manual-review clusters
- `cluster_size > 2`
- unresolved source conflicts
- ambiguous recent cases
- anything outside the approved policy file

Tracked keep/remove artifact:
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_plan.json`
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_plan.csv`

Subset summary:
- eligible clusters: `356`
- keep workout ids: `356`
- remove workout ids: `356`
- source-policy clusters inside subset: `319`
- affected local dates: `306`
- affected date range: `2018-06-22` to `2023-11-05`

Each cleanup item records:
- `cluster_id`
- `user_id`
- `keep` workout
- `remove` workout(s)
- `affected_local_dates`
- `eligibility_basis`
- `reason_basis`

## Checkpoint / backup strategy

Before mutation, a verifiable snapshot of the affected staging set was exported:
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_snapshot_before.json`

It contains:
- all involved workout rows
- `keep_ids`
- `remove_ids`
- affected `workout_load` rows
- affected `daily_load` rows
- affected `daily_recovery` rows
- affected local dates
- before-count summary

Before counts:
- workouts found: `712`
- keep ids: `356`
- remove ids: `356`
- workout_load rows: `580`
- daily_load rows: `1530`
- daily_recovery rows: `0`
- affected local dates: `306`

Dry-run artifact created before mutation:
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_dry_run.json`

Dry-run summary:
- workouts to delete: `356`
- workout_load rows to delete: `290`
- daily_load dates to rebuild: `306`
- daily_recovery dates to rebuild: `306`

## Execution

Execution script:
- `scripts/execute_workout_dedup_cleanup.py`

Cleanup path used:
- physical delete of loser rows in `workouts`
- explicit delete of related `workout_load` rows

Rationale:
- `is_deleted` in the current model reflects ingest/tombstone semantics
- this operation is historical duplicate remediation, not an upstream delete event
- physical delete keeps the canonical dataset clean while the snapshots preserve traceability

Execution artifact:
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_execution.json`

Execution result:
- deleted workouts: `356`
- deleted workout_load rows: `290`
- rebuilt daily_load dates: `306`
- rebuilt daily_recovery dates: `306`
- rebuilt daily_recovery rows: `0`

## Recompute executed

Bounded recompute only; no full rebuild.

Recomputed surfaces:
- workout-derived load:
  - stale `workout_load` rows for removed workout ids deleted explicitly
- `daily_load`:
  - rebuilt only for the `306` affected local dates
- `daily_recovery`:
  - recomputed only for the same affected local dates
  - rows rebuilt: `0`

Why `daily_recovery` stayed at zero:
- this historical slice currently has no persisted recovery rows on those dates
- recompute still ran to keep downstream consistency explicit

## Post-cleanup validation

After snapshot:
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_snapshot_after.json`

After counts:
- workouts found: `356`
- keep ids: `356`
- remove ids: `356`
- workout_load rows: `290`
- daily_load rows: `1530`
- daily_recovery rows: `0`
- affected local dates: `306`

Key integrity checks:
- all keep ids retained: `true`
- all remove ids absent: `true`
- removed workout rows: `356`

Daily-load delta check:
- rows with changed `sessions_count` or `trimp_total`: `490`
- observed changes were reductions only on expected affected dates
- unchanged sport/date rows remained logically intact

Sample expected change:
- `2018-06-22 all`: `(sessions=2, trimp=72.70)` -> `(sessions=1, trimp=36.19)`
- `2018-06-22 bike`: `(sessions=2, trimp=72.70)` -> `(sessions=1, trimp=36.19)`

Duplicate audit rerun after cleanup:
- `docs/qa/phase4/artifacts/phase4_4_1_duplicate_audit_after_cleanup.json`

Before cleanup, with policy applied:
- candidate clusters: `530`
- candidate rows: `1150`
- auto-cleanup eligible clusters: `356`
- auto-cleanup eligible rows: `712`
- manual-review clusters: `174`
- manual-review rows: `438`

After cleanup:
- candidate clusters: `174`
- candidate rows: `438`
- auto-cleanup eligible clusters: `0`
- auto-cleanup eligible rows: `0`
- manual-review clusters: `174`
- manual-review rows: `438`

Interpretation:
- the entire eligible subset was removed from the duplicate universe
- only the manual-review surface remains

## API sanity checks on staging

Post-cleanup smoke validation:
- `GET /health` -> `200`
- `GET /v1/workouts?from=2020-10-29T00:00:00Z&to=2020-10-30T23:59:59Z` -> `200`
- `GET /v1/daily?from=2020-10-29&to=2020-10-30` -> `200`
- `GET /v1/training-load?days=7&sport=all` -> `200`
- `GET /v1/daily-domains/recovery?from=2020-10-29&to=2020-10-30` -> `200`

Observed responses:
- `/v1/workouts` returned items normally
- `/v1/daily` remained healthy
- `/v1/training-load` remained healthy
- `/v1/daily-domains/recovery` returned `items: []`, consistent with zero persisted recovery rows on the affected historical dates

## Unexpected findings

No serious unexpected blocker appeared during staging cleanup.

Notable but expected:
- `daily_load` row count stayed flat because the rebuild recreates rows for the same date/sport surface
- metric values changed only where duplicate workouts had inflated counts/load
- recent ambiguous clusters were not touched because they never entered the subset

## Block 5 conclusion

- targeted staging cleanup executed successfully
- checkpoint and before/after evidence captured
- bounded recompute completed
- eligible duplicate subset removed
- legacy endpoints remained healthy
- only manual-review duplicate clusters remain

Operational read:
- staging validates well
- the repo is ready to plan a production-specific runbook for the same policy-bounded cleanup
- production should **not** be touched until a dedicated production checkpoint and execution plan are reviewed
