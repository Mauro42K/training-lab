# Phase 4.4.1 — Production Cleanup Runbook

## Status
- Date: 2026-03-11 (America/Mexico_City)
- Environment: production
- Mode: runbook only
- Production mutation in this document: not executed yet

## Purpose
- execute the same policy-bounded cleanup already validated in staging
- freeze the exact production subset before any mutation
- require verifiable checkpoint artifacts
- run a dry run before the real execution
- recompute only the affected downstream windows
- stop immediately if production diverges materially from the validated staging profile

This runbook does **not**:
- widen the subset beyond the approved policy
- touch manual-review clusters
- perform a full reload
- replace a production-specific go/no-go review

## Inputs / prerequisites

Required scripts:
- `scripts/audit_workout_history_duplicates.py`
- `scripts/build_workout_dedup_cleanup_plan.py`
- `scripts/export_workout_cleanup_snapshot.py`
- `scripts/execute_workout_dedup_cleanup.py`

Required policy:
- `docs/qa/phase4/artifacts/phase4_4_1_source_precedence_policy.json`

Reference evidence from staging:
- `docs/qa/phase4/PHASE4_4_1_STAGING_CLEANUP.md`
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_plan.json`
- `docs/qa/phase4/artifacts/phase4_4_1_cleanup_execution.json`
- `docs/qa/phase4/artifacts/phase4_4_1_duplicate_audit_after_cleanup.json`

Expected staging baseline for comparison:
- eligible clusters: `356`
- keep workout ids: `356`
- remove workout ids: `356`
- source-policy clusters: `319`
- affected local dates: `306`
- date range: `2018-06-22` to `2023-11-05`

## Production freeze window

The operator must define a single freeze point `T0` before any mutation.

At `T0`:
1. confirm the exact production SHA via `/health`
2. confirm `environment=production`
3. confirm production auto deploy remains `OFF`
4. run the production audit with policy
5. generate the cleanup plan
6. record the plan summary and checksum
7. do not execute cleanup until those artifacts are reviewed

The frozen plan is the only plan allowed for the subsequent dry run and real execution.
If the plan changes after `T0`, abort and restart from a new freeze point.

## Required production artifacts

All of these must be generated before cleanup:
- `docs/qa/phase4/artifacts/phase4_4_1_prod_duplicate_audit_with_policy.json`
- `docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_plan.json`
- `docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_plan.csv`
- `docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_plan.sha256`
- `docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_snapshot_before.json`
- `docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_dry_run.json`

Artifacts generated only after real execution:
- `docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_execution.json`
- `docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_snapshot_after.json`
- `docs/qa/phase4/artifacts/phase4_4_1_prod_duplicate_audit_after_cleanup.json`

## Stop / go gate before mutation

### GO only if all are true
- production `/health` is healthy and on the intended SHA
- Alembic is at `head`
- production auto deploy is still `OFF`
- the cleanup plan is frozen and checksummed
- the frozen subset stays within the approved policy
- the dry run matches the frozen plan
- production does not differ materially from staging in subset shape

### STOP immediately if any are true
- the production subset includes manual-review clusters
- any cluster in the frozen subset has `cluster_size > 2`
- unresolved source conflicts appear inside the frozen subset
- recent ambiguous cases enter the frozen subset
- the production subset differs materially from the staging profile
- the dry run deletes more rows than the frozen plan
- the dry run implies a blast radius not supported by the frozen plan

Material difference means any of:
- different eligibility basis outside the approved policy
- unexpected source pairs inside the eligible subset
- large unexplained increase in eligible clusters, remove ids, or affected dates
- newly eligible recent cases that were not part of the validated staging profile

If production differs materially, do **not** execute cleanup. Open review first.

## Preflight checklist

### Runtime / infra
- [ ] `curl -sS https://api.training-lab.mauro42k.com/health`
- [ ] response includes `environment=production`
- [ ] response SHA matches the intended deploy
- [ ] production auto deploy remains `OFF`
- [ ] app container is identified correctly
- [ ] Alembic `current` equals `head`

### Read-only data freeze
- [ ] rerun duplicate audit with policy on production
- [ ] build cleanup plan on production
- [ ] export `sha256` for the cleanup plan JSON
- [ ] export before snapshot for the affected set
- [ ] confirm counts are internally consistent across audit / plan / snapshot

