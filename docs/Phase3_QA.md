# Phase 3 QA Closure (Online-First)

## Resumen Ejecutivo
Phase 3 queda cerrada con evidencia reproducible para el flujo online-first:

- API backend en producción con `/health` público y `/v1/*` protegido por `X-API-KEY`.
- Endpoints v1 validados: ingest, workouts, daily.
- Idempotencia validada: replay (200 con `idempotent_replay=true`) y conflicto (409).
- Builds de app multiplatform validados (iOS Simulator + macOS).
- Wiring manual de `project.pbxproj` documentado para incluir fuentes TrainingLab en target.

## Alcance Phase 3
Arquitectura validada:

`HealthKit -> SyncClient -> API v1 -> PostgreSQL -> API reads -> SwiftUI gate/UI`

## Evidencia
Backend/API:
- `docs/qa/phase3/backend_health.log`
- `docs/qa/phase3/backend_auth_401.log`
- `docs/qa/phase3/backend_workouts_200.log`
- `docs/qa/phase3/backend_daily_200.log`
- `docs/qa/phase3/backend_idempotency_replay_200.log`
- `docs/qa/phase3/backend_idempotency_conflict_409.log`

Builds:
- `docs/qa/phase3/ios-build.log`
- `docs/qa/phase3/macos-build.log`

UI / Manual evidence:
- `docs/qa/phase3/README.md`
- `docs/qa/phase3/screenshots/` (placeholders + naming contract)

Infra/wiring note:
- `docs/qa/phase3/pbxproj_wiring_note.md`

## DoD Checklist (Phase 3)
- [x] PostgreSQL + Alembic base operativos en backend.
- [x] Auth mínima viable: `X-API-KEY` obligatorio en `/v1/*`.
- [x] Endpoints v1 implementados y verificados (`ingest/workouts`, `workouts`, `daily`).
- [x] Idempotencia implementada y verificada (replay 200 / conflict 409).
- [x] Deduplicación por `UNIQUE(user_id, healthkit_workout_uuid)` validada vía contrato de ingest.
- [x] Payload guards activos (`INGEST_MAX_BATCH_SIZE`, validaciones de schema).
- [x] Shell iOS + Permission Gate conectados al flujo online-first.
- [x] Compilación multiplatform iOS/macOS en verde.
- [x] Evidencia de QA consolidada en `docs/qa/phase3/`.

## Notas de cierre
- Rate limiting dedicado se pospone a **Phase 3.1** (en Phase 3 se mantiene auth + payload guards).
- Política de idempotencia con TTL de 14 días documentada en `docs/PHASE3_IDEMPOTENCY.md`.
- Wiring de fuentes TrainingLab en Xcode fue manual sobre `project.pbxproj` y está detallado en `docs/qa/phase3/pbxproj_wiring_note.md`.
