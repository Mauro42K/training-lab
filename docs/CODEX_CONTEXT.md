# Training Lab Codex Context

## Repo
- Training Lab is the source repository for the product foundation.
- This file is the source of truth for every Codex run.

## Current Phase
- **Phase 5.7 — Deep QA / Home integration** (**Open**)

- Phase 5.6 — Data Completeness / Confidence is closed.
- The phase resolved Home-wide trust/completeness with minimal client-side alignment:
  - canonical `complete / partial / missing` normalization
  - block-level fallback and warning behavior
  - `missing` treated as fallback-only, never as a real-looking value
  - `partial` preserving useful content instead of hiding it
- The implementation stayed on the client and did not introduce a new transversal `home_summary` object or backend contract expansion.
- Phase 5.6.1 is closed. It was an iPhone-first UX/UI polish subphase only:
  - dark premium cohesion
  - reduced nested cards
  - Drivers visual refinement
  - Recommended Today editorial refinement
  - Core Metrics less dashboard-like
  - Trend Card spacing, hierarchy, and balance
- Phase 5.6.1 did not reopen backend, contracts, trust semantics, or Coach / planner / chat.
- Phase 5.6.1 delivered the reusable Home compact-layout pattern:
  - compact explainability columns for `Drivers`
  - compact supporting snapshots for `Core Metrics`
  - reduced vertical stack height on iPhone

- `Readiness v1` is now implemented as a read-time layer on top of the existing daily domains and exposed through `GET /v1/home/summary`.
- `daily_recovery` remains the canonical consolidated-input domain; it was not turned into a persisted final score.
- The public readiness contract now exposes:
  - `score`
  - `label`
  - `confidence`
  - `completeness_status`
  - `inputs_present`
  - `inputs_missing`
  - `model_version`
  - `has_estimated_context`
  - `trace_summary`
  - `explainability`
- Readiness v1 uses the approved primary inputs and weights:
  - Sleep `40%`
  - HRV `35%`
  - RHR `25%`
- Baselines are resilient to sparse history:
  - HRV `28d`
  - RHR `28d`
  - Sleep `7–14d`
  - isolated missing days degrade `confidence`, not the whole model
- recent exertion/load remains a bounded secondary context only:
  - penalty-only
  - capped
  - excluded from readiness completeness math
- iOS now fetches `/v1/home/summary` and hosts the Readiness Hero at the top of `TrainingLoadScreen` as the pragmatic temporary Home surface.
- The hero was implemented against the approved Home Figma direction:
  - dominant score
  - centered premium label
  - dark premium base surface
  - atmospheric wash
  - confidence visually secondary
  - semantic theming keyed by `label`
- Theme mapping is now stable in UI:
  - `Ready` -> premium green
  - `Moderate` -> premium amber
  - `Recover` -> premium coral/red
- Guardrails preserved:
  - no load/capacity narrative inside the hero
  - `Trend Card` remains `Load vs Capacity`
  - `Recommended Today` was not absorbed
  - no Coach semantics were introduced
- Validation completed:
  - backend unit/API tests passed locally
  - iOS device build passed
  - iOS simulator build passed
  - simulator launch passed on `Codex iPhone 17`
  - visual validation of the hero completed before release closure
- Initial production DB audit confirmed the first blocker was not the readiness model but missing physiological ingest.
- Phase 5.2.1 is resolved and no longer an active subphase.
- Its delivered scope was:
  - iPhone HealthKit permission flow for sleep / HRV / RHR
  - client ingest to `POST /v1/ingest/sleep` and `POST /v1/ingest/recovery-signals`
  - physiology-specific bootstrap / incremental sync state
  - minimum sync observability for counts, latest dates, and bootstrap completion
- The key product note remains:
  - enabling ingest does not guarantee `complete` readiness immediately
  - the first real output may still be `partial` or `insufficient` while baselines consolidate
- Subsequent real-device validation and production DB/API audit confirmed `Phase 5.2.1` succeeded:
  - production now has real rows in `sleep_sessions`, `recovery_signals`, `daily_sleep_summary`, and `daily_recovery`
  - `daily_activity` can still be empty without blocking Readiness v1
  - production deploy parity for the backend was resolved after promoting the readiness/home-summary changes
  - `/v1/home/summary` now returns real `readiness`, not `null`
  - `/v1/training-load` now returns the current shape with `history_status`, `semantic_state`, `latest_load`, and `latest_capacity`
