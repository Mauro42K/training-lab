

# Training Lab — Roadmap (Source of Truth)

**Project name:** Training Lab  
**Repo (GitHub):** `training-lab`  
**Primary platforms:** iPhone + Mac (SwiftUI, single codebase)  
**Source of truth for training/health data:** Apple Fitness / Apple Health (HealthKit)  
**Product goal:** Running-first dashboard → Athlytic-like analytics → AI Coach (Runna-like)  

---

## 0. Governance

### 0.1 Non-negotiables
- **Design-first is mandatory:** no feature screens are coded until the Design System (tokens + components + layout rules) is defined and approved.
- **Battery is transparent:** any score shown to the user must include a clear **breakdown (“drivers”)** and a **data completeness** indicator.
- **Running-first, multi-sport-aware:** running is the primary narrative, but bike/strength/walk must be represented without distorting endurance load.
- **Zero confusion:** avoid duplicated data, hidden assumptions, and opaque scores.

### 0.2 Tabs (IA / v0.2)
- **Home** (moment of truth: before/after training)
- **Trends** (long-range charts & comparisons)
- **Workouts** (history + workout detail)
- **Body** (weight & body measurements; replaces Journal)
- **More** (settings, permissions, calibration)
- **Coach** (future)

### 0.3 MVP anchor
- **Home hero card = TRIMP chart** (usable from day 1).

---

## 1. Phase 0 — Automation & Infrastructure Bootstrap (Codex-driven)

**Status:** CLOSED on 2026-03-04 (America/New_York)  
**Goal:** One command/one run that sets the foundation: GitHub repo + VPS backend skeleton deployed to Coolify.

### 1.0.1 Phase 0.1 patch note
- Custom domain + TLS enabled: https://api.training-lab.mauro42k.com
- `/health` now returns baked metadata (`deploy_metadata.json`) with `git_sha` / `short_sha`
- GitHub Actions CI added
- Commit reference: `33d43855c4a2459269ad9ba7dc1273b4c9ed0e01`

### 1.1 Deliverables
1) **GitHub repository created**: `training-lab`
- Default branches, README stub, MIT/Private decision documented.
- Branch protection (at least: PR required on `main`, checks required).

2) **VPS backend scaffold deployed via Coolify**
- VPS access: `ssh root@178.156.251.31`.
- Coolify project/service created for **API** (backend).
- Domain + TLS plan documented (even if not activated yet).

3) **Environment & secrets baseline**
- `.env.example` (no secrets) + Coolify env vars.
- Health endpoint reachable in staging/prod form (even if placeholder).

4) **Docs**
- `docs/STACK_INFRA.md`: VPS/Coolify basics, service names, ports.
- `docs/DEPLOY_RUNBOOK.md`: deploy steps, rollback, smoke checks.

### 1.2 Definition of Done (DoD)
- Repo exists in GitHub, clone works, CI placeholder runs.
- VPS has a Coolify service for the backend; it builds and runs.
- `/health` returns a 200 with basic metadata (version can be placeholder initially).

### 1.3 QA (Shell → Service → HTTP)
- Shell: verify SSH access, service containers running.
- HTTP: `curl -i https://<api-domain>/health` returns 200.

### 1.4 Codex tasks (explicit)
- **Task A:** Create GitHub repo + initialize docs structure.
- **Task B:** Bootstrap backend service in Coolify via SSH (create project, service, env, deploy).

---

## 2. Phase 1 — Product Definition Pack (PRD-lite) + Metrics Inventory

**Status:** CLOSED (2026-03-04 America/New_York)  
**Goal:** Freeze what we are building before writing feature code.

**Evidence:**
- `docs/PRD.md`
- `docs/DATA_SOURCES.md`
- `docs/METRICS_CATALOG.md` (con fórmulas v1 + `metrics_model_version`)
- `docs/GLOSARIO.md`
- `docs/CHANGELOG.md`

