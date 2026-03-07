# Phase 4 QA Closure (TRIMP + Training Load)

## Resumen Ejecutivo
Phase 4.0 y 4.1 quedan cerradas con validación funcional end-to-end:

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
- Fix crítico cerrado:
  - mismatch de `Today` entre UI y backend.

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

## Guardrail de cierre de fase
- Phase 4.1 cierra UX polish + estabilidad multiplataforma + runtime config.
- Real ingest de Apple Fitness/HealthKit no se cierra en 4.1.
- Ese alcance pasa formalmente a Phase 4.2 (HealthKit Real Ingest Enablement).

## DoD Checklist (Phase 4.0 + 4.1)
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
