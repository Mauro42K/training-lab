

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
- Delivered the first load-domain value: TRIMP v1, recompute pipeline, `GET /v1/training-load`, and historical backfill.
- Integrated the temporary iOS Training Load screen with sport filters, 28-day daily bars, today highlight, and day detail.
- Fixed the `Today` alignment bug so UI and backend agree on the active calendar day.

### Phase 4.1 — Training Load UX Polish
**Status:** CLOSED (2026-03-06 America/New_York)
- Refined the temporary Training Load screen for better chart readability, interaction stability, and sparse-data handling.
- Hardened macOS/runtime configuration and isolated cache scope by effective `baseURL`.
- Closed as UX polish only; real HealthKit ingest alignment remained for Phase 4.2.

### Phase 4.2 — HealthKit Real Ingest Enablement
**Status:** COMPLETED
- Validated real HealthKit bootstrap ingest on iPhone and verified backend persistence in PostgreSQL.
- Confirmed incremental sync after bootstrap and fixed the post-ingest refresh `422` plus the iOS 18 `totalEnergyBurned` deprecation.
- Real workouts now drive real TRIMP values in the load domain.

### Phase 4.3 — Staging Environment & Environment Separation
**Status:** CLOSED (2026-03-10 America/Mexico_City)
- Separated production and staging into distinct services, databases, and runtime targets.
- Added explicit environment signaling in `/health` and iOS debug builds.
- Canonical staging DNS/TLS and staging `/v1/training-load` were validated before feature work continued.

### Phase 4.4 — Workout Reconciliation & Historical Cleanup
**Status:** ON HOLD / CONDITIONAL
- Kept the broader reconciliation umbrella available for future HealthKit parity work.
- Remains inactive unless validated deletion/reconciliation needs exceed targeted duplicate remediation.

#### Phase 4.4.1 — Workout History Dedup & Recompute
**Status:** CLOSED (2026-03-11 America/Mexico_City)
- Performed a staging-first duplicate audit, applied a canonical dedupe rule, and validated recompute safely in staging.
- Production was preflighted separately and required no cleanup for the approved eligible subset.

### Phase 4.5 — Daily Domains & Summary Contracts (Apple-first)
**Status:** CLOSED (2026-03-11 America/Mexico_City)
- Opened the Apple-first daily-domain foundation for `sleep_sessions`, `daily_sleep_summary`, `daily_recovery`, `daily_activity`, and `body_measurements`.
- Froze `daily_recovery` as consolidated inputs only, with explicit completeness/provenance rules and no final readiness score.
- Kept the anti-scope-creep guardrails explicit: no generic `GET /v1/daily`, no multi-provider platform, no raw-blob persistence, and no extra async infrastructure.

## Phase 5 — Home v1 (committee-aligned rollout)

**Status:** CLOSED
- Home v1 completed as the approved daily-athlete surface, with `Readiness` as the governing hero term and `Battery` retained only as a historical alias.
- `Recommended Today` stayed guidance-only, `Trend Card` stayed `Load vs Capacity`, and all load-domain semantics remained separate from readiness semantics.
- The rollout finished with the integrated Home stack validated on iPhone and Mac, including completeness, explainability, UX polish, and deep QA closure.

### Phase 5.0 — Home investigation / decisions / alignment
**Status:** CLOSED (2026-03-13 America/New_York)
- Closed the documentary alignment work and froze the Home execution order.
- Approved `Readiness` as the hero term, `Battery` as an alias, `Recommended Today` as guidance-only, and `Load vs Capacity` as the Trend Card.

### Phase 5.1 — Trend Card (Load vs Capacity)
**Status:** CLOSED (2026-03-13 America/New_York)
- Formalized `Capacity` in the load domain and completed the `Load vs Capacity` card.
- Extended `GET /v1/training-load` with stable load, capacity, and history/semantic states.
- Hardened legacy cache behavior so old rows do not collapse into false zeros or false missing states.

### Phase 5.1.1 — App Identity Baseline
**Status:** CLOSED (2026-03-13 America/New_York)
- Removed the remaining demo-shell identity by shipping the real app name and icon.
- Verified simulator and iPhone launch without asset-catalog or signing regressions.

