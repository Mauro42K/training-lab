# Training Lab Codex Context

## Repo
- Training Lab is the source repository for the product foundation.
- This file is the source of truth for every Codex run.

## Current Phase
- **Phase 4.5 — CLOSED** (2026-03-11 America/Mexico_City)

### Phase 4.5 Closure Summary
- Apple-first daily-domain foundation delivered end-to-end:
  - `sleep_sessions`
  - `daily_sleep_summary`
  - `daily_activity`
  - `body_measurements`
  - `recovery_signals`
  - `daily_recovery`
- Query contracts delivered:
  - `GET /v1/daily-domains/sleep`
  - `GET /v1/daily-domains/activity`
  - `GET /v1/daily-domains/recovery`
  - `GET /v1/daily-domains/body-measurements`
  - `GET /v1/home/summary`
- QA/hardening closed:
  - local automated QA passed
  - staging and production validated after Alembic migration `20260311_01`
  - production auto deploy turned `OFF`
  - staging auto deploy remains `ON`
- Minor iOS closure fix delivered:
  - runtime environment now aligns with the API host
  - debug runtime badge stays visible for `local` / `staging` and hidden for `production`

## Phase 4.0 Delivered

### Backend
- TRIMP engine v1.
- Recompute pipeline (incremental + deterministic daily rebuild).
- `GET /v1/training-load` endpoint.
- Backfill pipeline for historical load.

### iOS
- `TrainingLoadScreen` (temporary runtime screen).
- `TrainingLoadRepository` integrated.
- Daily TRIMP chart (28 days).
- Sport filters: `all`, `run`, `bike`, `strength`, `walk`.
- Day detail sheet with multi-session support.

### Critical Fix Closed
- Today mismatch between UI and backend fixed.
- Final validation:
  - `today_local = 2026-03-06`
  - last training-load item `date = 2026-03-06`
  - values match exactly.

## Phase 4.1 Delivered

### UX/UI + Chart
- Temporal axis polish for Training Load chart.
- Summary hierarchy + filter feedback refinement.
- State polish with explicit priority: `selected > today > hover > normal`.
- Baseline fix: bars always grow from bottom; `TRIMP=0` stays anchored.
- Sparse-data rendering polish and lightweight macOS hover tooltip.

### Multiplatform Stability
- macOS interaction flow stabilized for day detail open/close.
- iOS/macOS behavior kept consistent without backend/API changes.

### Runtime Config + Data Consistency
- Persistent runtime config via `xcconfig` + bundle values (no `launchctl` dependency).
- Cache scope isolation by effective `baseURL` to prevent cross-environment cache mixing.

Guardrail (explicit):
- Phase 4.1 closes UX polish + multiplatform stability + runtime config only.
- Real HealthKit / Apple Fitness ingest alignment is not solved here.

## Phase 4.2 Delivered

### Ingest Pipeline
- Real ingest path validated end-to-end:
  - Apple Health / Fitness
  - iPhone HealthKit authorization
  - `fetchWorkouts(since:)`
  - `POST /v1/ingest/workouts`
  - PostgreSQL persistence
  - `GET /v1/workouts`, `GET /v1/daily`, `GET /v1/training-load`
- Historical bootstrap ingest completed successfully with **3436 workouts** fetched from HealthKit and processed in **9 batches**.
- Backend persistence verified in PostgreSQL with real training-load values after ingest.

### Sync Lifecycle
- Sync lifecycle validated on real device:
  - `bootstrap`
  - `incremental`
  - `ready`
- Cursor tracking in iOS uses `lastSuccessfulIngestAt`.
- Post-ingest refresh bug closed by sending date-only params to `GET /v1/daily`.

### Runtime / Platform Notes
- Backend database type in active environment: **PostgreSQL**.
- Batch ingestion remains idempotent through `healthkit_workout_uuid` + request idempotency keys.
- Deprecated HealthKit energy access replaced with `HKWorkout.statistics(for: .activeEnergyBurned)`.

