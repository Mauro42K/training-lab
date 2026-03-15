

# Training Lab — Roadmap (Source of Truth)

**Project name:** Training Lab  
**Repo (GitHub):** `training-lab`  
**Primary platforms:** iPhone + Mac (SwiftUI, single codebase)  
**Source of truth for training/health data:** Apple Fitness / Apple Health (HealthKit)  
**Product goal:** Running-first dashboard → Athlytic-like analytics → AI Coach (Runna-like)  

---

## Governance

### Non-negotiables
- **Design-first is mandatory:** no feature screens are coded until the Design System (tokens + components + layout rules) is defined and approved.
- **Readiness is transparent:** any readiness score shown to the user must include a clear **breakdown (“drivers”)** and a **data completeness** indicator.
- **Running-first, multi-sport-aware:** running is the primary narrative, but bike/strength/walk must be represented without distorting endurance load.
- **Zero confusion:** avoid duplicated data, hidden assumptions, and opaque scores.

### Tabs (IA / v0.2)
- **Home** (moment of truth: before/after training)
- **Trends** (long-range charts & comparisons)
- **Workouts** (history + workout detail)
- **Body** (weight & body measurements; replaces Journal)
- **More** (settings, permissions, calibration)
- **Coach** (future)

### MVP anchor
- **TRIMP chart usable from day 1** as the MVP load anchor before final Home composition.

---

## Closed Phases Summary (Phase 0-3)

### Phase 0 — Automation & Infrastructure Bootstrap
- Repo, CI, VPS backend scaffold, domain/TLS baseline, and deploy/runbook foundation were closed.
- Operational detail now lives in [STACK_INFRA.md](/Users/mauro/Training-lab/docs/STACK_INFRA.md) and [DEPLOY_RUNBOOK.md](/Users/mauro/Training-lab/docs/DEPLOY_RUNBOOK.md).

### Phase 1 — Product Definition Pack + Metrics Inventory
- PRD, data sources, metrics catalog, glossary, and changelog foundations were frozen.
- Product semantics and metric governance now live in [PRD.md](/Users/mauro/Training-lab/docs/PRD.md), [METRICS_CATALOG.md](/Users/mauro/Training-lab/docs/METRICS_CATALOG.md), [GLOSARIO.md](/Users/mauro/Training-lab/docs/GLOSARIO.md), and [DATA_SOURCES.md](/Users/mauro/Training-lab/docs/DATA_SOURCES.md).

### Phase 2 — Design System & Layout
- Tokens, layout rules, reusable components, gallery, and multiplatform visual QA were closed.
- Visual-system detail now lives in [DesignSystem.md](/Users/mauro/Training-lab/docs/DesignSystem.md), [Phase2_Checklist.md](/Users/mauro/Training-lab/docs/Phase2_Checklist.md), and [Phase2_VisualQA.md](/Users/mauro/Training-lab/docs/Phase2_VisualQA.md).

### Phase 3 — HealthKit Access & Local Data Model
- HealthKit access, online-first backend foundation, idempotent ingest contracts, and shell integration were closed.
- Detailed evidence remains in [Phase3_QA.md](/Users/mauro/Training-lab/docs/Phase3_QA.md) and [docs/qa/phase3/](/Users/mauro/Training-lab/docs/qa/phase3).

---

## Phase 4.0 — TRIMP Engine v1 + Home TRIMP Hero Card (MVP)

**Status:** CLOSED (2026-03-06 America/New_York)  
**Goal:** Deliver the first real value: TRIMP chart usable from day 1.

**Closure summary:**
- Backend source of truth for TRIMP delivered:
  - TRIMP engine v1.
  - recompute pipeline.
  - endpoint `GET /v1/training-load`.
  - backfill operativo por lotes para histórico.
- iOS integration delivered:
  - `TrainingLoadScreen` funcional (temporal).
  - filtros por deporte (`all/run/bike/strength/walk`).
  - chart diario TRIMP de 28 días.
  - highlight de today.
  - tap en día abre detail sheet con soporte multi-session.
- Critical bug fixed:
  - mismatch de `Today` entre UI y backend.
  - validación final: `today_local = 2026-03-06` y último item serie `date = 2026-03-06` (coinciden).

### Deliverables (Delivered)
- TRIMP calculation v1 (documented in `docs/METRICS_CATALOG.md`).
- Daily TRIMP aggregation:
  - All / Run / Bike / Strength / Walk filters.
  - last 28 days.
- API contract v1:
  - `GET /v1/training-load?days=28&sport=...`
- iOS temporary Training Load screen:
  - summary badges (today, 7d, 28d),
  - daily bar chart,
  - filter control,
  - day detail sheet.

### DoD (Closed)
- TRIMP chart loads fast from backend/cache path.
- Filter changes update chart correctly.
- Day Sheet shows correct sessions and totals.

### QA (Closed)
- Multi-session day (run + strength): PASS.
- No-HR workouts (fallback rules): PASS.
- Today alignment UI vs backend: PASS.
- Evidence:
  - `docs/Phase4_QA.md`
  - `docs/qa/phase4/README.md`

### Phase 4.1 — Training Load UX Polish
**Status:** CLOSED (2026-03-06 America/New_York)  
**Goal:** Improve visual quality and interaction stability of temporary Training Load screen before Home integration.

