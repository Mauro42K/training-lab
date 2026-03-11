# Stack and Infrastructure

## Application Stack
- Backend framework: FastAPI
- ASGI server: Uvicorn
- Python version target: 3.11+
- Dependency management: `pip` with `requirements.txt`

## Repository Layout
- `api/`: application code
- `docs/`: operating context, roadmap, infra notes, deployment runbook
- `scripts/`: utility scripts for local and ops workflows

## Deployment Defaults
- Source of truth: GitHub repo `Mauro42K/training-lab`
- Runtime host: Coolify on `root@178.156.251.31`
- Deployment mode: Git-based Dockerfile build
- Container port: `8000`
- Stable public domain: `https://api.training-lab.mauro42k.com`
- Staging target domain: `https://api-staging.training-lab.mauro42k.com`
- Staging fallback domain (debug/emergency only): `http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io`
- Public health path: `/health`

## Build and Runtime Contract
- Build installs dependencies from `requirements.txt`.
- Build writes `api/deploy_metadata.json` into the image with version, full `git_sha`, and `short_sha`.
- Runtime starts the service with `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- Runtime environment variables:
  - `PORT=8000`
  - `DATABASE_URL`
  - `TRAINING_LAB_API_KEY`
  - `INGEST_MAX_BATCH_SIZE=500`
  - `APP_ENVIRONMENT`
- TLS is terminated by Coolify with Let's Encrypt on `api.training-lab.mauro42k.com`.

## API v1 Contract (Phase 3)
- `POST /v1/ingest/workouts`
  - Required headers: `X-API-KEY`, `X-Idempotency-Key`
  - Enforces batch payload limit from `INGEST_MAX_BATCH_SIZE`
  - Idempotency semantics documented in `docs/PHASE3_IDEMPOTENCY.md`
- `GET /v1/workouts?from&to&sport`
  - Required header: `X-API-KEY`
- `GET /v1/daily?from&to`
  - Required header: `X-API-KEY`
- `/` and `/health` remain public.

## Database
- Coolify database resource name: `training-lab-postgres`
- Engine/image: PostgreSQL (`postgres:18-alpine`)
- Internal service host on Coolify network: `j8cccgk8o4ock4c0s8sw8k48`
- Database name: `training_lab`
- Database user: `training_lab`
- Production `DATABASE_URL` is configured in Coolify on the `training-lab-api` service environment variables.
- Staging database resource name: `training-lab-postgres-staging`
- Staging internal service host on Coolify network: `u0wosgo04s008g44k4gkgwok`
- Staging database name: `training_lab_staging`
- Staging database user: `training_lab_staging`
- Staging baseline created from a one-shot logical clone of production.
- Do not store DB passwords in repository docs. Rotate secrets directly in Coolify when needed.

## Environment Verification
- `/health` now returns explicit `environment`.
- Expected values:
  - production: `environment=production`
  - staging: `environment=staging`
- Minimum verification before any destructive or reconciliation test:
  1. confirm domain/URL target
  2. confirm `/health.environment`
  3. confirm Coolify service/resource name
  4. confirm DB host/resource name

## Staging Status
- Separate staging API service created in Coolify: `training-lab-api-staging`
- Separate staging PostgreSQL created in Coolify: `training-lab-postgres-staging`
- Current clone validation counts:
  - production: `workouts=3436`, `workout_load=3173`, `daily_load=9720`
  - staging: `workouts=3436`, `workout_load=3173`, `daily_load=9720`
- Canonical staging hostname is operational:
  - `api-staging.training-lab.mauro42k.com`
- Canonical staging DNS resolves to `178.156.251.31`.
- TLS is issued and valid on the canonical staging hostname.
- The `sslip` host remains only as fallback/debug access, not as the primary route.

## Decisions Recorded
- Use FastAPI for the smallest reliable HTTP skeleton.
- Use a root `Dockerfile` so Coolify can build the service without guessing the runtime.
- Install `curl` in the image because Coolify's container health checks expect `curl` or `wget` inside the runtime image.
- Keep application version at `0.0.0` until explicit SemVer release management is introduced.
- Bake deploy metadata into the image so `/health` can report commit metadata without relying on runtime-only env vars.
- Never paste tokens into logs or docs; rotate immediately if exposure happens.
