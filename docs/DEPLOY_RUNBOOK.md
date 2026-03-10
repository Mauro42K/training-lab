# Deploy Runbook

## Scope
- Phase 0 deploys the FastAPI backend in this repository to Coolify on `root@178.156.251.31`.
- Stable API URL target for phase 0.1: `https://api.training-lab.mauro42k.com`
- Bootstrap fallback URL: `http://p8w04c88088gw844okkw80gg.178.156.251.31.sslip.io`
- Staging target URL: `https://api-staging.training-lab.mauro42k.com`
- Current staging fallback URL: `http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io`

## Local Preparation
1. Ensure the latest `main` branch is pushed to GitHub.
2. Confirm local health: `uvicorn api.main:app --host 127.0.0.1 --port 8000` then `curl -i http://127.0.0.1:8000/health`.

## Preferred Coolify Service Setup
1. Open the Coolify dashboard in the browser.
2. Create or open a project named `training-lab`.
3. Add a new Resource and choose `Application`.
4. Select `Public Repository`.
5. Set repository to `https://github.com/Mauro42K/training-lab`.
6. Set branch to `main`.
7. Choose `Dockerfile` as the build pack.
8. Keep build context as `/`.
9. Keep Dockerfile path as `/Dockerfile`.
10. Set the application name to `training-lab-api`.
11. In Environment Variables, add `PORT=8000`.
12. Expose the service on port `8000`.
13. Attach the custom domain `https://api.training-lab.mauro42k.com`.
14. Ensure HTTPS is forced and Let's Encrypt is enabled for the domain.
15. Click `Deploy`.

## Automated Server-Side Setup Via Coolify API
1. SSH into the host: `ssh root@178.156.251.31`.
2. Create a temporary API token inside a shell variable without printing it:
   `TOKEN="$(docker exec coolify sh -lc 'php artisan tinker --execute="session([\"currentTeam\" => App\\Models\\Team::find(0)]); echo App\\Models\\User::find(0)->createToken(\"codex-bootstrap\")->plainTextToken;" 2>/dev/null)"`
3. Use that token against the internal Coolify API endpoint at `http://127.0.0.1:8080/api/v1`.
4. Create the project:
   `curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"training-lab","description":"Training Lab phase 0 bootstrap"}' http://127.0.0.1:8080/api/v1/projects`
5. Read the returned project UUID and environment UUID from `GET /api/v1/projects/<project_uuid>`.
6. Create the application from the public GitHub repository using build pack `dockerfile`.
7. Set `dockerfile_location` to `/Dockerfile`, `ports_exposes` to `8000`, `base_directory` to `/`, `health_check_path` to `/health`, and enable `autogenerate_domain`.
8. Set `PORT=8000` on the application envs.
9. Update the application domain with `domains=https://api.training-lab.mauro42k.com` and keep `is_force_https_enabled=true`.
10. Trigger deployment with `GET /api/v1/deploy?uuid=<application_uuid>&force=true`.
11. After the deployment is healthy, remove the temporary API token.

## Healthcheck Requirement
- Coolify's container health probe runs inside the application container.
- The image must include `curl` or `wget`; this repository includes `curl` in the `Dockerfile` for that reason.
- If deployment logs show `curl: not found` or `wget: not found`, rebuild after updating the image.

## Deploy Metadata
- The Docker build writes `api/deploy_metadata.json` inside the image.
- `/health` resolves deploy metadata in this order:
  1. Runtime env vars: `APP_VERSION`, then `COMMIT_SHA` / `GIT_COMMIT` / `RENDER_GIT_COMMIT` / `GIT_SHA`.
  2. Baked file: `api/deploy_metadata.json`.
  3. Fallback: `unknown`.
- Verify with `curl -i https://api.training-lab.mauro42k.com/health` and confirm `git_sha` plus `short_sha` are present.