Delivered scope:
- temporal axis polish for fast 28d reading.
- summary row hierarchy and filter feedback refinement.
- chart state polish (`selected > today > hover > normal`), baseline/growth-from-bottom fix, sparse-data rendering improvements.
- robust hover/click/detail interaction, including stable macOS close flow.
- medium decoupling of chart presentation layer for future Home TrendCard reuse.
- real macOS compatibility and runtime config persistence via `xcconfig` + bundle config.
- cache scope isolation by effective `baseURL` to avoid cross-environment cache mix.

Guardrail (explicit):
- Phase 4.1 closes UX polish + multiplatform stability + runtime config only.
- Real HealthKit / Apple Fitness ingest alignment is **not** resolved in 4.1.
- That work moves formally to **Phase 4.2**.

### Phase 4.2 — HealthKit Real Ingest Enablement
**Status:** COMPLETED  
**Goal:** Ensure real Apple Fitness/HealthKit workouts are reliably ingested end-to-end and reflected in training-load calculations.

Completion summary:
- real HealthKit bootstrap ingest validated on iPhone.
- 3436 workouts successfully ingested from the historical HealthKit dataset.
- backend persistence verified on PostgreSQL.
- training-load endpoints now produce real TRIMP values.
- incremental sync confirmed after bootstrap completion.
- post-ingest refresh `422` fixed by correcting `GET /v1/daily` date formatting.
- iOS 18 HealthKit deprecation resolved by replacing `totalEnergyBurned` with `HKWorkout.statistics(for: .activeEnergyBurned)`.

### Phase 4.3 — Staging Environment & Environment Separation
**Status:** CLOSED (2026-03-10 America/Mexico_City)  
**Goal:** Introduce a proper **staging environment** separated from production to allow safe experimentation, schema evolution, and ingest testing without risking the primary dataset.

Context:
- Phase 4.2 enables real HealthKit ingest with Mauro's real historical dataset.
- That dataset becomes the **initial production baseline** for Training Lab.
- From this point forward, development must not run directly against production.

High‑level architecture after this phase:

Production:
- API: `api.training-lab.mauro42k.com`
- Database: PostgreSQL production (`training-lab-postgres`)

Staging:
- API target: `api-staging.training-lab.mauro42k.com`
- Active fallback URL: `http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io`
- Database: PostgreSQL staging (`training-lab-postgres-staging`)

Completion summary:
- separate Coolify `staging` environment created for project `training-lab`
- separate staging PostgreSQL created and cloned one-shot from production
- comparative counts after clone:
  - `workouts = 3436`
  - `workout_load = 3173`
  - `daily_load = 9720`
- separate staging API service created and healthy
- `/health` now returns explicit `environment` so prod vs staging can be distinguished safely
- iOS runtime config now supports explicit `production | staging | local`
- debug builds show a visible runtime environment badge to avoid ambiguity
- canonical staging domain is operational:
  - `https://api-staging.training-lab.mauro42k.com`
- DNS resolves correctly to the VPS and TLS is valid
- staging `/health` and `/v1/training-load` respond `200` through the canonical host

#### Deliverables
- **Staging API service** deployed in Coolify (separate service from prod).
- **Database duplication**:
  - initial one-shot logical clone of production PostgreSQL into staging PostgreSQL.
- **Environment configuration separation**:
  - staging and production use different environment variables.
- **Runtime configuration in iOS app**:
  - ability to target `staging` or `production` API baseURL.
- **Documentation updates**:
  - `docs/STACK_INFRA.md` updated with both environments.
  - `docs/DEPLOY_RUNBOOK.md` includes staging deploy flow.

#### DoD
- Staging database created and populated from production baseline.
- App can connect to staging environment without affecting production data.
- Production ingest and metrics remain unchanged.
- Staging is verifiable without ambiguity by:
  - distinct service/container in Coolify
  - distinct PostgreSQL resource
  - `/health` returning `environment=staging`

- canonical staging DNS and TLS operational on `api-staging.training-lab.mauro42k.com`

#### QA
- Confirm staging API responds correctly to `/health`.
- Verify staging DB queries return expected cloned data.
- Validate that a staging ingest or recompute does **not** modify production DB.
- Compare prod vs staging counts for:
  - `workouts`
  - `workout_load`
  - `daily_load`

#### Guardrails
- Production database must never be modified directly during feature development.
- All schema experiments, migrations, and ingest tests must run in staging first.
- Production deploys must come from validated staging builds.
- iOS debug builds must show the active environment explicitly when not running default production.

### Phase 4.4 — Workout Reconciliation & Historical Cleanup
**Status:** ON HOLD / CONDITIONAL  
**Goal:** Keep the broader historical reconciliation umbrella available without making it the active execution phase.

Context:
- users may discover duplicated workouts in Apple Fitness history.
- when a workout is deleted in HealthKit, the backend should eventually reflect that change.
- this remains the broader conceptual phase for historical reconciliation, cleanup, and parity with HealthKit history.

Potential scope if reactivated:
- detect workouts that no longer exist in HealthKit.
- allow backend reconciliation.
- mark workouts as deleted or remove them.
- trigger recalculation of derived metrics.
- support duplicate cleanup when the problem exceeds a targeted remediation subphase.

