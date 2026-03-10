import os
from urllib.parse import urlsplit, urlunsplit
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    app_environment: str
    training_lab_api_key: str | None
    ingest_max_batch_size: int
    trimp_active_model_version: int
    trimp_active_method: str
    trimp_hr_rest_default: int
    trimp_hr_max_default: int
    trimp_sport_factor_run: float
    trimp_sport_factor_bike: float
    trimp_sport_factor_strength: float
    trimp_sport_factor_walk: float
    trimp_timezone_fallback: str

    @property
    def trimp_sport_factors(self) -> dict[str, float]:
        return {
            "run": self.trimp_sport_factor_run,
            "bike": self.trimp_sport_factor_bike,
            "strength": self.trimp_sport_factor_strength,
            "walk": self.trimp_sport_factor_walk,
        }


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _normalize_database_url(value: str | None) -> str | None:
    if value is None:
        return None

    raw = value.strip()
    if raw == "":
        return None

    parsed = urlsplit(raw)
    scheme = parsed.scheme

    if scheme in {"postgres", "postgresql"}:
        scheme = "postgresql+psycopg"

    return urlunsplit((scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    ingest_max_batch_size = _env_int("INGEST_MAX_BATCH_SIZE", 500)
    return Settings(
        database_url=_normalize_database_url(os.getenv("DATABASE_URL")),
        app_environment=os.getenv("APP_ENVIRONMENT", "production"),
        training_lab_api_key=os.getenv("TRAINING_LAB_API_KEY"),
        ingest_max_batch_size=ingest_max_batch_size,
        trimp_active_model_version=_env_int("TRIMP_ACTIVE_MODEL_VERSION", 1),
        trimp_active_method=os.getenv("TRIMP_ACTIVE_METHOD", "banister_hrr"),
        trimp_hr_rest_default=_env_int("TRIMP_HR_REST_DEFAULT", 60),
        trimp_hr_max_default=_env_int("TRIMP_HR_MAX_DEFAULT", 190),
        trimp_sport_factor_run=_env_float("TRIMP_SPORT_FACTOR_RUN", 1.0),
        trimp_sport_factor_bike=_env_float("TRIMP_SPORT_FACTOR_BIKE", 0.75),
        trimp_sport_factor_strength=_env_float("TRIMP_SPORT_FACTOR_STRENGTH", 0.35),
        trimp_sport_factor_walk=_env_float("TRIMP_SPORT_FACTOR_WALK", 0.25),
        trimp_timezone_fallback=os.getenv("TRIMP_TIMEZONE_FALLBACK", "America/New_York"),
    )


def get_database_url(strict: bool = False) -> str | None:
    value = get_settings().database_url
    if strict and not value:
        raise RuntimeError(
            "DATABASE_URL is not set. Export DATABASE_URL with a real PostgreSQL DSN before running Alembic."
        )
    return value
