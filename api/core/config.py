import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    training_lab_api_key: str | None
    ingest_max_batch_size: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    ingest_max_batch_size = int(os.getenv("INGEST_MAX_BATCH_SIZE", "500"))
    return Settings(
        database_url=os.getenv("DATABASE_URL"),
        training_lab_api_key=os.getenv("TRAINING_LAB_API_KEY"),
        ingest_max_batch_size=ingest_max_batch_size,
    )


def get_database_url(strict: bool = False) -> str | None:
    value = get_settings().database_url
    if strict and not value:
        raise RuntimeError(
            "DATABASE_URL is not set. Export DATABASE_URL with a real PostgreSQL DSN before running Alembic."
        )
    return value
