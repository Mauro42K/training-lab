# Training Lab Codex Context

## Repo
- Training Lab is the source repository for the product foundation.
- This file is the source of truth for every Codex run.

## Current Phase
- **Phase 4.0 — CLOSED** (2026-03-06 America/New_York)

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

## Next Phase
- **Phase 4.1 — Training Load UX Polish** (**Pending**)
- Scope:
  - improve visual hierarchy.
  - reduce scaffold appearance.
  - add minimal temporal axis in chart.
  - remove title duplication.
  - prepare reuse inside future Home screen.

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
