# README Dev

## Active documentation phase

- Phase 4.5 is formally closed through `docs/PHASE4_5_DAILY_DOMAINS_SUMMARY_CONTRACTS.md`.
- Delivered in 4.5:
  - Apple-first daily domains for sleep, activity, recovery, and body
  - explicit query contracts for daily domains
  - `GET /v1/home/summary` as composition-only summary contract
  - QA closure on staging + production after Alembic migration `20260311_01`
- Phase 4.4 remains on hold and must not be mixed into later active phases.
- Phase 5.1 is closed:
  - `Trend Card (Load vs Capacity)` shipped
  - legacy cache migration hardening shipped
  - training-load freshness and `Today` label correctness shipped
- Phase 5.2 is closed:
  - `Readiness Hero` shipped in Home
  - `Readiness v1` uses Sleep, HRV, and RHR as primary readiness inputs
- Phase 5.2.1 is resolved:
  - real Apple Health ingest for sleep, HRV SDNN, and resting HR is enabled from iPhone
  - production now has real rows in `sleep_sessions`, `recovery_signals`, `daily_sleep_summary`, and `daily_recovery`
- Phase 5.3 is closed:
  - Home `Core Metrics` shipped via `GET /v1/home/summary`
  - metrics shown are `7-Day Load`, `Fitness`, and `Fatigue`
- Phase 5.4 is closed:
  - `Readiness Explainability` shipped
  - visible v1 scope is `Sleep`, `HRV`, `RHR`, plus `Exertion` as secondary context
  - explainability is delivered as `readiness.explainability` inside `GET /v1/home/summary`
- Phase 5.5 is closed:
  - `Recommended Today` shipped and integrated in Home as guidance-only
  - Home order is `Readiness Hero -> Drivers -> Recommended Today -> Core Metrics -> Load Trend -> Trend Card`
  - backend-only recommendation structure + UI layer are both implemented
  - dynamic Spanish copy is generated client-side with controlled templates
  - phase 5.5 does not use OpenAI API key, does not run a real LLM runtime, and does not introduce backend generative copy
  - no planner, no coach, no chat, no workout prescription, no adaptive planning
- Phase 5.6 is closed:
  - Home trust/completeness is normalized through `complete`, `partial`, and `missing`
  - fallback behavior is handled in client/UI using existing semantics
  - no new transversal `home_summary` object or backend contract expansion was introduced
- Phase 5.6.1 is closed:
  - UX/UI polish only
  - dark premium cohesion and reduced nested-card feel
  - compact `Drivers` / `Recommended Today` / `Core Metrics` layouts shipped
  - no backend, contract, or trust-semantic changes
- Phase 5.7 is now the active next phase:
  - deep QA / Home integration
  - validate the already delivered Home blocks as a single surface
  - keep trust semantics unchanged
- Phase 4.4 remains on hold and must not be mixed into the next active phase.

## Environment targets

Training Lab now has three runtime targets at the app config layer:

- `production`
  - base URL target: `https://api.training-lab.mauro42k.com`
- `staging`
  - canonical target: `https://api-staging.training-lab.mauro42k.com`
  - optional fallback/debug path: `http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io`
- `local`
  - base URL target: `http://127.0.0.1:8000`

## iOS runtime config

1. Copiar `DesignSystemDemo/Config/Runtime.Local.example.xcconfig` a `DesignSystemDemo/Config/Runtime.Local.xcconfig`.
2. Elegir exactamente un bloque:
   - `TRAINING_LAB_RUNTIME_ENV = production`
   - `TRAINING_LAB_RUNTIME_ENV = staging`
   - `TRAINING_LAB_RUNTIME_ENV = local`
3. Definir:
   - `TRAINING_LAB_API_BASE_URL`
   - `TRAINING_LAB_API_KEY`

Notas:
- `Runtime.Local.xcconfig` no se versiona.
- En debug, la app muestra un badge visible con el entorno activo.
- La key embebida en bundle debe ser solo de dev/staging/local. Nunca una credencial sensible de producción.
- Para staging, preferir siempre el host canónico `api-staging.training-lab.mauro42k.com`.

## Ingest pipeline real

Flujo actual validado:

`HealthKit -> iPhone client -> ingest endpoints -> PostgreSQL -> daily domains / load domains -> Home`

Dominios reales ya activos desde iPhone:
- workouts -> `POST /v1/ingest/workouts`
- sleep -> `POST /v1/ingest/sleep`
- recovery signals (`hrv_sdnn`, `resting_hr`) -> `POST /v1/ingest/recovery-signals`