Reactivation rule:
- Phase 4.4 does not return as the primary immediate phase.
- It only reactivates if Phase 4.4.1 reveals broader corruption/scope than targeted cleanup can safely handle.
- It also reactivates if true deletion/reconciliation requirements become validated needs beyond duplicate remediation.

Guardrails:
- must be tested in STAGING first.
- must not risk production data corruption.
- must maintain idempotency of ingest pipeline.

#### Phase 4.4.1 — Workout History Dedup & Recompute
**Status:** CLOSED (2026-03-11 America/Mexico_City)  
**Goal:** Resolve historical duplicate workouts already present in the dataset through a surgical cleanup and recompute path, without reopening full Phase 4.4 by default.

Scope:
- duplicate audit
- exact canonical dedupe rule
- impact estimation
- staging-first cleanup
- recompute
- post-cleanup validation
- escalation gate to reload if needed

Non-goals:
- no full Phase 4.4 reopening
- no new user-facing features
- no provider abstraction
- no production reset as first move

Deliverables:
- duplicate audit report
- canonical dedupe rule
- backup/snapshot checkpoint of affected staging set before cleanup
- cleanup procedure/runbook
- recompute procedure
- manual-review report for ambiguous clusters
- final decision: cleanup sufficient vs reload escalation

Risks:
- false-positive dedupe
- incomplete recompute
- too-weak identity rule

Exit criteria:
- affected set quantified
- exact rule frozen
- ambiguous clusters excluded from auto-cleanup
- staging cleanup validated
- production path explicitly chosen

Execution approach:
- audit first, cleanup second
- backup/snapshot of affected staging rows before mutation is mandatory
- strongest stable source identity must be frozen as an exact rule before execution
- ambiguous clusters are excluded from auto-cleanup and sent to report/manual review

Decision note:
- Preferred strategy: targeted cleanup first
- Escalation: full reload only if audit/validation fails viability thresholds

Closure summary:
- duplicate audit completed with explicit source-precedence policy for the dominant conflict pairs.
- targeted cleanup was executed and validated in staging only.
- production freeze/preflight confirmed the correct production target and found `0` auto-cleanup eligible clusters.
- production matched the residual post-cleanup manual-review surface already validated in staging.
- no production cleanup was needed for the currently approved eligible subset.

### Phase 4.5 — Daily Domains & Summary Contracts (Apple-first)
**Status:** CLOSED (2026-03-11 America/Mexico_City)  
**Goal:** Establish the minimum Apple-first daily-domain foundation that will unblock Home and Trends without adopting a generic multi-provider architecture.

Closure decisions carried into this phase:
- do not convert Training Lab into a generic platform,
- do not adopt `open-wearables` as the architectural base,
- do not expand `GET /v1/daily` to cover heterogeneous daily domains,
- do not introduce Redis/Celery/OAuth/webhooks/portal web,
- do not persist full raw blobs,
- keep Phase 4.4 on hold and out of active execution scope.

#### Deliverables
- Documentary opening and semantic freeze for:
  - `sleep_sessions`
  - `daily_sleep_summary`
  - `daily_recovery`
  - `daily_activity`
  - `body_measurements`
- Backend foundation + migrations delivered for:
  - normalized daily-domain storage
  - derived daily summaries
  - affected-date recompute
- Vertical slices delivered for:
  - sleep
  - daily activity
  - body measurements
  - daily recovery
- Query contracts delivered:
  - `GET /v1/daily-domains/sleep`
  - `GET /v1/daily-domains/activity`
  - `GET /v1/daily-domains/recovery`
  - `GET /v1/daily-domains/body-measurements`
  - `GET /v1/home/summary`
- Explicit cross-domain rules for:
  - `local_date`
  - timezone
  - completeness
  - provenance
  - idempotency
  - affected-date recompute
- Layer model frozen as:
  - normalized -> derived -> query
- `daily_recovery` defined as consolidated inputs only:
  - no final score `0-100`
- explicit emission/completeness rules for `daily_recovery`:
  - emit only if sleep or HRV or RHR exists
  - `complete` requires sleep + HRV + RHR
  - `missing` means no row emitted
- explicit timezone and `local_date` semantics by domain
- explicit `main_sleep` / `nap` rules
- explicit daily canonicalization for `body_measurements`
- minimum provenance frozen as:
  - `provider`
  - `source_count`
  - `has_mixed_sources`
  - `primary_device_name`

#### DoD
- Phase 4.5 has a primary source-of-truth document in `docs/`.
- Naming is frozen and consistent across roadmap, context, data-sources, and metrics docs.
- Scope boundaries and anti-scope-creep rules are explicit.
- Relation to Phase 4.4 on hold is explicit and non-ambiguous.
- `missing` is explicitly represented as no emitted derived row.
- `primary_device_name` resolution is explicitly constrained to confidence-only, without complex heuristics.
- staging and production validated after Alembic migration `20260311_01`.
- iPhone smoke test validated runtime alignment with production host and no debug badge in production.

#### QA
- Documentation review for naming and scope consistency.
- Local automated QA: PASS.
- staging smoke validation post-migration: PASS.
- production sanity validation post-migration: PASS.
- Validate explicit handling of:
  - overnight sleep assignment
  - naps without reliable stages
  - HRV/RHR missing data
  - steps-only day
  - weight present with body-composition absent
  - `null != 0`
  - timezone/local-date shifts
  - `missing` without empty rows
  - `primary_device_name = null` when not confidently resolvable

