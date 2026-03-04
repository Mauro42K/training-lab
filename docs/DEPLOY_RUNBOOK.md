# Deploy Runbook

## Scope
- Phase 0 deploys the FastAPI backend in this repository to Coolify on `root@178.156.251.31`.
- Live Phase 0 URL: `http://p8w04c88088gw844okkw80gg.178.156.251.31.sslip.io`

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
13. Enable a generated domain or attach the desired domain.
14. Click `Deploy`.

## Automated Server-Side Setup Via Coolify API
1. SSH into the host: `ssh root@178.156.251.31`.
2. Create a temporary API token inside the Coolify container:
   `docker exec coolify sh -lc 'php artisan tinker --execute="session([\"currentTeam\" => App\\Models\\Team::find(0)]); echo App\\Models\\User::find(0)->createToken(\"codex-bootstrap\")->plainTextToken;"'`
3. Use that token against the internal Coolify API endpoint at `http://127.0.0.1:8080/api/v1`.
4. Create the project:
   `curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"training-lab","description":"Training Lab phase 0 bootstrap"}' http://127.0.0.1:8080/api/v1/projects`
5. Read the returned project UUID and environment UUID from `GET /api/v1/projects/<project_uuid>`.
6. Create the application from the public GitHub repository using build pack `dockerfile`.
7. Set `dockerfile_location` to `/Dockerfile`, `ports_exposes` to `8000`, `base_directory` to `/`, `health_check_path` to `/health`, and enable `autogenerate_domain`.
8. Set `PORT=8000` on the application envs.
9. Trigger deployment with `GET /api/v1/deploy?uuid=<application_uuid>`.
10. After the deployment is healthy, remove the temporary API token.

## Healthcheck Requirement
- Coolify's container health probe runs inside the application container.
- The image must include `curl` or `wget`; this repository includes `curl` in the `Dockerfile` for that reason.
- If deployment logs show `curl: not found` or `wget: not found`, rebuild after updating the image.

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
5. Run `curl -i https://<coolify-public-url>/health`.

## Rollback
1. Open the service in Coolify.
2. Open `Deployments`.
3. Pick the previous successful deployment.
4. Click `Redeploy`.
5. Verify `curl -i https://<coolify-public-url>/health`.

## SSH Verification And Fallback
- SSH access can verify that Coolify is installed: `ssh root@178.156.251.31 "docker ps --format '{{.Names}}'"`.
- This phase validated that API automation is feasible from the host through `docker exec coolify`.
- If UI automation is not feasible from this terminal, use the dashboard steps above.
- If a CLI-based Coolify workflow becomes available on the host later, keep the same build inputs: repo `Mauro42K/training-lab`, branch `main`, Dockerfile `/Dockerfile`, port `8000`, env `PORT=8000`.

## Smoke Test Checklist
1. Local `GET /health` returns HTTP 200 with placeholder metadata.
2. Remote `GET /health` returns HTTP 200 from the public Coolify URL.
3. Record the final URL back into this document once the service is live.
   Recorded for phase 0: `http://p8w04c88088gw844okkw80gg.178.156.251.31.sslip.io`
