# Phase 4 QA Evidence README

## Fecha / Entorno
- Fecha de cierre documental Phase 4.2: 2026-03-09 (America/Mexico_City)
- Repo: `/Users/mauro/Training-lab`
- Backend validado:
  - local: `http://127.0.0.1:8000`
  - real: `https://api.training-lab.mauro42k.com`
- Simulador iOS: iPhone 17
- Device real Phase 4.2: iPhone físico con HealthKit autorizado

## Runtime config persistente (iOS/macOS app)
1. Copiar `DesignSystemDemo/Config/Runtime.Local.example.xcconfig` a `DesignSystemDemo/Config/Runtime.Local.xcconfig`.
2. Definir:
   - `TRAINING_LAB_RUNTIME_ENV`
   - `TRAINING_LAB_API_BASE_URL`
   - `TRAINING_LAB_API_KEY`
3. Ejecutar app sin `launchctl setenv`.

Notas:
- `Runtime.Local.xcconfig` está ignorado por git.
- La API key inyectada en build settings queda accesible en metadatos del bundle.
- Solo usar keys de dev/local/staging. Nunca credenciales sensibles de producción en cliente.
- En debug, la app muestra un badge visible del entorno activo.

## Validaciones backend
```bash
curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/training-load?days=28&sport=all"

curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/training-load?days=28&sport=run"

curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/training-load?days=28&sport=strength"
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

## Validaciones 4.1 UX/UI + macOS
- eje temporal del chart legible (28d/21d/14d/7d/Today).
- jerarquía de estados estable: `selected > today > hover > normal`.
- baseline fix validado: valores 0 anclados abajo.
- macOS: hover visible y detalle diario cierra correctamente sin bloquear la app.
- runtime config persistente: sin `launchctl setenv`.

## Validaciones 4.2 ingest real
- HealthKit authorization en iPhone real: PASS.
- `fetchWorkouts(since:nil)` histórico: PASS.
- Dataset histórico HealthKit obtenido: **3436 workouts**.
- Ingest procesado en **9 batches** hacia `POST /v1/ingest/workouts`: PASS.
- Persistencia PostgreSQL validada con workouts reales: PASS.
- `GET /v1/training-load` devuelve valores TRIMP reales tras ingest: PASS.
- `sync_mode` cambia correctamente de `bootstrap` a `incremental`: PASS.
- estado final de sync: `ready`: PASS.
- refresh post-ingest corregido al usar `YYYY-MM-DD` en `GET /v1/daily`: PASS.
- deprecación `totalEnergyBurned` resuelta con `HKWorkout.statistics(for: .activeEnergyBurned)`: PASS.

## Cierre de inconsistencia Today
- `today_local`: `2026-03-06`
- último item serie `/v1/training-load` (`all`): `date=2026-03-06`
- estado: PASS (alineados)

## Pendiente trasladado a Phase 4.4
- Reconciliación histórica entre backend y HealthKit.
- Manejo de workouts borrados/duplicados desde Apple Fitness.
- Cleanup histórico seguro con recálculo de métricas derivadas.

## Phase 4.2 QA Runbook
- Ver `docs/qa/phase4/PHASE4_2_HEALTHKIT_REAL_INGEST.md` para validación de ingest real en iPhone.

## Validaciones 4.3 staging / environment separation
- `/health` debe diferenciar explícitamente:
  - prod -> `environment=production`
  - staging -> `environment=staging`
- staging debe usar DB distinta de prod.
- conteos mínimos comparativos tras clon:
  - `workouts`
  - `workout_load`
  - `daily_load`
- mientras `api-staging.training-lab.mauro42k.com` no tenga DNS público, QA HTTP de staging puede ejecutarse con el fallback:
  - `http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io`

## Phase 4.3 QA Runbook
- Ver `docs/qa/phase4/PHASE4_3_STAGING_ENVIRONMENT.md`.
