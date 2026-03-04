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
- Public health path: `/health`

## Build and Runtime Contract
- Build installs dependencies from `requirements.txt`.
- Runtime starts the service with `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- `PORT` is the only required runtime environment variable.

## Decisions Recorded
- Use FastAPI for the smallest reliable HTTP skeleton.
- Use a root `Dockerfile` so Coolify can build the service without guessing the runtime.
- Install `curl` in the image because Coolify's container health checks expect `curl` or `wget` inside the runtime image.
- Keep version and git SHA as placeholders until release automation exists.