#### Guardrails
- No readiness final.
- No battery final.
- No baselines `7d/28d`.
- No scoring.
- No premium explainability layer.
- No generic timeseries endpoint.
- No multi-provider abstractions.
- No extra async infrastructure in this phase.

#### Handoff
- Phase 4.4 remains ON HOLD and is not reopened by this closure.
- The documentary alignment layer for Home is now closed as **Phase 5.0**.
- The next executable Home block is now **Phase 5.2 — Hero Readiness**.
- Deferred-by-decision, not bugs:
  - no recovery score yet
  - no readiness/battery final
  - no baselines 7d/28d
  - no body daily derived table
  - no generic timeseries

---

## Phase 5 — Home v1 (committee-aligned rollout)

**Status:** ACTIVE  
**Goal:** Deliver Home in the approved execution order, keeping PRD semantics, `Readiness` naming, and load-domain contracts aligned across product, metrics, and implementation.

### Phase-level guardrails
- PRD is the source of truth for Home semantics and product intent.
- `docs/METRICS_CATALOG.md` is the source of truth for metrics, models, fallbacks, completeness, and edge cases.
- `docs/GLOSARIO.md` is the source of truth for UI terminology.
- Phase 2 documentation (`docs/DesignSystem.md`, `docs/Phase2_Checklist.md`) remains the source of truth for reusable UI primitives and layout rules.
- Phase 4.5 documentation (`docs/PHASE4_5_DAILY_DOMAINS_SUMMARY_CONTRACTS.md`) remains the source of truth for daily-domain contracts and `GET /v1/home/summary` composition rules.
- Figma Home prototype is a visual reference only; it does not redefine functional meaning or metric semantics.
- `Readiness` is the governing Home hero term. `Battery` remains only as a historical/documentary alias where legacy references still exist.
- `Recommended Today` remains a contextual guidance block only. It does not absorb Coach scope.
- `Trend Card` remains **Load vs Capacity**. `Capacity` belongs to the load domain and is formally defined/implemented in **Phase 5.1**.
- Every Phase 5 subphase follows: **Definition -> Plan -> Implement -> QA**.

### Phase 5.0 — Home investigation / decisions / alignment
**Status:** CLOSED (2026-03-13 America/New_York)  
**Goal:** Close the documentary investigation and committee alignment required before Home implementation starts.

**Closure summary**
- Required documentary investigation was completed across PRD, Metrics Catalog, Glossary, Roadmap, Design System, and Phase 4.5 contracts.
- `Readiness` was approved as the governing Home hero term.
- `Battery` was demoted to controlled historical/documentary alias status.
- `Recommended Today` was bounded as guidance-only contextual output using `Readiness + recent load + confidence/completeness`.
- `Trend Card` was confirmed as **Load vs Capacity** and `Capacity` was assigned to the load domain for definition/implementation in Phase 5.1.
- The old MVP TRIMP hero chart was reclassified as an MVP load anchor, not the final Home hero.
- The official execution order for Home was frozen.

**Definition of Done**
- Naming ambiguity that would block Home execution is closed.
- The Phase 5 sequence is explicit and approved.
- The next implementation block is unambiguous: **Phase 5.1 — Trend Card (Load vs Capacity)**.

**QA focus**
- Documentary consistency across Roadmap, Metrics Catalog, Glossary, Context, and PRD.

### Phase 5.1 — Trend Card (Load vs Capacity)
**Status:** CLOSED (2026-03-13 America/New_York)  
**Goal:** Define and implement the first final Home block: `Load vs Capacity`.

**Closure summary**
- `Capacity` was formalized inside the load domain as `Fitness (CTL)` in v1.
- `GET /v1/training-load` now returns `load`, `capacity`, `history_status`, `semantic_state`, `latest_load`, and `latest_capacity`.
- `semantic_state` is server-derived from `ATL vs CTL`, with centralized heuristics for `Below capacity`, `Within range`, `Near limit`, and `Above capacity`.
- Calendar coverage states are now explicit: `available`, `partial`, `insufficient_history`, `missing`.
- A reusable `Load vs Capacity` card now exists in the current iOS load surface using the existing chart system, without reintroducing the old TRIMP hero framing.
- The final card pattern is now stable:
  - `load bars + capacity line`
  - compact semantic reading
  - polished `partial`, `insufficient_history`, and `missing` states
- Local cache hardening is closed:
  - SwiftData migration no longer fails on legacy cached training-load rows
  - legacy cache fallback now reconstructs `history_status` from real cached load coverage instead of degrading to `missing`
  - legacy cache fallback now reconstructs `Capacity` from cached load history when `capacity` was not persisted yet, avoiding false zero lines in the chart

**Why this block exists**
- It carries forward the validated load narrative from the MVP while moving Home toward its final PRD structure.

**Scope**
- Define `Capacity` as a formal metric inside the load domain using the existing training-load model as the foundation.
- Implement the Home Trend Card as `Load vs Capacity`.
- Resolve the MVP inheritance by moving the temporary TRIMP hero narrative into the final Home Trend Card layer.

**Main dependencies**
- Phase 5.0 closure
- TRIMP, Load, Training Load foundations from Phases 4.0 / 4.1
- `GET /v1/training-load`
- Phase 2 chart system
- `docs/METRICS_CATALOG.md`