## Domain, TLS, And Security
1. In Coolify open the `training-lab-api` application.
2. In `General` or `Domains`, replace the sslip.io entry with `https://api.training-lab.mauro42k.com`.
3. Save and confirm `Force HTTPS` remains enabled.
4. Let Coolify request or renew the Let's Encrypt certificate for the custom domain.
5. Trigger a redeploy and verify `https://api.training-lab.mauro42k.com/health`.
6. Never paste API tokens into the UI, docs, shell history notes, or chat.
7. If a token is ever exposed, rotate it immediately and record the rotation in this runbook.

## Runtime Values
- Build context: `/`
- Dockerfile path: `/Dockerfile`
- Internal port: `8000`
- Start command inside the container is provided by the Docker image: `uvicorn api.main:app --host 0.0.0.0 --port 8000`

## Redeploy
1. Push a new commit to `main`.
2. Open the service in Coolify.
3. Click `Deploy`.
4. Wait until the deployment logs report the container as healthy.
5. Run `curl -i https://api.training-lab.mauro42k.com/health`.

## Staging Environment Setup (Phase 4.3)
1. In Coolify project `training-lab`, create a separate `staging` environment.
2. Create a separate PostgreSQL resource:
   - resource name: `training-lab-postgres-staging`
   - database: `training_lab_staging`
   - user: `training_lab_staging`
3. Create a separate application:
   - resource name: `training-lab-api-staging`
   - same repository and branch
   - same Dockerfile build path
4. Set staging env vars independently:
   - `DATABASE_URL`
   - `TRAINING_LAB_API_KEY`
   - `INGEST_MAX_BATCH_SIZE`
   - `APP_ENVIRONMENT=staging`
5. Trigger staging deploy and confirm `/health` returns `environment=staging`.

## Production -> Staging Clone (One-Shot)
1. Never share the same DB resource between prod and staging.
2. Create staging DB first.
3. Run a logical clone from prod into staging.
4. Validate counts on both sides:
   - `workouts`
   - `workout_load`
   - `daily_load`
5. After the initial clone, staging is allowed to diverge. No continuous sync.

## Environment Validation Checklist
Before any destructive or reconciliation experiment:
1. Confirm the URL you are using:
   - production: `https://api.training-lab.mauro42k.com`
   - staging fallback: `http://v0w8cgwwos8go0ggswgg4wgk.178.156.251.31.sslip.io`
2. Confirm `/health`:
   - production -> `environment=production`
   - staging -> `environment=staging`
3. Confirm the Coolify resource:
   - production app: `training-lab-api`
   - staging app: `training-lab-api-staging`
4. Confirm the DB resource:
   - production DB: `training-lab-postgres`
   - staging DB: `training-lab-postgres-staging`

## DNS Note For Canonical Staging Hostname
- Coolify can be configured with `https://api-staging.training-lab.mauro42k.com` as the canonical target.
- External routing will remain on the sslip fallback until the public DNS A record is created for `api-staging.training-lab.mauro42k.com`.
- Do not assume the canonical domain is active until:
  1. `dig +short api-staging.training-lab.mauro42k.com` resolves
  2. `curl -i https://api-staging.training-lab.mauro42k.com/health` returns 200

## Rollback
1. Open the service in Coolify.
2. Open `Deployments`.
3. Pick the previous successful deployment.
4. Click `Redeploy`.
5. Verify `curl -i https://api.training-lab.mauro42k.com/health`.

## SSH Verification And Fallback
- SSH access can verify that Coolify is installed: `ssh root@178.156.251.31 "docker ps --format '{{.Names}}'"`.
- This phase validated that API automation is feasible from the host through `docker exec coolify`.
- If UI automation is not feasible from this terminal, use the dashboard steps above.
- If a CLI-based Coolify workflow becomes available on the host later, keep the same build inputs: repo `Mauro42K/training-lab`, branch `main`, Dockerfile `/Dockerfile`, port `8000`, env `PORT=8000`.

## Smoke Test Checklist
1. Local `GET /health` returns HTTP 200 with version plus non-unknown `git_sha`.
2. Remote `GET /health` returns HTTP 200 from `https://api.training-lab.mauro42k.com`.
3. Keep the sslip.io URL only as a temporary fallback, not the primary endpoint.
