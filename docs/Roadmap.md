# Training Lab Roadmap

## Phase 0 — Automation & Infrastructure Bootstrap
- Status: CLOSED on 2026-03-04 (America/New_York).
- Bootstrap repository structure.
- Establish the documentation baseline.
- Ship a deployable FastAPI health service through Coolify.
- Phase 0.1 patch note:
- Custom domain + TLS enabled: https://api.training-lab.mauro42k.com
- `/health` now returns baked metadata (`deploy_metadata.json`) with `git_sha` and `short_sha`
- GitHub Actions CI added
- Commit reference: `33d43855c4a2459269ad9ba7dc1273b4c9ed0e01`

## Next Phases
- Design the design-first product shell around the core tabs.
- Expand the API beyond placeholder telemetry and health metadata.
- Add CI, environment promotion, and automated smoke tests.
