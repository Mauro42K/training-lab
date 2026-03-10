# Training Lab

Training Lab is the repository for the product foundation and iterative phase delivery.

Current status:
- Phase 4.2 is closed (real HealthKit ingest pipeline validated end-to-end).
- Real data now flows from iPhone HealthKit to backend PostgreSQL and Training Load endpoints.
- Next planned phase is Phase 4.4 (Workout Reconciliation & Historical Cleanup).

## Local API
1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `uvicorn api.main:app --host 127.0.0.1 --port 8000`.
4. Verify with `curl -i http://127.0.0.1:8000/health`.

## Local iOS/macOS Runtime Config
1. Copy `DesignSystemDemo/Config/Runtime.Local.example.xcconfig` to `DesignSystemDemo/Config/Runtime.Local.xcconfig`.
2. Set:
   - `TRAINING_LAB_API_BASE_URL`
   - `TRAINING_LAB_API_KEY`
3. Build and run `DesignSystemDemo` normally from Xcode; no `launchctl setenv` is required.

Security note:
- Values injected through build settings end up in app bundle metadata.
- Use only dev/local/staging keys in `Runtime.Local.xcconfig`.
- Never embed production-sensitive credentials in the client bundle.

## Deploy
1. Push `main` to `Mauro42K/training-lab`.
2. In Coolify, create an application from the GitHub repository using the root `Dockerfile`.
3. Set `PORT=8000`.
4. Deploy and verify `/health`.

Detailed operational steps live in `docs/DEPLOY_RUNBOOK.md`.

## Documentation Source of Truth
- Roadmap: `docs/Roadmap.md`
- Changelog: `docs/CHANGELOG.md`
- Codex context: `docs/CODEX_CONTEXT.md`
- Phase 4 QA closure: `docs/Phase4_QA.md`
- Dev ingest notes: `docs/README-dev.md`
