from fastapi import FastAPI


app = FastAPI(title="training-lab-api")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Welcome to Training Lab",
        "service": "training-lab-api",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "training-lab-api",
        "version": "0.0.0",
        "git_sha": "unknown",
    }
