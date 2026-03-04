# Training Lab Codex Context

## Repo
- Training Lab is the source repository for the product foundation.
- This file is the source of truth for every Codex run.

## Non-Negotiables
- Design-first.
- Battery transparent.
- TRIMP hero.

## Product Tabs
- Home
- Trends
- Workouts
- Body
- More
- Coach

## Workflow
- Shell -> Service -> HTTP QA.
- Keep patches scoped and explicit.
- Never leave uncommitted changes.
- Always update documentation before pushing a new version.

## Infra
- GitHub repository: `Mauro42K/training-lab`
- VPS host: `root@178.156.251.31`
- Deploy platform: Coolify running on the VPS.
- Phase 0 deploy target: FastAPI service from this repository.
- Stable API domain target: `https://api.training-lab.mauro42k.com`
- Default start command: `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- Local smoke test: `curl -i http://127.0.0.1:8000/health`
- Remote smoke test: `curl -i https://api.training-lab.mauro42k.com/health`

## Security
- Never paste tokens into docs, logs, or chat.
- If a token is exposed, rotate it immediately and document the rotation.

## How To Work With Codex
- Always read this file first.
- Inspect the current tree before editing anything else.
- Keep patches scoped.
- Produce diffs through git.
- Run QA after changes.
- Commit and push only when the tree is clean.