**Deliverables**
- `Capacity` documented in the Metrics Catalog with justified scope and formal ownership in the load domain
- Extended `GET /v1/training-load` contract
- Reusable iOS Trend Card delivery on top of the existing load screen as the temporary host

**Definition of Done**
- `Capacity` is explicitly documented before implementation is considered complete.
- Trend Card semantics are stable and no longer rely on the temporary MVP hero framing.
- API contract, history/completeness states, and iOS presentation are all validated.
- Legacy cache migration and fallback behavior no longer create contradictory or false-zero Home load states on device.

**QA focus**
- Today alignment
- Sparse load history
- Calendar coverage vs real rest days
- Visual consistency with Phase 2 charts
- Legacy cache migration and offline fallback on real device

### Phase 5.1.1 — App Identity Baseline
**Status:** CLOSED (2026-03-13 America/New_York)  
**Goal:** Remove the remaining demo shell identity before opening the next Home block.

**Closure summary**
- The visible iPhone app name now resolves to `Training Lab` instead of the previous demo label.
- The iOS app now ships with a configured `AppIcon` asset set built from the approved product image source.
- Validation in simulator and real iPhone confirmed:
  - the icon is no longer the generic white placeholder
  - the visible app name is `Training Lab`
  - the app installs and launches without asset-catalog or signing regressions from this identity update

**Why this block exists**
- The product should no longer present itself as a design-system demo before Home v1 continues.

**Scope**
- Visible iOS app name
- Real iPhone app icon asset
- Validation on simulator and iPhone

**Definition of Done**
- Demo-facing iPhone identity is removed.
- The app icon is configured through the real asset catalog path used by the target.
- The next product phase remains **Phase 5.2 — Hero Readiness** with no roadmap ambiguity.

### Phase 5.1.2 — SwiftData Legacy Migration Hardening (macOS)
**Status:** CLOSED (2026-03-13 America/New_York)  
**Goal:** Eliminate a real macOS startup crash caused by legacy local-store migration after recent cache/schema additions.

**Closure summary**
- `CachedSyncState.hasCompletedRealHealthKitIngest` no longer blocks legacy SwiftData/CoreData migration on macOS.
- The field is now persisted in a migration-safe way for cache/local-store semantics and normalized back to `false` when a legacy row loads without a stored value yet.
- Review of the other local persistence models confirmed no remaining new mandatory cache fields with the same migration profile:
  - `CachedTrainingLoadPoint` had already been hardened in Phase 5.1
  - `CachedWorkout` and `CachedDailySummary` did not introduce equivalent new required fields
- Validation passed for:
  - clean macOS store creation
  - legacy store migration on macOS
  - iOS simulator build regression check

**Why this block exists**
- Phase 5.1 cannot be considered operationally closed if a legacy local store still crashes the macOS app on launch.

**Scope**
- `CachedSyncState`
- local SwiftData/CoreData migration safety
- cross-platform build sanity check only

**Definition of Done**
- The app no longer crashes on macOS when a legacy local store is present.
- Legacy rows missing `hasCompletedRealHealthKitIngest` are interpreted safely.
- The next product phase remains **Phase 5.2 — Hero Readiness** with no roadmap ambiguity.

### Phase 5.1.3 — Data Freshness + Today Label Correctness
**Status:** CLOSED (2026-03-13 America/New_York)  
**Goal:** Restore user trust in the training-load surface by fixing stale-date semantics and making cache fallback observable.

**Closure summary**
- macOS and iPhone were confirmed to use the same effective `baseURL`; divergence came from platform-specific local caches, not different backends.
- The app no longer labels `Today` on the last chart point unless that point is actually the current calendar day.
- `Load Trend` summary totals (`Today`, `7d`, `28d`) are now calculated against calendar windows ending today, not just the last items in the array.
- The iOS client now accepts the legacy `training-load` payload still returned by production and reconstructs missing `Capacity`, `history_status`, `latest_*`, and `semantic_state` values client-side instead of failing decode and falling back to stale cache unnecessarily.
- Training-load fetches now log and expose a contained freshness snapshot with:
  - effective `baseURL`
  - remote fetch attempt
  - remote failure if any
  - cache fallback usage
  - latest point date
  - latest cache update timestamp
- When data is stale, the UI now says so explicitly instead of silently presenting an old last point as if it were current.
- Diagnosis was confirmed:
  - macOS and iPhone were not using different backends
  - they can diverge because each platform owns its own local cache and the training-load request can fall back to cache when remote refresh fails or when the app sees an older payload shape it can no longer decode
  - the old `Today` labeling logic made that cache divergence look worse and less trustworthy than it really was
- Final local macOS validation also normalized the target bundle identifier so the app could launch reliably during cross-platform verification.

**Why this block exists**
- A stale but mislabeled trend card breaks trust faster than a clearly-stale but honest one.

**Scope**
- Training load refresh/cache diagnostics
- Trend card temporal labeling
- Training load summary temporal aggregation

**Definition of Done**
- `Today` only appears for the actual current calendar day.
- Stale cache fallback is visible and diagnosable.
- The next product phase remains **Phase 5.2 — Hero Readiness** with no roadmap ambiguity.

### Phase 5.2 — Hero Readiness
**Status:** IMPLEMENTED / FUNCTIONALLY OPEN