- Readiness has now been validated against real production data:
  - the active production user reached `complete` readiness input coverage on recent days
  - a real observed day returned `score=35`, `label=Recover`, `confidence=0.93`
  - that low score was coherent with poor sleep and very low HRV against baseline, while RHR was supportive and recent load context applied no penalty
- `Phase 5.2` and `Phase 5.2.1` are therefore complete enough to be treated as closed inputs for `Phase 5.3 — Core Metrics`.

### Phase 5.3 Current Summary
- `GET /v1/home/summary` now extends the Home contract with `core_metrics`.
- `core_metrics` exposes:
  - `seven_day_load`
  - `fitness`
  - `fatigue`
  - `history_status`
- The block reuses the existing `training-load` domain:
  - `seven_day_load` = trailing 7-day load sum
  - `fitness` = Home UI naming for internal `Capacity / CTL`
  - `fatigue` = existing `ATL` from the load model
  - `history_status` = same sufficiency state already used by `training-load`
- No load formulas were duplicated in client.
- iOS now renders a separate compact `Core Metrics` block between:
  - the `Readiness` hero
  - the `Load Trend` section
- The final visual pass aligned the block back to the shared design-system primitives:
  - `DSSectionHeader` for section hierarchy
  - `DSMetricSnapshotCard` for the compact multi-metric snapshot
  - `DSCard` as the base supporting surface primitive
  - `DSMetricPill` only for secondary history/trust states
- The Gallery now exposes the supporting snapshot pattern directly so Home does not need to improvise multi-metric supporting cards ad hoc.
- The block now stays visually coherent with the Home hero/trend language without relying on ad-hoc custom surface recipes.
- Core Metrics now reuses a stable Home load snapshot so:
  - `7-Day Load` matches the trailing 7-day sum
  - `Fitness` aligns with the current load-domain `Capacity / CTL`
  - `Fatigue` aligns with the current load-domain `ATL`
- Guardrails preserved:
  - Core Metrics remains separate from Readiness
  - Core Metrics remains separate from the Trend Card
  - no Coach or Recommended Today semantics were introduced
- Validation closed:
  - backend/API tests passed locally
  - iOS and macOS builds passed locally
  - production now returns real `core_metrics`
  - macOS visual QA confirmed `Readiness Hero + Core Metrics + Load Trend` together in the Home host

### Phase 5.4 Current Summary
- `GET /v1/home/summary` now extends `readiness` with a nested `explainability` block instead of pushing explainability logic into the client.
- `readiness.explainability` exposes:
  - `completeness_status`
  - `confidence`
  - `model_version`
  - `items[]`
- Every visible explainability item now carries:
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
- Visible v1 scope is constrained to the approved taxonomy:
  - primary drivers:
    - `sleep`
    - `hrv`
    - `rhr`
  - secondary context:
    - `recent_exertion`
- Public visible roles are now only:
  - `primary_driver`
  - `secondary_context`
- Public statuses are now:
  - `measured`
  - `estimated`
  - `proxy`
  - `missing`
- Guardrails preserved:
  - `recent_exertion` remains secondary context only
  - `Exertion` is the UI label, but backend key remains `recent_exertion`
  - `Movement` and secondary strength context stay out of the v1 Home surface
  - score math and readiness weighting were not changed
- `trace_summary` remains in the readiness contract for compatibility, but is now derived from the same explainability evaluation path so score/trace/explainability cannot drift.
- iOS Home now renders a distinct `Drivers` block between:
  - the `Readiness` hero
  - `Core Metrics`
- The drivers block reuses a governed Design System primitive instead of a bespoke Home card:
  - `DSExplainabilityCard`
  - Gallery preview added for the pattern
- Visual hierarchy is now explicit in Home:
  - Hero remains dominant
  - `Sleep`, `HRV`, and `RHR` carry the main explainability weight
  - `Exertion` remains visually quieter as context
  - `Core Metrics` and `Trend Card` stay separate from explainability
- Validation completed locally:
  - backend unit/API tests passed
  - iOS simulator build passed
  - macOS build passed
  - visual QA completed on iPhone simulator and macOS host using a local mock of the approved Home contract to verify the new block before backend rollout