### Sanity API
- [ ] `GET /v1/workouts`
- [ ] `GET /v1/daily`
- [ ] `GET /v1/training-load`
- [ ] `GET /v1/daily-domains/recovery`

## Subset freeze procedure

Use the approved source precedence policy file and generate the production plan read-only.

Minimum recorded fields:
- `cluster_id`
- `user_id`
- `keep workout id`
- `remove workout id(s)`
- `affected_local_dates`
- `eligibility_basis`
- `reason_basis`

The frozen plan must also record:
- `eligible_cluster_count`
- `keep_workout_count`
- `remove_workout_count`
- `affected_local_date_count`
- `source_precedence_policy_clusters`
- `generated_at_utc`
- `sha256` of the JSON plan

Recommended checksum command:

```bash
shasum -a 256 docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_plan.json \
  > docs/qa/phase4/artifacts/phase4_4_1_prod_cleanup_plan.sha256
```

## Checkpoint / backup strategy

Before mutation, export a verifiable subset snapshot:
- all involved workout rows
- `keep_ids`
- `remove_ids`
- affected `workout_load` rows
- affected `daily_load` rows
- affected `daily_recovery` rows
- affected local dates
- before-count summary

Important note:
- not every loser workout is expected to have a `workout_load` row
- therefore `deleted_workout_load_rows` may be lower than `deleted_workouts`
- that is acceptable if it matches the before snapshot and dry run

## Dry run procedure

Run the cleanup script in dry-run mode against the frozen production plan.

Expected dry-run outputs:
- `deleted_workouts`
- `deleted_workout_load_rows`
- `rebuilt_daily_load_dates`
- `rebuilt_daily_recovery_dates`
- `rebuilt_daily_recovery_rows`

Dry run must match the frozen subset.
If there is any mismatch, stop and review before mutation.

## Cleanup execution procedure

Only after successful preflight + frozen plan + matching dry run.

Cleanup path:
- physical delete of loser rows in `workouts`
- explicit delete of related `workout_load` rows

Why physical delete:
- `is_deleted` reflects ingest/tombstone semantics
- this cleanup is historical duplicate remediation, not an upstream delete event
- physical delete matches the validated staging path and keeps the canonical dataset clean

Execution must stay bounded to the frozen subset only.

## Recompute plan

No full rebuild by default.

Recompute only:
- stale `workout_load` cleanup for removed workouts
- `daily_load` rebuild for affected local dates only
- `daily_recovery` recompute for those same dates only

Important note:
- do not overinterpret `daily_recovery` if before/after remains `0`
- in staging the affected historical slice already had `0` persisted recovery rows
- a `0 -> 0` result there is neutral, not a failure signal

## Post-cleanup validation

### Required data validation
- export `phase4_4_1_prod_cleanup_snapshot_after.json`
- rerun the duplicate audit with policy
- verify all keep ids remain present
- verify all remove ids are absent
- verify the eligible subset is gone from the duplicate universe
- verify only manual-review surface remains

### Required downstream validation
- compare `daily_load` before vs after only on affected dates
- confirm changes are reductions/adjustments consistent with dedupe
- confirm there are no unexpected changes outside the affected blast radius

### Required API sanity
- `GET /health`
- `GET /v1/workouts`
- `GET /v1/daily`
- `GET /v1/training-load`
- `GET /v1/daily-domains/recovery`

## Rollback expectations

This runbook does **not** assume instant automatic rollback.

Rollback expectation is targeted restoration from the frozen before snapshot:
1. use `phase4_4_1_prod_cleanup_snapshot_before.json`
2. use the frozen cleanup plan
3. restore removed rows explicitly if needed
4. rerun bounded recompute

If the failure exceeds the targeted subset or restoration cannot be trusted:
- stop further action
- escalate to DB-level recovery only if a separate restore path is approved

## Success criteria

Production cleanup is successful only if all are true:
- frozen subset generated and checksummed at `T0`
- dry run matched the frozen plan
- real execution removed exactly the expected loser rows
- keep ids remained present
- remove ids disappeared
- audit rerun shows the eligible subset gone
- manual-review clusters remain untouched
- legacy endpoints stay healthy
- no serious unexpected finding appears during or after recompute

## Next operator step

The next safe operational step is:
1. run production freeze at `T0`
2. export checksum + before snapshot
3. execute dry run only
4. review dry run against the frozen plan
5. request explicit go/no-go before real production mutation