### 2.1 Deliverables
- `docs/PRD.md` (lightweight):
  - personas (you), use-cases (pre/post training), success criteria.
  - tabs definition + what data lives where.
  - MVP scope boundaries.
- `docs/METRICS_CATALOG.md`:
  - metric list, sources (HealthKit), calculation notes, fallbacks.
- `docs/DATA_SOURCES.md`:
  - Apple Health data types required (workouts, HR samples, HRV, RHR, sleep, steps, weight).
  - data availability rules + “missing data” behavior.

### 2.2 DoD
- Clear agreement on: Home modules, Trends modules, Workouts summary cards, Body scope.
- Metric definitions include **inputs**, **outputs**, and **edge cases**.

### 2.3 QA
- Peer review checklist (committee): no hidden assumptions, no ambiguous definitions.

---

## 3. Phase 2 — Design System & Layout (MANDATORY, before feature screens)

**Status:** CLOSED (2026-03-05 America/New_York)  
**Goal:** Establish a premium, Apple-like visual language and reusable UI primitives.

**Closure notes:**
- Tokens finalized with parity in Swift: colors, typography, spacing, radius, shadows/elevation.
- Chart styling rules v0.1 implemented and documented.
- Multiplatform component gallery running on iOS + macOS via `DesignSystemDemo`.
- Visual QA completed with evidence in `docs/Phase2_VisualQA.md` and `docs/qa/phase2/`.
- Implementation base commit: `3431927`.
- Documentary closure: `chore(phase2): close docs (roadmap, changelog, qa evidence) + include PRD`.

### 3.1 Deliverables (Design)
- **Design tokens** (source of truth):
  - colors (backgrounds/surfaces/semantic states), typography scale, spacing, radius, shadow/elevation.
  - chart styling rules (grid, axes, labels, interaction).
- **Layout rules**:
  - card density, section spacing, navigation patterns (iPhone tabs vs Mac split view).
- **Component library spec**:
  - Ring, MetricPill, Card, ChartCard, SectionHeader, SegmentedControl, EmptyState, LoadingState.

### 3.2 Deliverables (Implementation scaffolding)
- `DesignSystem/` Swift modules (or folder) with:
  - `AppColors`, `AppTypography`, `AppSpacing`, `AppRadius`, `AppShadows`.
  - base components implemented and demoed in a gallery screen.

### 3.3 DoD
- Tokens approved (no placeholders).
- Component gallery renders on iPhone + Mac.
- No feature screens built yet (only gallery / sandbox).

### 3.4 QA
- Visual QA on iPhone + Mac (light/dark, dynamic type basic).

---

## 4. Phase 3 — HealthKit Access & Local Data Model (Foundation)

**Status:** CLOSED (2026-03-05 America/New_York)  
**Goal:** Read Apple Health data reliably and normalize it into a local store for fast charts.

**Evidence:**
- `docs/Phase3_QA.md`
- `docs/qa/phase3/`

**Closure notes:**
- Backend online-first foundation completed: PostgreSQL + Alembic + API v1.
- Auth baseline enforced on `/v1/*` with `X-API-KEY`; `/` and `/health` remain public.
- Idempotency flow validated end-to-end (replay 200 / conflict 409).
- iOS shell + permission gate + online-first contracts integrated.
- Xcode wiring gap for TrainingLab sources closed via `project.pbxproj` update (documented in QA evidence).
- Rate limiting remains deferred to **Phase 3.1**.

### 4.1 Deliverables
- HealthKit permission flow + data access layer.
- Local persistence (recommended: **SQLite/CoreData**) with:
  - normalized workouts (type, start/end, duration, distance, kcal)
  - HR samples linkage (as available)
  - sleep summaries, steps, HRV, RHR, weight/body metrics
- Deduplication strategy (source/device conflicts).
- Basic background refresh plan (as feasible).
- Backend v1 ingest/query endpoints with idempotency and payload limits.
- Rate limiting moved to **Phase 3.1** (Phase 3 keeps auth + payload guards).

