# Changelog

This project follows a simple SemVer-style changelog.

## Planning

- Recorded roadmap decision: Phase 4.4 remains on hold / conditional; Phase 4.4.1 created as targeted historical dedupe and recompute subphase.

## v0.5.5 - 2026-03-18

## Phase 5.5 — Recommended Today

Added
- `recommended_today` Home block in the iOS Home stack between Drivers and Core Metrics.
- controlled Spanish copy generation for `Recommended Today` using the existing structured recommendation state.

Improved
- Home guidance quality by replacing fixed placeholder copy with short premium copy modulated by:
  - `state`
  - `confidence`
  - `reason_tags`
- maintainability by keeping the backend contract structured and stable while generating copy client-side.

Notes
- `Recommended Today` remains guidance-only.
- no LLM runtime, Coach behavior, planner scope, or workout prescription was introduced in this phase.
- the backend recommendation logic remains the source of truth for recommendation structure.

## v0.5.4 - 2026-03-16

## Phase 5.4 — Drivers / Explainability

Added
- `readiness.explainability` nested inside `GET /v1/home/summary`.
- explainability item contract with:
  - `key`
  - `role`
  - `status`
  - `effect`
  - `display_value`
  - `display_unit`
  - `baseline_value`
  - `baseline_unit`
  - `is_baseline_sufficient`
  - `short_reason`
- visible v1 explainability scope for:
  - `Sleep`
  - `HRV`
  - `RHR`
  - `Exertion` as secondary context
- reusable Design System primitive for the drivers surface and gallery coverage for the pattern.

Improved
- readiness transparency without changing the score math.
- consistency between score evaluation, `trace_summary`, and explainability by deriving them from the same readiness evaluation path.
- Home hierarchy by inserting a dedicated Drivers / Explainability block between Hero and Core Metrics.
- production validation coverage with real payloads for both complete and missing-driver days.

Notes
- `Movement` and `secondary strength context` remain out of the visible v1 explainability surface.
- `Exertion` remains secondary context and is not treated as a primary readiness driver.
- Phase 5.4 is formally closed.

## v0.5.3 - 2026-03-15

## Phase 5.3 — Core Metrics

Added
- `core_metrics` inside `GET /v1/home/summary`.
- Home Core Metrics block with:
  - `7-Day Load`
  - `Fitness`
  - `Fatigue`
- reusable Design System support for compact supporting metric groups.
- Gallery coverage for the Home metric snapshot pattern.

Improved
- Home context by surfacing current load-state metrics without requiring navigation to Trends.
- alignment between Home and the load domain by reusing the existing training-load calculations instead of recalculating in client code.
- Design System governance for Home supporting blocks.

Fixed
- deploy parity issue where production was still returning `core_metrics = null` while `training-load` was already up to date.
- snapshot inconsistency so `Fitness` and `Fatigue` now align with the standard load-domain window used by the trend surfaces.

Notes
- `Fitness` is the Home UI name for the internal `Capacity / CTL` value.
- Hero, Core Metrics, and Trend Card remain visually and semantically separate.
- Phase 5.3 is formally closed.

## v0.5.2 - 2026-03-14

## Phase 5.2 — Readiness Hero

Added
- `Readiness v1` as a read-time layer exposed through `GET /v1/home/summary`.
- Home Hero surface for `Readiness` with premium theming by semantic label.
- new readiness contract fields for score, label, confidence, completeness, inputs present/missing, model version, and trace summary.
- Apple Health ingest enablement for:
  - sleep
  - HRV SDNN
  - resting HR
- separate physiology bootstrap / incremental sync state for historical backfill and ongoing ingest.

Improved
- resilience of readiness baselines with sparse-history handling.
- Home semantics by standardizing `Readiness` as the governing hero concept.
- production data realism by enabling sleep and recovery-signal ingestion from iPhone HealthKit.

Fixed
- stale or misleading `Readiness unavailable` states caused by missing physiological ingest rather than readiness model failure.
- cache migration / local-store issues tied to newly added readiness-related fields in SwiftData models.
- deploy parity issues that prevented production from serving the readiness contract initially.

Notes
- primary readiness inputs in v1 are `Sleep`, `HRV`, and `RHR`.
- recent load / exertion remains bounded secondary context only.
- Phase 5.2 and 5.2.1 are operationally resolved and treated as closed inputs for subsequent Home phases.

## v0.5.1 - 2026-03-13

## Phase 5.1 — Trend Card (Load vs Capacity)

Added
- `Load vs Capacity` trend block for Home, backed by the load domain.
- `Capacity` formalized from `Fitness / CTL` and exposed in the load contract.
- `history_status`, `semantic_state`, `latest_load`, and `latest_capacity` in the training-load response.
- app naming/icon pass for Training Lab on Apple platforms.

Improved
- trend semantics by separating current load state from readiness.
- cache fallback logic so legacy local data can reconstruct load-history state and capacity more safely.
- label correctness and freshness handling for `Today` in load views.

Fixed
- stale-cache inconsistencies where the trend view could show real history while the status block said `missing`.
- capacity fallback rendering at `0` for legacy cached rows.
- cache migration failures caused by newly added mandatory fields in local SwiftData models.

Notes
- Phase 5.1, 5.1.1, 5.1.2, and 5.1.3 are closed as the full Trend Card delivery track.
- Trend Card remains part of the load domain and separate from Readiness.

## v0.4.4.1 - 2026-03-11

## Phase 4.4.1 — Workout History Dedup & Recompute

Added
- duplicate-audit evidence and source-precedence decision artifacts for the historical workout dedupe subset.
- staging cleanup evidence with keep/remove traceability, bounded recompute, and post-cleanup validation.
- production freeze/preflight artifacts:
  - `phase4_4_1_prod_duplicate_audit_with_policy.json`
  - `phase4_4_1_prod_cleanup_plan.json`
  - `phase4_4_1_prod_cleanup_plan.csv`
  - `phase4_4_1_prod_cleanup_plan.sha256`

Improved
- operational confidence around historical dedupe by validating the subset in staging before any production action.
- production decision hygiene by freezing and checksumming the candidate subset before any mutation.

Notes
- Phase 4.4.1 is now formally closed.
- staging cleanup was executed and validated successfully.
- production cleanup was not needed because production already matched the residual post-cleanup manual-review surface and had `0` auto-cleanup eligible clusters under the approved policy.
- Phase 4.4 remains on hold / conditional.

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