## Phase 4.3 Delivered

### Environment Separation
- Production and staging are now separated operationally in Coolify.
- Production API remains `https://api.training-lab.mauro42k.com`.
- Staging service exists as a separate Coolify application and is reachable through the canonical host `https://api-staging.training-lab.mauro42k.com`.
- Staging fallback `sslip` host remains only as an emergency/debug path, not the primary endpoint.
- Canonical staging DNS resolves publicly and TLS is valid on `https://api-staging.training-lab.mauro42k.com`.

### Databases
- Active backend database type remains **PostgreSQL**.
- Production DB resource: `training-lab-postgres`.
- Staging DB resource: `training-lab-postgres-staging`.
- Staging baseline was created through a one-shot logical clone from production.
- Comparative validation after clone:
  - `workouts = 3436`
  - `workout_load = 3173`
  - `daily_load = 9720`

### Environment Verification
- `/health` now returns explicit `environment`.
- Current expected values:
  - production: `environment=production`
  - staging: `environment=staging`
- This is the primary non-ambiguous runtime check together with the canonical domain.

### iOS Runtime Config
- Runtime config now supports explicit `production`, `staging`, and optional `local`.
- `Runtime.Local.example.xcconfig` documents how to point the app at each environment.
- Debug builds show a visible runtime environment badge to avoid pointing at the wrong backend silently.
- Cache isolation by effective `baseURL` remains in place.

Closure note:
- Phase 4.3 remains the last completed pre-daily-domains environment phase.
- Phase 4.5 is now fully closed with implementation, QA evidence, and operational validation.

## Next Phase
- **Phase 5 — Home v1 (Rings + Drivers Cards)** (**Planned**)
- Focus:
  - compose Home from the explicit 4.5 daily-domain contracts already delivered,
  - preserve transparency and data completeness semantics,
  - avoid introducing hidden scoring logic before driver presentation is explicit.

### Tactical Remediation Track
- Tactical remediation track approved: **Phase 4.4.1 — Workout History Dedup & Recompute**
- Purpose: historical duplicate audit, targeted cleanup, and recompute
- Status: closed, staging cleanup validated, production cleanup not needed
- It does not replace Phase 5 as the next product phase.
- Phase 4.4 remains on hold unless 4.4.1 findings force broader reconciliation scope.
- Closure note:
  - staging cleanup executed successfully over the approved eligible subset,
  - production freeze/preflight confirmed the correct production target,
  - production already matched the residual post-cleanup manual-review surface and had `0` auto-cleanup eligible clusters,
  - no production mutation was required.

## On Hold Phase
- **Phase 4.4 — Workout Reconciliation & Historical Cleanup** (**On Hold**)
- Status note:
  - historical workout reconciliation, deleted workout cleanup, and duplicate cleanup remain paused and must not be mixed into Phase 4.5.

## Non-Negotiables
- Design-first.
- Battery transparent.
- TRIMP hero.

## Product Tabs
- Home
- Trends
- Workouts
- Body
- More
- Coach

## Workflow
- Shell -> Service -> HTTP QA.
- Keep patches scoped and explicit.
- Never leave uncommitted changes.
- Always update documentation before pushing a new version.

## Infra
- GitHub repository: `Mauro42K/training-lab`
- VPS host: `root@178.156.251.31`
- Deploy platform: Coolify running on the VPS.
- Stable API domain target: `https://api.training-lab.mauro42k.com`
- Default start command: `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Local smoke test: `curl -i http://127.0.0.1:8000/health`
- Remote smoke test: `curl -i https://api.training-lab.mauro42k.com/health`

## Security
- Never paste tokens into docs, logs, or chat.
- If a token is exposed, rotate it immediately and document the rotation.

## How To Work With Codex
- Always read this file first.
- Inspect the current tree before editing anything else.
- Keep patches scoped.
- Produce diffs through git.
- Run QA after changes.
- Commit and push only when the tree is clean.
