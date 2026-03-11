# Phase 4.4.1 — Duplicate Audit (Block 2)

## Status
- Date: 2026-03-11 (America/Mexico_City)
- Environment: staging database only
- Mode: read-only audit
- Mutation: none

## Scope of this block
- Audit probable historical duplicate workouts
- Quantify blast radius before any cleanup
- Separate `auto-cleanup eligible` vs `manual review`
- Decide whether targeted cleanup still looks viable

This block does **not**:
- delete rows
- mark rows as deleted
- recompute derived data
- touch production

## Execution

Script created:
- `scripts/audit_workout_history_duplicates.py`

Remote execution used:

```bash
ssh root@178.156.251.31 \
  "docker exec -i v0w8cgwwos8go0ggswgg4wgk-114859126478 python -" \
  < scripts/audit_workout_history_duplicates.py \
  > /tmp/phase4_4_1_duplicate_audit.stdout.json
```

Tracked artifacts:
- `docs/qa/phase4/artifacts/phase4_4_1_duplicate_audit.json`
- `docs/qa/phase4/artifacts/phase4_4_1_duplicate_clusters.csv`

## Duplicate cluster definition used

Two workouts enter the same **probable duplicate cluster** only if all of these are true:
- same `user_id`
- `is_deleted = false`
- different `healthkit_workout_uuid`
- same `sport`
- `abs(start_a - start_b) <= 120s`
- and:
  - `abs(end_a - end_b) <= 120s`
  - or `abs(duration_sec_a - duration_sec_b) <= 120s`

Important:
- probable cluster does **not** imply delete candidate
- `sport` remains a hard gate for clustering
- the thresholds below are audit defaults, not eternal truth

Auxiliary divergence defaults used for auto-cleanup eligibility:
- `distance_m`: `<= max(100m, 3%)`
- `energy_kcal`: `<= max(20 kcal, 10%)`
- `avg_hr_bpm`: `<= 3 bpm`

## Canonical winner rule used for audit

This rule was used only to test deterministic viability. It is **not** a cleanup action.

Order:
1. If cluster size `> 2`, send to manual review.
2. If both rows have different non-null `source_bundle_id`, send to manual review.
3. If exactly one row has non-null `source_bundle_id`, prefer it.
4. If exactly one row has non-null `device_name`, prefer it.
5. Prefer richer metadata completeness:
   - `source_bundle_id`
   - `device_name`
   - `avg_hr_bpm`
   - `distance_m`
   - `energy_kcal`
6. Stable technical tie-breaker only:
   - oldest `created_at`
   - then lowest `id`

Important:
- oldest `created_at` is only a stable technical tie-breaker
- it is **not** a semantic quality signal

## Signals available in staging

Coverage over `workouts`:
- total rows: `3436`
- active rows: `3436`
- deleted rows: `0`
- distinct users: `1`
- with `source_bundle_id`: `3436` (`100%`)
- with `device_name`: `649` (`18.89%`)
- with `avg_hr_bpm`: `2270`
- with `distance_m`: `2935`
- with `energy_kcal`: `3168`

Interpretation:
- `source_bundle_id` coverage is strong enough for source-based decisions
- `device_name` is too sparse to drive the strategy by itself
- distance/energy/HR are useful auxiliary filters, not primary identity

## Findings

### Cluster volume
- affected users: `1`
- probable duplicate clusters: `530`
- candidate rows inside those clusters: `1150`
- date range affected:
  - min start: `2015-03-17T23:11:45+00:00`
  - max start: `2026-02-13T11:55:23+00:00`

Cluster size distribution:
- size `2`: `465`
- size `3`: `45`
- size `4`: `17`
- size `5`: `1`
- size `6`: `2`

Sports distribution:
- `run`: `235`
- `bike`: `211`
- `other`: `76`
- `walk`: `8`

### Auto-cleanup vs manual review
- auto-cleanup eligible clusters: `37`
- auto-cleanup eligible rows: `74`
- manual-review clusters: `493`
- manual-review rows: `1076`

Manual-review reasons:
- `conflicting_source_bundle_id`: `408`
- `cluster_size_gt_2`: `65`
- `hr_divergence`: `37`
- `distance_divergence`: `36`
- `energy_divergence`: `34`

Important nuance:
- only `37 / 530` clusters are currently auto-cleanup eligible under the conservative rule
- but `333` manual-review clusters are size-2 clusters blocked **only** by conflicting `source_bundle_id`
- this means the main blocker is not general ambiguity; it is missing source precedence policy

### Source patterns observed

Top `source_bundle_id` conflict patterns:
- `com.garmin.connect.mobile` vs `com.strava.stravaride`: `267`
- `com.rungap.RunGap` vs `com.strava.stravaride`: `98`
- `com.strava.stravaride` vs `net.workoutdoors.workoutdoors`: `15`
- `com.nike.nikeplus-gps` vs `com.strava.stravaride`: `8`
- `com.strava.stravaride` vs `com.zwift.Zwift`: `5`

Interpretation:
- the duplicate problem is concentrated in a small set of source pairings
- `strongest stable source identity` is directionally useful
- but it still must be frozen as an **exact precedence rule** before any cleanup

### Sport consistency audit

Cross-sport near-match pairs found: `17`

Observed patterns include:
- `walk` vs `run`
- `other` vs `strength`

Interpretation:
- `sport` is not fully clean in near-identical historical sessions
- keeping `sport` as a hard clustering gate was the correct conservative choice
- these cross-sport pairs should remain outside auto-cleanup unless explicitly reviewed later

## Blast radius

### All probable clusters
- candidate workout rows: `1150`
- affected `workout_load` rows: `992`
- affected distinct `workout_load.local_date`: `372`
- affected `daily_load` rows: `2165`
- affected distinct `daily_load` user/date pairs: `433`
- affected legacy `/v1/daily` user/date pairs: `442`
- affected `daily_recovery` rows currently present on those dates: `0`

### Auto-cleanup eligible only
- candidate workout rows: `74`
- affected `workout_load` rows: `74`
- affected distinct `workout_load.local_date`: `32`
- affected `daily_load` rows: `155`
- affected distinct `daily_load` user/date pairs: `31`
- affected legacy `/v1/daily` user/date pairs: `31`
- affected `daily_recovery` rows currently present on those dates: `0`

Interpretation:
- a fully broad cleanup touches a meaningful historical surface
- a first conservative cleanup subset is much smaller and operationally manageable

## Viability assessment

### Current read
- **Option A remains viable**
- **Option B is not justified as first move**

Why:
- the model has enough real signals to cluster conservatively
- source identity coverage is strong (`100%` bundle coverage)
- the largest blocker is concentrated in a few repeatable source conflicts, not random corruption
- ambiguous clusters can be excluded cleanly into manual review

What still blocks cleanup execution:
- exact precedence rule for `source_bundle_id` must be frozen
- ambiguous clusters must remain excluded from auto-cleanup
- staging cleanup must be preceded by a backup/snapshot of the affected set

### Decision gate for next block
Proceed to targeted-cleanup planning only if all three are frozen:
1. exact source precedence for the observed bundle conflicts
2. explicit exclusion list for ambiguous clusters
3. backup/snapshot procedure for affected staging rows

If the next block cannot freeze source precedence with confidence, then escalation discussion reopens.

## Block 2 conclusion

- read-only audit completed
- probable duplicate surface quantified
- blast radius quantified
- auto-cleanup subset identified
- manual-review reasons identified
- recommendation: **continue with Option A**
- do **not** escalate to full reload at this stage
