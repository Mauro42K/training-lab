# Phase 4.3 — Staging Environment & Environment Separation

## Objetivo
Separar producción y staging con:
- API separada
- PostgreSQL separada
- clon lógico one-shot de producción hacia staging
- configuración iOS explícita por entorno
- QA operativa sin ambigüedad

## Topología validada

### Production
- API: `https://api.training-lab.mauro42k.com`
- `/health.environment`: `production`
- Coolify app: `training-lab-api`
- PostgreSQL: `training-lab-postgres`

### Staging
- target canónico: `https://api-staging.training-lab.mauro42k.com`
- fallback activo: `http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io`
- `/health.environment`: `staging`
- Coolify app: `training-lab-api-staging`
- PostgreSQL: `training-lab-postgres-staging`

## QA comparativa prod vs staging

Conteos validados tras el clon lógico one-shot:

```text
production
- workouts = 3436
- workout_load = 3173
- daily_load = 9720

staging
- workouts = 3436
- workout_load = 3173
- daily_load = 9720
```

## Smoke HTTP

Production:

```bash
curl -sS https://api.training-lab.mauro42k.com/health
```

Resultado esperado:
- `status=ok`
- `environment=production`

Staging:

```bash
curl -sS http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io/health
curl -sS -H "X-API-KEY: $TRAINING_LAB_STAGING_API_KEY" \
  "http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io/v1/training-load?days=7&sport=all"
```

Resultado esperado:
- `/health` -> `environment=staging`
- `/v1/training-load` -> `200` con datos clonados de staging

## iOS runtime config

`Runtime.Local.example.xcconfig` documenta tres targets:
- `production`
- `staging`
- `local`

Validación mínima:
- debug + staging -> la app resuelve `baseURL` staging
- debug + staging -> badge visible `STAGING`
- release/default -> `production`

## Guardrails operativos
- Nunca usar producción para reconciliación histórica o borrado experimental.
- Toda prueba destructiva debe ejecutarse primero contra staging.
- Confirmar siempre:
  1. URL
  2. `/health.environment`
  3. app resource en Coolify
  4. DB resource en Coolify

## DNS pendiente
- `api-staging.training-lab.mauro42k.com` quedó configurado como dominio objetivo en Coolify.
- El A record público todavía no existe, por lo que la validación operativa usa el fallback `sslip`.
- No cerrar Phase 4.3 como completada hasta que:
  1. `dig +short api-staging.training-lab.mauro42k.com` resuelva
  2. `curl -i https://api-staging.training-lab.mauro42k.com/health` devuelva `200`
