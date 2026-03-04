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
- Public health path: `/health`

## Build and Runtime Contract
- Build installs dependencies from `requirements.txt`.
- Build writes `api/deploy_metadata.json` into the image with version, full `git_sha`, and `short_sha`.
- Runtime starts the service with `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- `PORT` is the only required runtime environment variable.
- TLS is terminated by Coolify with Let's Encrypt on `api.training-lab.mauro42k.com`.

## Decisions Recorded
- Use FastAPI for the smallest reliable HTTP skeleton.
- Use a root `Dockerfile` so Coolify can build the service without guessing the runtime.
- Install `curl` in the image because Coolify's container health checks expect `curl` or `wget` inside the runtime image.
- Keep application version at `0.0.0` until explicit SemVer release management is introduced.
- Bake deploy metadata into the image so `/health` can report commit metadata without relying on runtime-only env vars.
- Never paste tokens into logs or docs; rotate immediately if exposure happens.
