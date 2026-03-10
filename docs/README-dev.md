# README Dev

## Ingest pipeline real

Flujo actual validado en Phase 4.2:

HealthKit -> iOS Client -> POST /v1/ingest/workouts -> PostgreSQL -> load endpoints

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