**Closure summary**
- `Readiness v1` now ships from `GET /v1/home/summary` as a stable read-time contract on top of `daily_recovery`, `daily_sleep_summary`, and bounded load context.
- The hero contract now exposes:
  - `score`
  - `label`
  - `confidence`
  - `completeness_status`
  - `inputs_present`
  - `inputs_missing`
  - `model_version`
  - `has_estimated_context`
  - `trace_summary`
- The model uses the approved primary inputs and weights:
  - Sleep `40%`
  - HRV `35%`
  - RHR `25%`
- Baselines were implemented with gap tolerance:
  - HRV `28d`
  - RHR `28d`
  - Sleep `7–14d`
  - an isolated missing day degrades confidence/completeness instead of collapsing the model
- `recent exertion/load` remains a bounded secondary penalty-only modifier and does not redefine Readiness as Load.
- iOS now renders the Readiness Hero at the top of the temporary `TrainingLoadScreen`, with Figma-aligned hierarchy and label-driven theming:
  - `Ready` -> premium green
  - `Moderate` -> premium amber
  - `Recover` -> premium coral/red
- Guardrails remained intact:
  - `Trend Card` stays `Load vs Capacity`
  - `Recommended Today` stays separate
  - no Coach behaviors were introduced
- Validation completed:
  - backend unit/API tests passed locally
  - iOS device build passed
  - iOS simulator build passed
  - simulator launch passed
  - screenshot artifact captured for the hero host
- Production functional validation remains open because the current production user has no physiological rows in:
  - `recovery_signals`
  - `sleep_sessions`
  - `daily_sleep_summary`
  - `daily_recovery`
  - `daily_activity`
- Current production `Readiness unavailable` is therefore correct.
- The next subphase opens to enable real physiological ingest instead of weakening the model or inventing synthetic readiness.

**Goal:** Deliver the final Home hero that answers "How am I today?" through `Readiness`.

**Why this block exists**
- The PRD defines Home around the athlete's current state, and committee alignment closed `Readiness` as the governing term.

**Scope**
- Implement the final `Readiness` hero using documented recovery/readiness semantics.
- Keep `Battery` out of active product naming except as legacy documentary alias.
- Preserve transparency, drivers, and missing-data behavior.

**Main dependencies**
- Phase 5.0 closure
- `daily_recovery`
- `daily_sleep_summary`
- Load/exertion context from documented metrics
- Phase 2 card/layout rules

**Deliverables**
- Final Home hero contract for `Readiness`
- Hero UI and state model
- Explicit transparency entry into drivers and completeness

**Definition of Done**
- Hero naming, semantics, and missing-data behavior are fully aligned.
- Production receives enough real physiological data to validate the hero against non-empty `Readiness` states.

**QA focus**
- Missing HRV / RHR / sleep
- Partial readiness inputs
- State label clarity

### Phase 5.2.1 — Readiness data enablement
**Status:** IN PROGRESS

**Goal:** Enable real Apple Health physiological ingest so production can populate `Readiness` inputs with real sleep, HRV, and RHR data.

**Why this block exists**
- The production hero is not blocked by scoring. It is blocked by missing physiological ingest.
- `Readiness unavailable` is currently the correct output for the real production dataset.
- Enabling real ingest does not guarantee `complete` readiness on day 1. Early real outputs may be `partial` or `insufficient` while baselines consolidate.

**Scope**
- Keep Apple Health / HealthKit as the real source of truth for:
  - sleep
  - HRV
  - RHR
- Reuse backend ingest/recompute already present:
  - `POST /v1/ingest/sleep`
  - `POST /v1/ingest/recovery-signals`
  - `sleep_sessions -> daily_sleep_summary`
  - `recovery_signals + daily_sleep_summary -> daily_recovery`
- Enable iPhone-side HealthKit reads and transport for:
  - `sleepAnalysis`
  - `heartRateVariabilitySDNN`
  - `restingHeartRate`
- Add physiology-specific bootstrap/incremental sync state instead of reusing the workouts bootstrap flag.
- Add minimum observability for physiology sync:
  - bootstrap vs incremental mode
  - counts sent
  - latest sleep/recovery dates sent
  - confirmation of physiology bootstrap completion

**Non-goals**
- No readiness scoring/model changes
- No fake seed data
- No Coach or Load domain changes
- No provider abstraction or `open-wearables` adoption

**Definition of Done**
- The iPhone app requests HealthKit permission for sleep, HRV, and resting HR.
- The client can send real sleep and recovery payloads with timezone IANA to production-capable ingest endpoints.
- Physiology bootstrap can run independently of workout bootstrap.
- Recent physiological raw rows begin appearing in the active backend environment.
- Derived rows (`daily_sleep_summary`, `daily_recovery`) begin appearing from those raw inputs.
- First real readiness output is observable, even if initially `partial` or `insufficient`.

### Phase 5.3 — Core Metrics
**Status:** CLOSED

**Closure summary**
- `GET /v1/home/summary` now includes a dedicated `core_metrics` block for Home.
- The block exposes only already-approved load-domain metrics:
  - `seven_day_load`
  - `fitness`
  - `fatigue`
  - `history_status`
- Backend reuses the existing `training-load` model instead of duplicating formulas:
  - `seven_day_load` = trailing 7-day load sum
  - `fitness` = Home naming for internal `Capacity / CTL`
  - `fatigue` = existing `ATL`
  - `history_status` = the same trust/sufficiency state already used by `training-load`
