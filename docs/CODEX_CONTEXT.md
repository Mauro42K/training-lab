# Training Lab Codex Context

## Repo
- Training Lab is the source repository for the product foundation.
- This file is the source of truth for every Codex run.

## Current Phase
- **Phase 4.2 — CLOSED** (2026-03-09 America/Mexico_City)

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

## Next Phase
- **Phase 4.4 — Workout Reconciliation & Historical Cleanup** (**Planned**)
- Scope:
  - reconcile historical backend state with current HealthKit reality.
  - support deleted/duplicated workout cleanup safely.
  - recalculate derived metrics after historical corrections.

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
