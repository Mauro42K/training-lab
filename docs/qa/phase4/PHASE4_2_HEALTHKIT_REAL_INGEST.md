# Phase 4.2 QA Runbook — HealthKit Real Ingest Enablement

## Closure summary
- Phase 4.2 validated successfully with real data.
- HealthKit authorization works on real device.
- Bootstrap ingest fetched **3436 workouts** from the historical dataset.
- Ingest completed in **9 batches** against `POST /v1/ingest/workouts`.
- Backend persisted workouts and derived load in PostgreSQL.
- Training-load endpoints now return real TRIMP values.
- Sync lifecycle reached `bootstrap -> incremental -> ready`.
- Post-ingest refresh `422` on `GET /v1/daily` was fixed by sending `YYYY-MM-DD`.
- Deprecated HealthKit `totalEnergyBurned` access was replaced with `HKWorkout.statistics(for: .activeEnergyBurned)`.

## Objective
Validate real end-to-end ingest:

Apple Fitness / HealthKit  
-> iOS authorization  
-> `fetchWorkouts(since:)`  
-> `/v1/ingest/workouts`  
-> `workouts` / `workout_load` / `daily_load`  
-> Training Load UI with real data

## Platform rule
- iPhone real: mandatory for acceptance.
- Simulator/macOS: smoke only.

## Runtime prerequisites
1. `DesignSystemDemo/Config/Runtime.Local.xcconfig` points to target backend.
2. `TRAINING_LAB_API_KEY` is valid for that backend.
3. Backend `/health` returns 200.

## iOS app prerequisites
1. HealthKit entitlement present in target (`DesignSystemDemo.entitlements`).
2. Health usage descriptions present in `Info.plist`.
3. Build and run on iPhone real with valid signing/team.

## Bootstrap strategy (explicit)
- Local sync state now tracks `hasCompletedRealHealthKitIngest`.
- If `false`:
  - orchestrator ignores previous `lastSuccessfulIngestAt` and performs full bootstrap fetch (`since=nil`).
- After first successful real ingest:
  - `hasCompletedRealHealthKitIngest` is set `true`.
  - subsequent syncs are incremental (`since=lastSuccessfulIngestAt`).

Practical reset for QA rerun:
- uninstall/reinstall app (or clear app data) to reset local SwiftData sync state.

## Avg HR rule (explicit)
- source: HR samples inside `[workout.start, workout.end]`.
- method: HealthKit `HKStatisticsQuery(.discreteAverage)` over heart-rate samples.
- if not enough HR data: `avg_hr_bpm = nil`.
- no hidden heuristics.

## Identity model (current phase)
- Backend ingestion still resolves to the default backend user (`get_or_create_default_user`).
- Multi-user identity by API key is not introduced in this phase.
- QA must treat the backend dataset as single-user scoped.

## Seed / fixture data policy
- Do not run blind/global deletes.
- Preferred strategy:
  - isolate QA comparison by recent date window and real source (`com.apple.health`) in API outputs.
- If cleanup is required:
  - use targeted tombstones only for known fixture UUIDs and/or known fixture sources.
  - document every deleted UUID and reason.

## Verification checklist
1. iPhone real grants HealthKit read access for workouts (and HR if requested).
2. Initial sync sends ingest batches successfully (no 401/409/422/500).
3. `GET /v1/workouts` contains expected recent sessions from Apple Fitness.
4. `source_bundle_id` for real sessions shows Apple source values (for example `com.apple.health`).
5. `GET /v1/training-load?days=28&sport=all` reflects new TRIMP values after ingest.
6. Training Load screen shows real daily updates for `all/run/strength` as applicable.

## Backend spot-check commands
```bash
curl -sS https://api.training-lab.mauro42k.com/health

curl -sS -H "X-API-KEY: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/training-load?days=28&sport=all"

curl -sS -H "X-API-KEY: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/workouts?from=2026-03-01T00:00:00Z&to=2026-03-07T00:00:00Z"
```

## Acceptance gate (Phase 4.2)
- Closed: iPhone real evidence confirmed backend results versus Apple Fitness/HealthKit history for recent days.