- iOS now renders Core Metrics as a separate compact block between the Readiness Hero and the Trend Card in the temporary Home host.
- The final visual pass aligned the block to shared Design System primitives instead of a bespoke surface:
  - `DSSectionHeader`
  - `DSMetricSnapshotCard`
  - `DSCard` as the base supporting surface primitive
  - `DSMetricPill` only for secondary trust/history states
- The supporting snapshot pattern now lives in the Design System Gallery so Home no longer improvises a one-off multi-metric card.
- Core Metrics now uses a stable Home load snapshot so `Fitness` and `Fatigue` stay aligned with the same load-domain state exposed by `training-load`.
- Guardrails remained intact:
  - no readiness semantics inside Core Metrics
  - no Trend Card semantic changes
  - Hero, Core Metrics, and Trend Card remain visually distinct supporting layers inside Home
  - no Coach / Recommended Today coupling
- Final validation passed:
  - backend/API QA
  - iOS build
  - macOS build
  - macOS visual QA of `Readiness Hero + Core Metrics + Load Trend`

**Goal:** Add the compact Home metrics block that contextualizes current training state.

**Why this block exists**
- Home needs immediate recent-load context without sending the user to Trends.

**Scope**
- Implement the PRD Core Metrics block using only catalog-defined load-domain metrics.
- Current target metrics:
  - `7-Day Load`
  - `Fitness`
  - `Fatigue`

**Main dependencies**
- Phase 5.0 closure
- Training Load series
- `docs/METRICS_CATALOG.md`
- Phase 2 metric/card components

**Deliverables**
- Core Metrics contract
- Core Metrics implementation

**Definition of Done**
- Every metric in the block already exists in the Metrics Catalog and is consistently named in UI/docs.

**QA focus**
- Sparse history
- Mixed real vs estimated TRIMP days
- Multi-sport recent load

### Phase 5.4 — Drivers / Explainability
**Status:** CLOSED

**Closure summary**
- `Readiness` now exposes a nested explainability contract in `GET /v1/home/summary` under `readiness.explainability`.
- The public explainability block exposes:
  - `completeness_status`
  - `confidence`
  - `model_version`
  - `items[]`
- Every visible item now carries:
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
- Visible v1 scope is now locked to the approved set:
  - primary drivers:
    - `sleep`
    - `hrv`
    - `rhr`
  - secondary context:
    - `recent_exertion`
- Public visible `role` values are only:
  - `primary_driver`
  - `secondary_context`
- Public visible `status` values are:
  - `measured`
  - `estimated`
  - `proxy`
  - `missing`
- Guardrails remained intact:
  - `recent_exertion` stays context only and is presented in UI as `Exertion`
  - `Movement` and secondary strength context stay out of the v1 Home surface
  - score math and label semantics were not changed
  - `trace_summary` remains for compatibility but is derived from the same evaluation path
- iOS Home now renders a separate `Drivers` block between the hero and Core Metrics, using governed Design System primitives instead of a bespoke card:
  - `DSExplainabilityCard`
  - `DSSectionHeader`
  - `DSMetricPill` only for lightweight non-measured states
- Visual separation is now explicit:
  - Hero remains dominant
  - Drivers explain readiness
  - Core Metrics remains load snapshot
  - Trend Card remains load trajectory
- Validation completed locally:
  - backend unit/API tests passed
  - iOS simulator build passed
  - macOS build passed
  - visual QA passed on iPhone simulator and macOS host using a local mock of the approved contract

**Goal:** Make `Readiness` transparent through an explicit driver layer.

**Why this block exists**
- `Readiness` is only acceptable if the user can see why it moved.

**Scope**
- Implement the driver breakdown for the approved v1 items only:
  - primary drivers:
    - Sleep
    - HRV
    - RHR
  - secondary context:
    - Load / Exertion
- Use proxy/estimated labels only through approved `status`, not by inventing visible driver roles.
- Keep `Movement` and secondary strength context out of the visible v1 Home surface.

**Main dependencies**
- Phase 5.2 hero contract
- `docs/METRICS_CATALOG.md`
- `daily_recovery`, `daily_activity`, `daily_sleep_summary`
- `docs/GLOSARIO.md`

**Deliverables**
- Drivers/explainability contract
- Driver surfaces aligned with Design System rules

**Definition of Done**
- Every displayed driver/context item maps to a documented input or metric and preserves the approved primary-vs-context separation.

**QA focus**
- Missing drivers
- Measured vs estimated context treatment
- Separation from Core Metrics and Trend Card

### Phase 5.5 — Recommended Today
**Goal:** Add the contextual recommendation block without expanding into Coach.

**Why this block exists**
- Home must answer "What should I do today?" but without absorbing planner/chat/adaptive coaching scope.

**Scope**
- Implement `Recommended Today` as guidance-only contextual output.
- Inputs expected:
  - `Readiness`
  - recent load
  - confidence/completeness

**Main dependencies**
- Phase 5.2 hero readiness
- Phase 5.3 Core Metrics
- Phase 5.6 completeness/confidence layer
- PRD Home semantics

**Deliverables**
- Recommendation contract
- Recommendation implementation with bounded scope

**Definition of Done**
- The block is explicitly guidance-only and does not introduce Coach behaviors.