### 4.2 DoD
- App can request permissions and ingest at least 30 days of workouts.
- Local store supports querying by day and by sport.
- Missing data handled gracefully.

### 4.3 QA
- Permissions denied path.
- Empty dataset path.
- Duplicate workouts scenario.

---

## 5. Phase 4.0 — TRIMP Engine v1 + Home TRIMP Hero Card (MVP)

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

### 5.1 Deliverables (Delivered)
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

### 5.2 DoD (Closed)
- TRIMP chart loads fast from backend/cache path.
- Filter changes update chart correctly.
- Day Sheet shows correct sessions and totals.

### 5.3 QA (Closed)
- Multi-session day (run + strength): PASS.
- No-HR workouts (fallback rules): PASS.
- Today alignment UI vs backend: PASS.
- Evidence:
  - `docs/Phase4_QA.md`
  - `docs/qa/phase4/README.md`

### 5.4 Phase 4.1 — Training Load UX Polish
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

### 5.5 Phase 4.2 — HealthKit Real Ingest Enablement
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

### 5.6 Phase 4.3 — Staging Environment & Environment Separation
**Status:** IN PROGRESS  
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

Current execution status:
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
- canonical domain `api-staging.training-lab.mauro42k.com` is configured as the target in Coolify, but public DNS resolution is still pending an external A record

### 5.6.1 Deliverables
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

### 5.6.2 DoD
- Staging database created and populated from production baseline.
- App can connect to staging environment without affecting production data.
- Production ingest and metrics remain unchanged.
- Staging is verifiable without ambiguity by:
  - distinct service/container in Coolify
  - distinct PostgreSQL resource
  - `/health` returning `environment=staging`

Pending before closure:
- public DNS for `api-staging.training-lab.mauro42k.com`

### 5.6.3 QA
- Confirm staging API responds correctly to `/health`.
- Verify staging DB queries return expected cloned data.
- Validate that a staging ingest or recompute does **not** modify production DB.
- Compare prod vs staging counts for:
  - `workouts`
  - `workout_load`
  - `daily_load`

### 5.6.4 Guardrails
- Production database must never be modified directly during feature development.
- All schema experiments, migrations, and ingest tests must run in staging first.
- Production deploys must come from validated staging builds.
- iOS debug builds must show the active environment explicitly when not running default production.

### 5.7 Phase 4.4 — Workout Reconciliation & Historical Cleanup
**Status:** PLANNED  
**Goal:** Provide mechanisms to reconcile historical workouts between Apple Health and the backend database.

Context:
- users may discover duplicated workouts in Apple Fitness history.
- when a workout is deleted in HealthKit, the backend should eventually reflect that change.

Initial scope:
- detect workouts that no longer exist in HealthKit.
- allow backend reconciliation.
- mark workouts as deleted or remove them.
- trigger recalculation of derived metrics.

Potential capabilities:
- handle workouts removed from Apple Fitness.
- support duplicate cleanup.
- allow safe historical reconciliation.
- recalculate TRIMP / daily load after deletions.

Guardrails:
- must be tested in STAGING first.
- must not risk production data corruption.
- must maintain idempotency of ingest pipeline.

---

## 6. Phase 5 — Home v1 (Rings + Drivers Cards)

**Status:** PLANNED  
**Goal:** Build the “Today” page like Athlytic but improved: TRIMP first, then state rings & drivers.

### 6.1 Deliverables
- Rings row:
  - Recovery (Battery), Sleep, Exertion, Movement.
- Driver cards:
  - Health (HRV + RHR), Stress (if available), Battery breakdown, Steps/Goal, Strength & Cross.
- Transparent Battery v1:
  - score + breakdown + data completeness.

### 6.2 DoD
- Each ring/card navigates to a detail view (even if minimal at first).
- Battery shows “why” (drivers) and shows missing-data warnings.

