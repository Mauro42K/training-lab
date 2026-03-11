# Phase 4 QA Closure (TRIMP + Training Load + HealthKit Real Ingest + Staging Separation)

## Resumen Ejecutivo
Phase 4.0, 4.1, 4.2 y 4.3 quedan cerradas con validación funcional end-to-end:

- Backend:
  - TRIMP engine v1 operativo.
  - Recompute pipeline integrado.
  - `GET /v1/training-load` operativo con filtros por deporte.
  - Backfill de carga disponible.
- iOS:
  - `TrainingLoadScreen` funcional con serie de 28 días.
  - Filtros `all/run/bike/strength/walk`.
  - Tap en barra abre detalle diario con sesiones separadas.
  - Polish UX/UI del chart aplicado (axis/state/baseline/sparse handling).
  - Interacción macOS estabilizada (hover/click/detail + cierre explícito).
  - Runtime config persistente (`xcconfig` + bundle values) validado.
  - Separación explícita de entorno `production | staging | local` validada.
  - Badge visible de entorno en debug validado.
  - HealthKit real autorizado y bootstrap histórico ejecutado en iPhone físico.
- Infra:
  - staging API separada operativa.
  - staging PostgreSQL separada operativa.
  - clon lógico inicial prod -> staging validado.
  - host canónico staging con DNS + TLS operativos.
- Fix crítico cerrado:
  - mismatch de `Today` entre UI y backend.

## Validación de cierre Phase 4.2
- HealthKit authorization en device real: PASS.
- Bootstrap ingest real: PASS.
- Dataset histórico ingerido desde HealthKit: **3436 workouts**.
- Ingest procesado en **9 batches** de `POST /v1/ingest/workouts`.
- Persistencia backend verificada en PostgreSQL: PASS.
- `GET /v1/training-load` devuelve TRIMP real tras ingest: PASS.
- Transición de sync confirmada: `bootstrap -> incremental -> ready`.
- Bug post-ingest refresh `422` corregido en `GET /v1/daily`: PASS.
- Warning deprecado de energía en HealthKit resuelto con `HKWorkout.statistics(for: .activeEnergyBurned)`: PASS.

## Validación de cierre del fix `Today`
- `today_local` (simulador): `2026-03-06`
- último item de `/v1/training-load?days=28&sport=all`: `date=2026-03-06`
- Conclusión: **coinciden exactamente**.

Comprobaciones funcionales:
- `all`: `Today=75`, `7d=255`, `28d=944`
- `run`: `Today=75`, `7d=226`, `28d=753`
- `strength`: `Today=0`, `7d=14`, `28d=98`

## Evidencia
- `docs/qa/phase4/README.md`
- `docs/qa/phase4/PHASE4_2_HEALTHKIT_REAL_INGEST.md`
- `docs/qa/phase4/PHASE4_3_STAGING_ENVIRONMENT.md`

## Guardrail de cierre de fase
- Phase 4.1 cierra UX polish + estabilidad multiplataforma + runtime config.
- Real ingest de Apple Fitness/HealthKit no se cierra en 4.1.
- Ese alcance pasa formalmente a Phase 4.2 (HealthKit Real Ingest Enablement).
- Phase 4.2 sí cierra el ingest real end-to-end validado con datos reales.
- Reconciliación histórica, borrados y cleanup pasan a Phase 4.4.

## Validación de cierre Phase 4.3
- staging API service separado: PASS.
- staging PostgreSQL separada: PASS.
- clon lógico one-shot prod -> staging: PASS.
- conteos comparativos validados:
  - `workouts = 3436`
  - `workout_load = 3173`
  - `daily_load = 9720`
- `/health.environment` distingue `production` vs `staging`: PASS.
- runtime iOS distingue `production | staging | local`: PASS.
- host canónico staging `api-staging.training-lab.mauro42k.com`: PASS.
- DNS resuelve a `178.156.251.31`: PASS.
- TLS válido emitido para staging: PASS.
- `GET /health` staging: PASS.
- `GET /v1/training-load?days=7&sport=all` staging: PASS.

## DoD Checklist (Phase 4.0 + 4.1 + 4.2 + 4.3)
- [x] TRIMP engine v1 backend.
- [x] Recompute pipeline incremental.
- [x] Endpoint `GET /v1/training-load` con filtros.
- [x] Backfill operativo por lotes.
- [x] iOS Training Load screen funcional.
- [x] Chart 28 días con filtros por deporte.
- [x] Day detail sheet con soporte multi-session.
- [x] Bug `Today` alignment UI/backend corregido y validado.
- [x] Temporal axis y state polish del chart.
- [x] Baseline fix (barras ancladas abajo para `TRIMP=0`).
- [x] Compatibilidad macOS real en interacción de detalle.
- [x] Runtime config persistente sin dependencia de `launchctl`.
- [x] HealthKit real autorizado en iPhone físico.
- [x] Bootstrap histórico desde HealthKit completado.
- [x] Persistencia PostgreSQL validada con datos reales.
- [x] Sync incremental confirmado después del bootstrap.
- [x] Refresh post-ingest sin `422` en `/v1/daily`.
- [x] Staging API separada creada.
- [x] Staging PostgreSQL separada creada.
- [x] Clon lógico prod -> staging validado.
- [x] Host canónico staging con DNS + TLS operativos.