**QA focus**
- No-data day
- Conflicting signals
- Guardrail against Coach scope creep

### Phase 5.6 — Data Completeness / Confidence
**Goal:** Add the Home-wide trust layer for partial, missing, or mixed data.

**Why this block exists**
- Home cannot be trustworthy without explicit completeness/confidence semantics.

**Scope**
- Surface completeness states across Home blocks.
- Surface provenance/confidence cues already allowed by Phase 4.5.
- Keep `missing` distinct from empty synthetic values.

**Main dependencies**
- Phase 5.0 closure
- Phase 4.5 completeness/provenance rules
- `docs/METRICS_CATALOG.md`
- Phases 5.1-5.5 contracts

**Deliverables**
- Shared Home completeness/confidence contract
- Warning and fallback patterns

**Definition of Done**
- Every Home block declares how it behaves under `complete`, `partial`, and `missing`.

**QA focus**
- `complete` vs `partial` vs `missing`
- Mixed-source days
- `primary_device_name = null`

### Phase 5.7 — Deep QA / Home integration
**Goal:** Validate Home as one coherent surface once all blocks are present.

**Why this block exists**
- Block-level delivery is not enough; Home must work as a single product surface.

**Scope**
- Integrate Trend Card, Hero, Core Metrics, Drivers, Recommended Today, and Completeness layers.
- Validate navigation, state transitions, cross-platform presentation, and regression against the existing load experience.

**Main dependencies**
- Phases 5.1-5.6
- Phase 2 Design System
- Phase 3 / 4 / 4.5 data foundations

**Deliverables**
- Integrated Home v1
- Deep QA matrix and evidence

**Definition of Done**
- Home answers the PRD questions coherently and without semantic contradiction.

**QA focus**
- Missing-data days
- Very high load day
- Steps-only day
- Multi-session day
- iPhone + Mac consistency

---

## Phase 6 — Trends v1 (Core charts)

**Status:** PLANNED  
**Goal:** Provide long-range analytics akin to Athlytic, prioritized for running.

### Deliverables
- Recovery vs Exertion chart.
- Recovery vs Base Training with optimal ranges.
- Training Load (Fitness/Fatigue/Form) with 30/60/6m/1y.
- HR Zones charts (7/30/60).
- Aerobic Mix (Low/High/Anaerobic) if derivable.
- Cardio Fitness / HR Recovery when data sufficient.

### DoD
- All charts have consistent design language from Phase 2.
- Chart interactions (range toggles, sport toggles where relevant).

### QA
- Sparse data (new user).
- Data gaps.
- Multiple sports.

---

## Phase 7 — Workouts v1 (Summary + Detail)

**Status:** PLANNED  
**Goal:** A workouts hub with running-first highlights and solid filtering.

### Deliverables
- Summary cards: Top Efforts, #Workouts, Active Time, Distance, Energy, Strength Minutes.
- Workout list with filters.
- Workout detail v1:
  - core stats, TRIMP, HR avg/max, notes.
  - micro check-in (RPE/energy/pain) embedded (no Journal tab).

### DoD
- Fast browsing, stable filters.
- Detail loads from local store.

### QA
- Indoor/outdoor mix.
- Strength-only workouts.

---

## Phase 8 — Body v1 (Weight & Measurements)

**Status:** PLANNED  
**Goal:** Replace “Journal” with a structured Body metrics area.

### Deliverables
- Weight chart 30/90/365 + manual entry.
- Body measurements (optional fields) + trend charts.
- Goals (target weight range).
- Data sources:
  - Apple Health weight (if present)
  - Manual input fallback
  - Speediance import (Phase 9)

### DoD
- Users can view trend and add new datapoints.
- Clear units and privacy.

### QA
- No weight data.
- Mixed units.

---

## Phase 9 — Speediance Integration (Import pipeline)

**Status:** PLANNED  
**Goal:** Integrate weight/body composition/measurements from Speediance if feasible.

### Deliverables
- Confirm Speediance export/API options.
- Import flow (CSV/file-based first) + mapping to Body data model.
- Deduplication + conflict resolution.

### DoD
- Import produces correct Body timeline without duplicates.

### QA
- Corrupted file.
- Missing columns.

---

## Phase 10 — Athlytic-like Advanced Layer (v2 scores & insights)

**Status:** PLANNED  
**Goal:** Move from “charts” to “insights” while staying transparent.

### Deliverables
- Weekly Cardio Load (minutes in top zones).
- Training Adaptation readiness (requires sufficient HRV/RHR days).
- Insight engine v1 (rule-based):
  - what changed, risk flags, intensity distribution warnings.

### DoD
- Insights are explainable and never contradict the underlying charts.

---

## Phase 11 — Coach (Runna-like) — Final

**Status:** FUTURE  
**Goal:** Adaptive training plan + daily recommendation + chat coach.

### Deliverables
- Plan builder (goal race, weeks, availability, strength day).
- Daily recommendation (optimal/conservative/free).
- AI chat with guardrails + memory.

### DoD
- Coach recommendations grounded in metrics + check-ins.

---

## Immediate next actions
1) Open **Phase 5.2 — Hero Readiness**.
2) Keep `Readiness` naming and semantics aligned with PRD, Glossary, and daily recovery contracts.
3) Reuse the new `Load vs Capacity` block as an already-closed Home dependency without pulling readiness semantics back into the load domain.