- Production deploy parity for 5.4 was later completed and verified on the live API.
- `GET /v1/home/summary` in production now serves `readiness.explainability`, not just the local/mock contract.
- Real production validation covered both:
  - a complete readiness day with measured primaries and populated explainability
  - a missing-primaries day where explainability still renders coherent missing/not-used states without faking readiness
- Visual validation was completed against real app data with the full Home stack visible together:
  - Readiness Hero
  - Drivers / Explainability
  - Core Metrics
  - Load Trend
  - Trend Card
- Phase 5.4 is therefore closed on both implementation and real-environment validation, not only on local mock validation.

### Phase 5.5 Current Summary
- `GET /v1/home/summary` now includes a stable `recommended_today` guidance block in the Home contract.
- The structured backend contract remains intentionally minimal:
  - `state`
  - `confidence`
  - `reason_tags`
  - `guidance_only`
- Home order is now:
  - `Readiness Hero`
  - `Drivers / Explainability`
  - `Recommended Today`
  - `Core Metrics`
  - `Load Trend`
  - `Trend Card`
- The temporary fixed copy has been replaced by a controlled Spanish copy-generation layer in the iOS client.
- Copy generation currently uses only approved structured inputs:
  - `state`
  - `confidence`
  - `reason_tags`
  - `guidance_only`
- The generation layer is deterministic and templated, not LLM-backed:
  - backend remains the source of truth for recommendation structure
  - no backend contract expansion was required for copy generation
  - no OpenAI API key is used for this 5.5 copy layer
  - no runtime AI / Coach / planner integration was introduced
- Guardrails preserved:
  - guidance-only
  - short premium copy
  - no planner
  - no coach
  - no chat
  - no workout prescription
  - no adaptive planning
  - no medical framing
  - no contradiction with readiness/explainability context
- Future work note:
  - a later phase may evaluate LLM-backed copy only if it adds measurable value without breaking these guardrails or expanding into Coach scope
- Validation completed locally:
  - production backend already serves `recommended_today`
  - iOS build passed
  - macOS build passed
  - visual QA used the Home preview stack plus state-variant previews

### Phase 5.6 Closure Summary
- Home trust/completeness was resolved as a client-facing normalization problem in this phase.
- The canonical Home states are:
  - `complete`
  - `partial`
  - `missing`
- Decision for this phase:
  - align existing blocks semantically on the client
  - do **not** add a new transversal `home_summary` object
  - do **not** expand the backend contract just to carry trust metadata
- Result:
  - `Readiness Hero` shows score on `complete` and `partial`, with degraded trust on `partial`
  - `Drivers` and `Recommended Today` must render a soft fallback instead of disappearing when signal is unavailable
  - `Core Metrics` and `Load Trend` should treat `insufficient_history` as `partial`
  - `missing` must remain a fallback state only, never a real-looking value

### Phase 5.6.1 Current Summary
- Home polish is now scoped as a pure visual iteration.
- Supporting blocks now favor flat Home panels with embedded metric/explainability content instead of stacked nested cards.
- Pending UX/UI targets:
  - reduce nested-card feel
  - make Drivers less dense
  - give Recommended Today more editorial intent
  - make Core Metrics feel less dashboard/tabular
  - refine Trend Card spacing, hierarchy, and balance
  - improve dark premium cohesion on iPhone without changing semantics

### Phase 5.1.3 Closure Summary
- macOS and iPhone were confirmed to use the same effective `baseURL`; the divergence came from separate local caches and refresh/fallback behavior, not from different backends.
- `Today` no longer attaches to the last training-load point unless that point is actually the current calendar day.
- `Load Trend` totals now use calendar windows anchored to today instead of raw suffix slices.
- The client now tolerates the legacy `training-load` response shape still returned by production and reconstructs missing `Capacity`, `history_status`, `latest_*`, and `semantic_state` values instead of failing decode and falling back to stale cache by accident.
- Training-load fetch diagnostics now capture:
  - effective `baseURL`
  - remote fetch attempt
  - remote failure
  - cache fallback
  - latest point date
  - cache update timestamp