### Phase 5.1.2 — SwiftData Legacy Migration Hardening (macOS)
**Status:** CLOSED
- Fixed the legacy local-store crash on macOS by making the new cache field migration-safe.
- Confirmed no equivalent migration hazard remained in the other local persistence models.

### Phase 5.1.3 — Data Freshness + Today Label Correctness
**Status:** CLOSED
- Fixed stale-cache temporal labeling so `Today` only appears for the actual current calendar day.
- Kept stale fallback visible and diagnosable instead of silently misleading the user.

### Phase 5.2 — Hero Readiness
**Status:** CLOSED
- Shipped `Readiness v1` as a read-time contract from `GET /v1/home/summary` on top of sleep, HRV, RHR, and bounded load context.
- Preserved the approved weights, baseline windows, theming, and transparency rules.
- Production validation later confirmed the hero against real physiological data.

### Phase 5.2.1 — Readiness data enablement
**Status:** RESOLVED
- Enabled the real HealthKit physiology ingest path for sleep, HRV, and resting HR.
- Production now has real physiological rows, and `Readiness` can render `partial` or `complete` when coverage exists.

### Phase 5.3 — Core Metrics
**Status:** CLOSED
- Added the compact `core_metrics` block with `seven_day_load`, `fitness`, `fatigue`, and `history_status`.
- Kept the block load-domain only and reused the existing training-load model instead of duplicating formulas.

### Phase 5.4 — Drivers / Explainability
**Status:** CLOSED
- Added the explicit readiness explainability contract and the governed `Drivers` block.
- Kept the visible scope limited to `Sleep`, `HRV`, `RHR`, and quieter `Exertion` context.

### Phase 5.5 — Recommended Today
**Status:** CLOSED (2026-03-18 America/New_York)
- Added the bounded `recommended_today` guidance block without expanding into Coach scope.
- Kept the output short, controlled, and separate from planner/chat behavior.

### Phase 5.6 — Data Completeness / Confidence
**Status:** CLOSED (2026-03-19 America/New_York)
- Established the Home-wide `complete / partial / missing` trust layer.
- Kept `missing` fallback-only and avoided introducing a new transversal summary object.

### Phase 5.6.1 — Home UX/UI Polish
**Status:** CLOSED (2026-03-19 America/New_York)
- Tightened the Home canvas into a more cohesive dark/premium stack.
- Introduced the reusable compact patterns that now govern the denser Home surfaces.

### Phase 5.7 — Deep QA / Home integration
**Status:** CLOSED (2026-03-25 America/New_York)
- Validated Home as a single coherent surface across the approved real scenarios.
- Confirmed no semantic contradictions across Hero, Drivers, Recommended Today, Core Metrics, and Trend Card.

---

## Phase 6 — Trends v1

**Status:** IN PROGRESS  
**Goal:** Answer “How is my training evolving?” with long-range analytics that stay load-domain focused, premium, and Apple-consistent.

- Phase 6.0 delivered the shell foundation.
- Phase 6.0.1 resolved the macOS cross-platform hardening issue.
- Phase 6.1 is now the next active phase.

### Phase-level guardrails
- Trends stays in the load domain. Do not mix readiness or recovery semantics into Trends.
- Body stays physiology-domain focused and separate from Trends.
- Use only metrics already defined in `docs/METRICS_CATALOG.md`; do not invent new metrics for Trends.
- If a reusable visual pattern is missing, extend the Design System first, then implement the chart surface.
- Do not introduce a generic `/timeseries` endpoint as a shortcut.
- Keep the implementation order explicit: **Definition -> Plan -> Implement -> QA -> Docs closure**.
- The hero chart is the dominant analytical surface; avoid spreadsheet-like framing.

### Phase 6.0 — Navigation Shell & App Sections
**Status:** CLOSED (2026-03-25 America/New_York)  
**Goal:** Replace the temporary validation host with the real product navigation shell before any Trends charts ship.

**Scope**
- iPhone uses a top-level tab bar.
- Mac uses a split view / sidebar shell.
- Initial visible sections must support:
  - Home
  - Trends
  - Workouts
  - Calendar
  - Body
  - More
