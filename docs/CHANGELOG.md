# Changelog

This project follows a simple SemVer-style changelog.

## v0.4.5 - 2026-03-11

## Phase 4.5 — Daily Domains & Summary Contracts (Apple-first)

Added
- Apple-first backend foundation for:
  - `sleep_sessions`
  - `daily_sleep_summary`
  - `daily_activity`
  - `body_measurements`
  - `recovery_signals`
  - `daily_recovery`
- explicit query contracts:
  - `GET /v1/daily-domains/sleep`
  - `GET /v1/daily-domains/activity`
  - `GET /v1/daily-domains/recovery`
  - `GET /v1/daily-domains/body-measurements`
  - `GET /v1/home/summary`
- QA evidence for Block 7 closure on staging and production after Alembic migration `20260311_01`

Improved
- daily-domain semantics now run on the documented `normalized -> derived -> query` pattern.
- staging and production operational flow hardened with explicit migration validation before HTTP QA.
- iOS runtime environment now aligns with the API host, preventing debug environment drift when the app points to production.

Fixed
- remote `500` failures on Phase 4.5 endpoints caused by missing DB migration in staging and production.
- debug runtime badge visibility in production-like iPhone smoke tests.

Notes
- Phase 4.5 is now formally closed.
- Phase 4.4 remains on hold.
- the next logical focus moves to Phase 5 Home v1 on top of the contracts delivered here.

## v0.4.4 - 2026-03-11

## Phase 4.5 — Daily Domains & Summary Contracts (Apple-first)

Added
- primary phase-opening document: `docs/PHASE4_5_DAILY_DOMAINS_SUMMARY_CONTRACTS.md`.
- explicit documentary freeze for Apple-first daily domains:
  - `sleep_sessions`
  - `daily_sleep_summary`
  - `daily_recovery`
  - `daily_activity`
  - `body_measurements`
- explicit cross-domain rules for `local_date`, timezone, completeness, provenance, idempotency, and affected-date recompute.

Improved
- repository context updated so the active next phase is now 4.5.
- roadmap, README, dev notes, data sources, and metrics documentation aligned with the new Apple-first scope.
- provenance minimum frozen for Phase 4.5 as:
  - `provider`
  - `source_count`
  - `has_mixed_sources`
  - `primary_device_name`

Notes
- this is a documentation-only opening of Phase 4.5.
- no implementation, migrations, endpoints, or runtime contracts were added in this step.
- Phase 4.4 is now explicitly on hold and must not be mixed into 4.5 execution.

## v0.4.3 - 2026-03-10

## Phase 4.3 — Staging Environment & Environment Separation

Added
- separate staging API service in Coolify.
- separate staging PostgreSQL database resource.
- one-shot logical clone from production into staging baseline.
- explicit iOS runtime environment selection for `production | staging | local`.
- visible runtime environment badge in debug builds.

Improved
- environment verification through `/health.environment`.
- operational runbooks for staging deploy, DNS/TLS checks, and prod/staging isolation.
- developer runtime setup for environment-specific `Runtime.Local.xcconfig`.

Fixed
- canonical staging routing so `api-staging.training-lab.mauro42k.com` resolves and serves the staging app.
- stale staging proxy labels that were still pinned to the old `sslip` fallback host.
- staging TLS issuance on the canonical hostname.

Notes
- production and staging now use different PostgreSQL databases.
- staging starts from a cloned production baseline and is allowed to diverge afterward.
- historical reconciliation and cleanup move next to Phase 4.4.

## v0.4.2 - 2026-03-09

## Phase 4.2 — HealthKit Real Ingest Enablement

- Implemented real HealthKit ingest pipeline.
- Added batch ingestion endpoint integration.
- PostgreSQL persistence validated.
- Training load calculations validated with real data.
- Fixed refresh `422` error on `/v1/daily`.
- Replaced deprecated HealthKit `totalEnergyBurned` property.
- Completed bootstrap ingest of full historical dataset (3436 workouts).

## v0.4.1 - 2026-03-06

Phase 4.1 Closed

Added
- Training Load chart temporal axis polish for fast 28d read.
- macOS hover context tooltip (minimal and non-invasive).
- runtime config persistence through `xcconfig` + bundle-backed config resolution.

Improved
- chart states hierarchy and visual readability (`selected > today > hover > normal`).
- summary row hierarchy and sport filter interaction feedback.
- Training Load chart reuse readiness for future Home TrendCard integration.

Fixed
- baseline rendering so bars always grow from bottom (`TRIMP=0` anchored to baseline).
- macOS day detail interaction and close stability.
- cache scope isolation by effective `baseURL` to avoid mixing stale environment data.

Notes
- Phase 4.1 closes UX polish + multiplatform stability + runtime config hardening.
- Real Apple Health/Fitness ingest remains unresolved in this phase.
- HealthKit real ingest enablement is formally moved to Phase 4.2.

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
