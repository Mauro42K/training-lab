# Phase 4 QA Evidence README

## Fecha / Entorno
- Fecha de ejecución: 2026-03-06 (America/New_York)
- Repo: `/Users/mauro/Training-lab`
- Backend validado: `http://127.0.0.1:8000`
- Simulador iOS: iPhone 17

## Validaciones backend
```bash
curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "http://127.0.0.1:8000/v1/training-load?days=28&sport=all"

curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "http://127.0.0.1:8000/v1/training-load?days=28&sport=run"

curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "http://127.0.0.1:8000/v1/training-load?days=28&sport=strength"
```

Resultado esperado:
- `items.length = 28`
- filtro `all` y `run` con `today > 0` cuando hay carga en el día.
- filtro `strength` con `today = 0` cuando no hay sesiones de fuerza hoy.

## Validaciones iOS (runtime)
- pantalla `Training Load` visible.
- summary `Today/7d/28d` renderiza valores reales.
- filtros `all`, `run`, `strength` actualizan chart y summary.
- tap en día abre detalle.
- detalle muestra sesiones separadas cuando hay multi-session.

## Cierre de inconsistencia Today
- `today_local`: `2026-03-06`
- último item serie `/v1/training-load` (`all`): `date=2026-03-06`
- estado: PASS (alineados)
