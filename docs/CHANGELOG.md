# Changelog

This project follows a simple SemVer-style changelog.

## v0.4.0 - 2026-03-06

Phase 4.0 Closed

Added
- TRIMP engine v1.
- recompute pipeline.
- training-load endpoint (`GET /v1/training-load`).
- iOS Training Load screen.
- sport filters (`all/run/bike/strength/walk`).

Fixed
- Today mismatch UI vs backend.

Notes
- Training Load screen is temporary.
- It will be replaced by the real Home screen in later phases (Zero Legacy).

## v0.0.3 - 2026-03-05

- Phase 3 closed: online-first data foundation delivered and validated with QA evidence.
- Backend:
  - PostgreSQL foundation + Alembic migrations.
  - API v1 endpoints: `POST /v1/ingest/workouts`, `GET /v1/workouts`, `GET /v1/daily`.
  - API-key auth baseline for `/v1/*` (`X-API-KEY`).
  - Idempotency for ingest (`X-Idempotency-Key`) with replay/conflict behavior validated.
  - Payload guards active; dedicated rate limiting deferred to Phase 3.1.
- iOS:
  - TrainingLab shell root + permission gate flow integrated in demo runner.
  - Online-first contracts added (DTOs, clients, repositories, sync orchestration, SwiftData cache models).
  - Xcode project wiring fixed so TrainingLab sources compile under target `DesignSystemDemo`.
- QA evidence consolidated in `docs/Phase3_QA.md` and `docs/qa/phase3/`.

## v0.0.2 - 2026-03-05

- Phase 2 closed: Design System & Layout delivered and documented.
- Added `DesignSystemDemo` multiplatform runner for gallery validation on iOS + macOS.
- Finalized token system: `AppColors`, `AppTypography`, `AppSpacing`, `AppRadius`, `AppShadows`, `AppElevation`.
- Added chart styling source of truth (`AppChartStyle`) and chart container support.
- Component set closed for Phase 2: `DSCard`, `DSChartCard`, `DSRing`, `DSMetricPill`, `DSSectionHeader`, `DSSegmentedControl`, `DSEmptyState`, `DSLoadingState`.
- Visual QA matrix completed (light/dark + dynamic type basic + macOS window sizes) with evidence in `docs/Phase2_VisualQA.md` and `docs/qa/phase2/`.
- Implementation base reference: commit `3431927`; this release entry is the documentary closure.

## v0.0.1 - 2026-03-04

- Phase 1 documentation baseline completed: `docs/PRD.md`, `docs/DATA_SOURCES.md`, `docs/METRICS_CATALOG.md`, and `docs/GLOSARIO.md`.
- Versioning documentation added with this changelog and `metrics_model_version` set to `1`.

## v0.0.0 - 2026-03-04

- Initial bootstrap completed for Phase 0.
- Phase 0.1 patch closed with custom domain, TLS, baked deploy metadata, and GitHub Actions CI.