- The UI now surfaces stale load data honestly instead of presenting old cache points as if they were current.
- The confirmed diagnosis is:
  - macOS and iPhone use the same backend/baseURL
  - they can still show different dates because each platform owns a separate local cache
  - remote refresh could also fail on the old payload shape before the client-side compatibility fallback was added
  - when remote refresh fails, each platform falls back to its own cache state
  - the previous `Today` labeling bug amplified that divergence visually
- Final local macOS verification also required normalizing the target bundle identifier so the app could launch consistently during validation.

### Phase 5.1.2 Closure Summary
- macOS no longer crashes on launch when a legacy local SwiftData store is present.
- `CachedSyncState.hasCompletedRealHealthKitIngest` was hardened for legacy migration by making the persisted field migration-safe and normalizing missing legacy values back to `false` at load time.
- Review of the remaining local persistence models found no other new mandatory cache fields with the same unresolved migration risk:
  - `CachedTrainingLoadPoint` had already been hardened during Phase 5.1.
  - `CachedWorkout` and `CachedDailySummary` did not add equivalent new required fields.
- Validation passed for:
  - clean macOS local-store creation.
  - legacy macOS store migration.
  - iOS simulator build sanity check.

### Phase 5.1.1 Closure Summary
- The visible iPhone app name now resolves to `Training Lab`.
- The target now ships with a real `AppIcon` asset set instead of the generic placeholder icon.
- Validation passed in simulator and on real iPhone:
  - app installs and launches successfully
  - SpringBoard shows `Training Lab`
  - the icon is no longer the generic white/default tile
- This was intentionally kept as a small identity baseline only; no product or architecture changes were introduced.

### Phase 5.1 Closure Summary
- `Capacity` is now formally implemented inside the load domain.
- `Capacity = Fitness (CTL)` in v1, derived on top of the existing `DailyLoad` foundation.
- `semantic_state` is now server-derived from `ATL vs CTL`, not from the last daily load in isolation.
- `history_status` is now exposed as:
  - `available` = 42+ days
  - `partial` = 14–41 days
  - `insufficient_history` = 1–13 days
  - `missing` = 0 days
- `GET /v1/training-load` now returns:
  - `items[]` with `load`, `capacity`, and temporary `trimp` alias
  - `history_status`
  - `semantic_state`
  - `latest_load`
  - `latest_capacity`
- iOS now hosts a reusable `Load vs Capacity` card in `TrainingLoadScreen` using the design-system chart/card primitives.
- `partial` history explicitly communicates that the signal is still consolidating.
- The final visual polish pass is closed:
  - `Capacity` renders as a real daily series, not a flat replicated line
  - `partial` copy density was reduced
  - `insufficient_history` de-emphasizes precision
  - `missing` keeps continuity inside the same card component
- Legacy cache hardening is closed:
  - SwiftData migration no longer fails when old cached rows do not yet contain `capacity`
  - legacy cache fallback reconstructs `history_status` from real cached load coverage
  - legacy cache fallback reconstructs `Capacity` from cached load/TRIMP history instead of showing false zero capacity when history exists

### Upstream Phase 5.0 Context
- Home documentary investigation/alignment completed.
- `Readiness` is now the governing Home hero term.
- `Battery` remains only as a controlled historical/documentary alias.
- `Recommended Today` is frozen as contextual guidance-only.
- Home `Trend Card` remains **Load vs Capacity**.
- Official Phase 5 order is now:
  - 5.0 investigation / decisions / alignment
  - 5.1 Trend Card (Load vs Capacity)
  - 5.2 Hero Readiness
  - 5.3 Core Metrics
  - 5.4 Drivers / Explainability
  - 5.5 Recommended Today
  - 5.6 Data Completeness / Confidence
  - 5.7 Deep QA / Home integration

## Previous Phase
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
- **Phase 5.7 — Deep QA / Home integration** (**Current / active**)
- Focus:
  - integrate the already delivered Home blocks as a single surface,
  - validate state transitions, missing-data days, and cross-platform presentation,
  - keep the current Home hierarchy and trust semantics intact.

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
- Readiness transparent.
- TRIMP chart remains the validated MVP load anchor, not the final Home hero.

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
- For any new UI block, DesignSystem + Gallery + this CODEX_CONTEXT must be treated as mandatory source material before implementation.

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