### 6.3 QA
- Missing HRV or missing sleep.
- Very high load day.
- Steps-only day.

---

## 7. Phase 6 — Trends v1 (Core charts)

**Status:** PLANNED  
**Goal:** Provide long-range analytics akin to Athlytic, prioritized for running.

### 7.1 Deliverables
- Recovery vs Exertion chart.
- Recovery vs Base Training with optimal ranges.
- Training Load (Fitness/Fatigue/Form) with 30/60/6m/1y.
- HR Zones charts (7/30/60).
- Aerobic Mix (Low/High/Anaerobic) if derivable.
- Cardio Fitness / HR Recovery when data sufficient.

### 7.2 DoD
- All charts have consistent design language from Phase 2.
- Chart interactions (range toggles, sport toggles where relevant).

### 7.3 QA
- Sparse data (new user).
- Data gaps.
- Multiple sports.

---

## 8. Phase 7 — Workouts v1 (Summary + Detail)

**Status:** PLANNED  
**Goal:** A workouts hub with running-first highlights and solid filtering.

### 8.1 Deliverables
- Summary cards: Top Efforts, #Workouts, Active Time, Distance, Energy, Strength Minutes.
- Workout list with filters.
- Workout detail v1:
  - core stats, TRIMP, HR avg/max, notes.
  - micro check-in (RPE/energy/pain) embedded (no Journal tab).

### 8.2 DoD
- Fast browsing, stable filters.
- Detail loads from local store.

### 8.3 QA
- Indoor/outdoor mix.
- Strength-only workouts.

---

## 9. Phase 8 — Body v1 (Weight & Measurements)

**Status:** PLANNED  
**Goal:** Replace “Journal” with a structured Body metrics area.

### 9.1 Deliverables
- Weight chart 30/90/365 + manual entry.
- Body measurements (optional fields) + trend charts.
- Goals (target weight range).
- Data sources:
  - Apple Health weight (if present)
  - Manual input fallback
  - Speediance import (Phase 9)

### 9.2 DoD
- Users can view trend and add new datapoints.
- Clear units and privacy.

### 9.3 QA
- No weight data.
- Mixed units.

---

## 10. Phase 9 — Speediance Integration (Import pipeline)

**Status:** PLANNED  
**Goal:** Integrate weight/body composition/measurements from Speediance if feasible.

### 10.1 Deliverables
- Confirm Speediance export/API options.
- Import flow (CSV/file-based first) + mapping to Body data model.
- Deduplication + conflict resolution.

### 10.2 DoD
- Import produces correct Body timeline without duplicates.

### 10.3 QA
- Corrupted file.
- Missing columns.

---

## 11. Phase 10 — Athlytic-like Advanced Layer (v2 scores & insights)

**Status:** PLANNED  
**Goal:** Move from “charts” to “insights” while staying transparent.

### 11.1 Deliverables
- Weekly Cardio Load (minutes in top zones).
- Training Adaptation readiness (requires sufficient HRV/RHR days).
- Insight engine v1 (rule-based):
  - what changed, risk flags, intensity distribution warnings.

### 11.2 DoD
- Insights are explainable and never contradict the underlying charts.

---

## 12. Phase 11 — Coach (Runna-like) — Final

**Status:** FUTURE  
**Goal:** Adaptive training plan + daily recommendation + chat coach.

### 12.1 Deliverables
- Plan builder (goal race, weeks, availability, strength day).
- Daily recommendation (optimal/conservative/free).
- AI chat with guardrails + memory.

### 12.2 DoD
- Coach recommendations grounded in metrics + check-ins.

---

## Appendix A — Immediate next actions
1) Run Phase 0 automation (Codex) to create repo + bootstrap Coolify backend.
2) Create the definition pack (PRD-lite + metrics catalog).
3) Lock Design System before feature UI.