Derivadas backend:
- `sleep_sessions` -> `daily_sleep_summary`
- `recovery_signals` + `daily_sleep_summary` -> `daily_recovery`
- workouts -> `daily_load` / `training-load` / Home metrics

Notas:
- `GET /v1/daily` permanece como contrato legacy y no debe expandirse para absorber los dominios diarios nuevos.
- La timezone IANA del device forma parte del input operativo de los dominios diarios Apple-first.
- La validación oficial de ingest real sigue siendo en iPhone físico, no en simulador.

## Modos de sync

### Workout bootstrap mode
- Se usa cuando `hasCompletedRealHealthKitIngest == false`.
- El cliente ignora el cursor previo y ejecuta `fetchWorkouts(since: nil)`.
- Sirve para poblar el histórico completo en la primera ingest real de workouts.

### Workout incremental mode
- Se usa cuando `hasCompletedRealHealthKitIngest == true`.
- El cliente consulta solo workouts posteriores al cursor local.
- El cursor principal es `lastSuccessfulIngestAt`.

### Physiology bootstrap mode
- Se usa cuando `hasCompletedPhysiologyIngest == false`.
- El cliente hace bootstrap histórico de sueño + HRV + RHR aunque workouts ya estén completos.
- Sirve para poblar baselines reales de `Readiness`.

### Physiology incremental mode
- Se usa cuando `hasCompletedPhysiologyIngest == true`.
- El cliente consulta solo muestras fisiológicas posteriores al cursor propio.
- El cursor principal es `lastSuccessfulPhysiologyIngestAt`.

## Cursor tracking
- `lastIngestAttemptAt`: último intento iniciado de workouts.
- `lastSuccessfulIngestAt`: último sync remoto exitoso de workouts.
- `hasCompletedRealHealthKitIngest`: define si workouts corren en bootstrap o incremental.
- `lastPhysiologyIngestAttemptAt`: último intento iniciado de sueño / HRV / RHR.
- `lastSuccessfulPhysiologyIngestAt`: último sync remoto exitoso de fisiología.
- `hasCompletedPhysiologyIngest`: define si sueño / HRV / RHR corren en bootstrap o incremental.
- `syncStatusRaw`: refleja transición operativa (`idle`, `syncing`, `ready`, error según corresponda).

Notas:
- la timezone IANA viaja con los syncs Apple-first;
- workouts y fisiología ya no comparten el mismo bootstrap operativo.

## Batch ingest strategy
- El cliente agrupa workouts en lotes para `POST /v1/ingest/workouts`.
- El cliente también agrupa sueño y recovery signals en lotes dedicados.
- El batching reduce riesgo de timeouts y mantiene requests manejables.
- El backend conserva recompute downstream por fechas afectadas después de cada batch relevante.

## Idempotency keys
- Cada batch usa `X-Idempotency-Key`.
- El pipeline backend conserva idempotencia por request y por identificadores HealthKit.
- Replays no deben duplicar workouts, sleep sessions, recovery signals ni derivadas.

## Endpoints relevantes
- `POST /v1/ingest/workouts`
- `POST /v1/ingest/sleep`
- `POST /v1/ingest/recovery-signals`
- `GET /v1/workouts`
- `GET /v1/daily`
- `GET /v1/training-load`
- `GET /v1/home/summary`

## Home / readiness notes
- `Readiness v1` usa como drivers primarios: `Sleep`, `HRV`, `RHR`.
- `Exertion` aparece como contexto secundario en explainability; no es un driver primario del score.
- `Recommended Today` vive en `GET /v1/home/summary` como bloque guidance-only con:
  - `state`
  - `confidence`
  - `reason_tags`
  - `guidance_only`
- La copy de `Recommended Today` en 5.5 se resuelve en cliente con generación controlada/templated.
- En 5.5 no hay integración LLM real ni uso de OpenAI API key para copy.
- `Core Metrics` en Home muestra:
  - `7-Day Load`
  - `Fitness`
  - `Fatigue`
- `Readiness Explainability` vive dentro de `readiness.explainability`.

## Notas operativas
- Backend activo de esta fase: PostgreSQL.
- El refresh post-ingest debe enviar fechas `YYYY-MM-DD` a `GET /v1/daily`.
- Features delicadas de reconciliación histórica o borrado deben probarse primero en staging, no en producción.
- Para fases posteriores, la semántica nueva debe seguir reutilizando los dominios explícitos cerrados en Phase 4.5.
- `missing` en los derivados diarios Apple-first significa ausencia de row emitida, no row vacía.
