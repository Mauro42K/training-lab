# Phase 4.4.1 — Source Precedence Decision (Block 4)

## Status
- Date: 2026-03-11 (America/Mexico_City)
- Environment: staging evidence only
- Mode: read-only policy decision + audit rerun
- Mutation: none

## Scope
- review the filtered source-conflict sample
- freeze exact precedence for the two mandatory priority pairs
- rerun the duplicate audit with policy applied
- quantify how many clusters move from manual review to auto-cleanup eligible

This block does **not**:
- delete rows
- mark rows as deleted
- recompute derived tables
- touch production

## Human review basis

Review input:
- `docs/qa/phase4/artifacts/phase4_4_1_source_precedence_review_sample.csv`

Pairs reviewed first:
1. `com.garmin.connect.mobile` vs `com.strava.stravaride`
2. `com.rungap.RunGap` vs `com.strava.stravaride`

Review heuristic used:
- compare mirrored rows, not the entire raw export
- check whether one source is consistently at least as complete as the other
- reject any attempt to generalize into a global source hierarchy

## Pair decisions

### Garmin vs Strava
- pair:
  - `com.garmin.connect.mobile`
  - `com.strava.stravaride`
- preferred_source_bundle_id:
  - `com.garmin.connect.mobile`
- decision_basis:
  - filtered human sample review + stronger direct-source interpretation
- confidence:
  - `high`
- rationale:
  - the sample was homogeneous enough for a rule
  - Garmin rows were never less complete in the filtered sample
  - the mirrored rows were near-identical and Garmin looked like the more direct origin than Strava sync mirrors
- exceptions_policy:
  - only apply when the cluster is size-2 pure source conflict with no extra divergence reasons

Sample signals:
- review rows: `20`
- left-side completeness `>=` right-side completeness: `20 / 20`
- left-side completeness `>` right-side completeness: `0 / 20`
- avg HR present left/right: `20 / 20` vs `20 / 20`

Operational rule:
- prefer `com.garmin.connect.mobile` over `com.strava.stravaride` when the cluster is size-2 and the only reason is `conflicting_source_bundle_id`

### RunGap vs Strava
- pair:
  - `com.rungap.RunGap`
  - `com.strava.stravaride`
- preferred_source_bundle_id:
  - `com.rungap.RunGap`
- decision_basis:
  - filtered human sample review + repeated completeness advantage over Strava mirrors
- confidence:
  - `high`
- rationale:
  - the sample was sufficiently homogeneous for a rule
  - RunGap rows were never less complete in the filtered sample
  - RunGap had richer HR presence in a meaningful subset of cases
  - mirrored rows remained tightly aligned on time/distance/energy
- exceptions_policy:
  - only apply when the cluster is size-2 pure source conflict with no extra divergence reasons

Sample signals:
- review rows: `20`
- left-side completeness `>=` right-side completeness: `20 / 20`
- left-side completeness `>` right-side completeness: `6 / 20`
- avg HR present left/right: `19 / 20` vs `13 / 20`

Operational rule:
- prefer `com.rungap.RunGap` over `com.strava.stravaride` when the cluster is size-2 and the only reason is `conflicting_source_bundle_id`

## Policy artifact

Machine-readable policy:
- `docs/qa/phase4/artifacts/phase4_4_1_source_precedence_policy.json`

Important limit:
- this is pair-specific precedence only
- it is **not** a global hierarchy for all workout sources

## Audit rerun with policy

Rerun command used:

```bash
ssh root@178.156.251.31 \
  "docker exec -i v0w8cgwwos8go0ggswgg4wgk-114859126478 python - --policy-json /tmp/phase4_4_1_source_precedence_policy.json" \
  < scripts/audit_workout_history_duplicates.py
```

Note:
- the policy file was copied into the staging app container only for read-only audit rerun
- no DB mutation happened

Artifacts:
- baseline audit:
  - `docs/qa/phase4/artifacts/phase4_4_1_duplicate_audit.json`
- policy rerun:
  - `docs/qa/phase4/artifacts/phase4_4_1_duplicate_audit_with_policy.json`

## Rerun result

Before policy:
- auto-cleanup eligible clusters: `37`
- auto-cleanup eligible rows: `74`
- manual-review clusters: `493`

After policy:
- auto-cleanup eligible clusters: `356`
- auto-cleanup eligible rows: `712`
- manual-review clusters: `174`
- manual-review rows: `438`
- source-policy eligible clusters: `319`
- source-policy eligible rows: `638`

Delta:
- newly eligible clusters: `+319`
- newly eligible rows: `+638`

Interpretation:
- the two approved pairs alone unlock the majority of the current source-conflict backlog
- the next remaining manual-review surface is materially smaller and more defensible

## Blast radius after policy

Before policy, eligible-only blast radius:
- `workout_load` rows: `74`
- `workout_load` distinct dates: `32`
- `daily_load` rows: `155`
- `daily_load` user/date pairs: `31`

After policy, eligible-only blast radius:
- `workout_load` rows: `580`
- `workout_load` distinct dates: `243`
- `daily_load` rows: `1515`
- `daily_load` user/date pairs: `303`
- legacy `/v1/daily` user/date pairs: `304`

Interpretation:
- the blast radius becomes meaningfully larger
- but it is still bounded and traceable
- this remains consistent with targeted cleanup, not full reload

## Block 4 conclusion

- source precedence is now frozen for the two mandatory priority pairs
- the audit rerun shows a substantial reduction in manual-review pressure
- the next step should still be targeted-cleanup planning, not reload escalation
