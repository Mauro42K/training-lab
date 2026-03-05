import json
import os
from pathlib import Path

from fastapi import FastAPI

from api.bootstrap import build_v1_router
from api.version import APP_VERSION


app = FastAPI(title="training-lab-api")
app.include_router(build_v1_router())

DEPLOY_METADATA_PATH = Path(__file__).with_name("deploy_metadata.json")
ENV_GIT_SHA_KEYS = (
    "COMMIT_SHA",
    "GIT_COMMIT",
    "RENDER_GIT_COMMIT",
    "GIT_SHA",
    "SOURCE_COMMIT",
    "VERCEL_GIT_COMMIT_SHA",
)


def _read_baked_metadata() -> dict[str, str]:
    if not DEPLOY_METADATA_PATH.exists():
        return {}

    try:
        data = json.loads(DEPLOY_METADATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    metadata: dict[str, str] = {}
    for key in ("version", "git_sha", "short_sha"):
        value = data.get(key)
        if isinstance(value, str) and value:
            metadata[key] = value
    return metadata


def _resolve_deploy_metadata() -> dict[str, str]:
    baked = _read_baked_metadata()
    git_sha = next((os.getenv(key) for key in ENV_GIT_SHA_KEYS if os.getenv(key)), None)
    short_sha = git_sha[:7] if git_sha else None

    version = os.getenv("APP_VERSION") or baked.get("version") or APP_VERSION
    git_sha = git_sha or baked.get("git_sha") or "unknown"
    short_sha = short_sha or baked.get("short_sha") or "unknown"

    return {
        "version": version,
        "git_sha": git_sha,
        "short_sha": short_sha,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Welcome to Training Lab",
        "service": "training-lab-api",
    }


@app.get("/health")
def health() -> dict[str, str | int]:
    deploy_metadata = _resolve_deploy_metadata()
    return {
        "status": "ok",
        "service": "training-lab-api",
        "version": deploy_metadata["version"],
        "git_sha": deploy_metadata["git_sha"],
        "short_sha": deploy_metadata["short_sha"],
        "metrics_model_version": 1,
    }
