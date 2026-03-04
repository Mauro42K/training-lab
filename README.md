# Training Lab

Training Lab is the repository bootstrap for the product foundation. Phase 0 ships a minimal FastAPI backend that is designed to deploy cleanly on Coolify.

## Local API
1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `uvicorn api.main:app --host 127.0.0.1 --port 8000`.
4. Verify with `curl -i http://127.0.0.1:8000/health`.

## Deploy
1. Push `main` to `Mauro42K/training-lab`.
2. In Coolify, create an application from the GitHub repository using the root `Dockerfile`.
3. Set `PORT=8000`.
4. Deploy and verify `/health`.

Detailed operational steps live in `docs/DEPLOY_RUNBOOK.md`.