- Non-implemented sections may remain controlled placeholders, but the shell must read as a real product foundation, not a demo workaround.
- Preserve the validated Home hierarchy while introducing the new navigation model.
- Gallery/demo-visible UI is no longer part of the visible product shell.

**Definition of Done**
- Product navigation no longer depends on the temporary validation host.
- The shell is the default entry point on iPhone and Mac.
- Placeholder sections are clearly controlled and do not read as unfinished scaffolding.

### Phase 6.0.1 — macOS Shell Hardening / Cross-platform Gate Resolution
**Status:** CLOSED (2026-03-26 America/New_York)  
**Goal:** Resolve the macOS gate/bootstrap policy correctly so shell entry works cleanly on both iPhone and Mac before any Trends hero work begins.

**Closure summary**
- macOS shell entry now bypasses unsupported HealthKit as an expected platform limitation instead of blocking the product shell.
- The shell remains the visible product entry on both iPhone and Mac.
- macOS app icon now uses the branded icon asset set, keeping cross-platform branding coherent.
- The fix stayed centralized in the gate and asset catalog instead of spreading platform hacks through the shell.

**Definition of Done**
- macOS enters the shell cleanly.
- iPhone and Mac both reach the same product shell behavior.
- Phase 6.1 can open only after this subphase is closed.

### Phase 6.1 — Trends Hero / Training Status
**Status:** OPEN  
**Goal:** Establish the dominant hero surface for Trends so the screen reads as a single premium analytical summary.

**Scope**
- Make the hero chart the first and strongest surface on Trends.
- Keep the surface load-domain only and oriented around training evolution rather than recovery/readiness.
- Reuse catalog-defined metrics and existing chart language.

**Definition of Done**
- Trends opens with a clear analytical hero that answers the training-evolution question at a glance.

### Phase 6.2 — Fitness Progress
**Status:** PLANNED  
**Goal:** Show the long-range progression of Fitness in a way that supports trend reading, not tabular inspection.

**Scope**
- Chart Fitness progression across approved time ranges.
- Keep range toggles clear and consistent with the existing chart system.

**Definition of Done**
- Fitness progress can be read quickly across multiple ranges without drifting into spreadsheet framing.

### Phase 6.3 — Training Load Trend
**Status:** PLANNED  
**Goal:** Expose the training-load trajectory with the right capacity context and time-range controls.

**Scope**
- Keep the load trajectory clearly separate from readiness semantics.
- Reuse the approved load-domain metrics and states from the catalog.

**Definition of Done**
- Users can see whether load is rising, stabilizing, or pushing against capacity without semantic ambiguity.

### Phase 6.4 — Intensity Distribution
**Status:** PLANNED  
**Goal:** Surface intensity distribution only when it can be derived from approved metrics.

**Scope**
- Use only already-defined metrics and calculations.
- Avoid inventing new zone systems or ad hoc labels.

**Definition of Done**
- Intensity distribution is legible, data-backed, and consistent with the load-domain vocabulary.

### Phase 6.5 — Performance Trends
**Status:** PLANNED  
**Goal:** Add performance-oriented trend surfaces when data is sufficient and the result remains honest.

**Scope**
- Cover approved performance trend views such as cardio fitness or HR recovery only when the data supports them.
- Keep sparse-state behavior explicit and premium.

**Definition of Done**
- Performance trends appear only when they can be explained without faking certainty.

### Phase 6.6 — Deep QA / Integration / Closure
**Status:** PLANNED  
**Goal:** Integrate Trends into the shell, validate cross-platform behavior, and close the documentation loop.

**Scope**
- Validate iPhone and Mac presentation.
- Check sparse history, multiple sports, and empty-state behavior.
- Confirm Trends remains load-domain focused and separate from Home semantics.

**Definition of Done**
- Trends is integrated, tested, and documented as a coherent product surface.

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
1) Start **Phase 6.1 — Trends Hero / Training Status**.
2) Preserve the validated Home hierarchy:
   - `Readiness Hero`
   - `Drivers / Explainability`
   - `Recommended Today`
   - `Core Metrics`
   - `Load Trend`
   - `Trend Card`
