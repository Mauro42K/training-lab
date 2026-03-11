# README Dev

## Active documentation phase

- Phase 4.5 is formally opened through `docs/PHASE4_5_DAILY_DOMAINS_SUMMARY_CONTRACTS.md`.
- This opening is documentation-only.
- No new endpoints, migrations, or implementation contracts are active yet.
- Phase 4.4 remains on hold and must not be mixed with Phase 4.5 execution.

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

Flujo actual validado en Phase 4.2:

HealthKit -> iOS Client -> POST /v1/ingest/workouts -> PostgreSQL -> load endpoints

Nota Phase 4.5:
- La siguiente expansión Apple-first documentada cubre sueño, HRV, RHR, activity diaria y body measurements.
- Esa expansión todavía no cambia el pipeline implementado actual.
- `GET /v1/daily` permanece como contrato existente y no debe expandirse para absorber los dominios de Phase 4.5.
- La timezone IANA del device debe considerarse input operativo del sync de Phase 4.5.

## Modos de sync

### Bootstrap mode
- Se usa cuando `hasCompletedRealHealthKitIngest == false`.
- El cliente ignora el cursor previo y ejecuta `fetchWorkouts(since: nil)`.
- Sirve para poblar el histórico completo en la primera ingest real.

### Incremental mode
- Se usa cuando `hasCompletedRealHealthKitIngest == true`.
- El cliente consulta solo workouts posteriores al cursor local.
- El cursor principal es `lastSuccessfulIngestAt`.

## Cursor tracking
- `lastIngestAttemptAt`: último intento iniciado.
- `lastSuccessfulIngestAt`: último sync remoto exitoso usado para incremental.
- `hasCompletedRealHealthKitIngest`: define si el siguiente sync corre en bootstrap o incremental.
- `syncStatusRaw`: refleja transición operativa (`idle`, `syncing`, `ready`, error según corresponda).

Nota Phase 4.5:
- la apertura documental todavía no define cursores por dominio,
- pero sí congela que la timezone IANA debe viajar con el sync/ingest de dominios diarios Apple-first.

## Batch ingest strategy
- El cliente agrupa workouts en lotes para `POST /v1/ingest/workouts`.
- En la validación real de Phase 4.2, el histórico completo se procesó en 9 batches.
- El batching reduce riesgo de timeouts y mantiene requests manejables.

## Idempotency keys
- Cada batch usa `X-Idempotency-Key`.
- El pipeline backend conserva idempotencia por request y por `healthkit_workout_uuid`.
- Replays no deben duplicar workouts ni derivadas de carga.

## Endpoints relevantes
- `POST /v1/ingest/workouts`
- `GET /v1/workouts`
- `GET /v1/daily`
- `GET /v1/training-load`

## Notas operativas
- Backend activo de esta fase: PostgreSQL.
- El refresh post-ingest debe enviar fechas `YYYY-MM-DD` a `GET /v1/daily`.
- La validación oficial de ingest real se hace en iPhone físico, no en simulador.
- Features delicadas de reconciliación histórica o borrado deben probarse primero en staging, no en producción.
- Para Phase 4.5, la semántica nueva debe definirse primero en documentación y luego implementarse por dominios explícitos.
- `missing` en los derivados diarios de Phase 4.5 significa ausencia de row emitida, no row vacía.
