# Phase 4.5 — Block 7 QA / Hardening Evidence

## Fecha / contexto
- Fecha de ejecución: 2026-03-11 (America/Mexico_City)
- Repo local: `/Users/mauro/Training-lab`
- SHA local validado: `360e001`
- Objetivo del bloque:
  - hardening de contratos ya implementados,
  - validación de consistencia entre dominios,
  - validación de staging,
  - evidencia reproducible para cierre de fase.

## Scope validado
- Ingest:
  - `sleep_sessions`
  - `daily_activity`
  - `body_measurements`
  - `recovery_signals`
- Recompute:
  - `daily_sleep_summary`
  - `daily_recovery`
- Query contracts:
  - `GET /v1/daily-domains/sleep`
  - `GET /v1/daily-domains/activity`
  - `GET /v1/daily-domains/recovery`
  - `GET /v1/daily-domains/body-measurements`
- Summary contract:
  - `GET /v1/home/summary`
- Contrato legacy preservado:
  - `GET /v1/daily`

## QA local automatizado

### Comando ejecutado
```bash
pytest -q \
  tests/test_daily_domains_query_service.py \
  tests/test_daily_domains_api.py \
  tests/test_daily_recovery_builder.py \
  tests/test_daily_recovery_recompute_service.py \
  tests/test_recovery_signals_ingest_service.py \
  tests/test_recovery_signals_ingest_api.py \
  tests/test_daily_activity_ingest_service.py \
  tests/test_daily_activity_ingest_api.py \
  tests/test_body_measurements_ingest_service.py \
  tests/test_body_measurements_ingest_api.py \
  tests/test_body_measurements_canonicalizer.py \
  tests/test_sleep_ingest_service.py \
  tests/test_sleep_ingest_api.py \
  tests/test_sleep_summary_builder.py \
  tests/test_trimp_recompute_service.py \
  tests/test_daily_domain_rules.py \
  tests/test_local_date_daily_domains.py
```

### Resultado
- `54 passed in 0.72s`

### Cobertura validada
- `sleep -> recovery` rebuild.
- `activity -> recovery` rebuild.
- `load -> recovery` rebuild.
- `missing = no row emitida`.
- `null != 0`.
- `active_energy_kcal` nullable.
- `daily_recovery` sin score.
- selección canónica diaria:
  - `main_sleep`
  - `nap`
  - última HRV/RHR del día
  - última medición válida body por métrica.
- `body_measurements` expuesto sin tabla daily nueva.
- `home summary` como composición pura.

## QA sintáctico

### Comando ejecutado
```bash
python -m py_compile \
  api/routers/v1/daily_domains.py \
  api/routers/v1/__init__.py \
  api/schemas/daily_domains.py \
  api/services/daily_domains_query_service.py \
  api/services/home_summary_service.py \
  api/repositories/daily_sleep_repository.py \
  api/repositories/daily_activity_repository.py \
  api/repositories/daily_recovery_repository.py \
  api/repositories/body_measurements_repository.py \
  api/services/body_measurements_canonicalizer.py \
  api/services/daily_recovery_builder.py \
  api/services/daily_recovery_recompute_service.py \
  api/services/recovery_signals_ingest_service.py \
  api/repositories/daily_domains_repository.py
```

### Resultado
- PASS

## QA staging

### Preconditions
- Host canónico staging:
  - `https://api-staging.training-lab.mauro42k.com`
- API key de staging cargada localmente fuera de git.

### Comandos reproducibles
```bash
curl -sS -D - https://api-staging.training-lab.mauro42k.com/health

curl -sS -D - \
  -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "https://api-staging.training-lab.mauro42k.com/v1/training-load?days=3&sport=all"

curl -sS -D - \
  -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "https://api-staging.training-lab.mauro42k.com/v1/daily?from=2026-03-09&to=2026-03-11"

curl -sS -D - \
  -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "https://api-staging.training-lab.mauro42k.com/v1/daily-domains/sleep?from=2026-03-05&to=2026-03-07"

curl -sS -D - \
  -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "https://api-staging.training-lab.mauro42k.com/v1/daily-domains/activity?from=2026-03-05&to=2026-03-07"

curl -sS -D - \
  -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "https://api-staging.training-lab.mauro42k.com/v1/daily-domains/recovery?from=2026-03-05&to=2026-03-07"

curl -sS -D - \
  -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "https://api-staging.training-lab.mauro42k.com/v1/daily-domains/body-measurements?from=2026-03-05&to=2026-03-07"

curl -sS -D - \
  -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "https://api-staging.training-lab.mauro42k.com/v1/home/summary?date=2026-03-07"
```

### Resultado observado
- `GET /health`: `200`
- `environment=staging`: PASS
- staging `short_sha`: `1556888`
- `GET /v1/training-load?days=3&sport=all`: `200`
- `GET /v1/daily?...`: `200`
- nuevos endpoints Phase 4.5:
  - `GET /v1/daily-domains/sleep`: `404`
  - `GET /v1/daily-domains/activity`: `404`
  - `GET /v1/daily-domains/recovery`: `404`
  - `GET /v1/daily-domains/body-measurements`: `404`
  - `GET /v1/home/summary`: `404`

## Findings reales

### Finding 1 — staging no tiene desplegada la superficie Phase 4.5
- Severidad: bloqueante para cierre remoto del bloque.
- Evidencia:
  - local SHA validado: `360e001`
  - staging `/health.short_sha`: `1556888`
  - staging responde `200` en endpoints antiguos autenticados,
  - staging responde `404` en todos los endpoints nuevos de Phase 4.5.
- Conclusión:
  - no es caída general de staging,
  - no es problema de auth,
  - es un desfase de deploy / versión remota.

### Finding 2 — contrato legacy sigue estable en staging
- Severidad: informativa.
- Evidencia:
  - `GET /v1/daily`: `200`
  - `GET /v1/training-load`: `200`
- Conclusión:
  - la base staging actual sigue sana,
  - el bloqueo es específicamente la ausencia del build de Phase 4.5.

## Fixes aplicados durante Block 7
- Ningún fix funcional de semántica fue necesario tras la batería local.
- No se aplicó refactor cosmético amplio.
- La deuda estructural se limitó a la evidencia ya arrastrada:
  - `daily_domains_repository.py` sigue reducido respecto al estado anterior, pero no se reabrió refactor grande.

## Pendientes
- Desplegar a staging el SHA que contiene Phase 4.5.
- Reejecutar exactamente los curls de este documento contra staging.
- Confirmar que staging devuelve `200` y contratos correctos para:
  - `daily-domains/sleep`
  - `daily-domains/activity`
  - `daily-domains/recovery`
  - `daily-domains/body-measurements`
  - `home/summary`
- Solo después de eso puede considerarse cerrado el hardening remoto del bloque.

## Decisión operativa
- Hardening local: suficiente y reproducible.
- Cierre remoto en staging: pendiente por deploy externo al alcance de este bloque.
