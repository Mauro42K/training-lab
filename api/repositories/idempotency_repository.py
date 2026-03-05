import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import IngestIdempotency


@dataclass
class IdempotencyLookupResult:
    record: IngestIdempotency | None
    request_hash: str


def compute_request_hash(payload: dict) -> str:
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def get_record(db: Session, user_id: UUID, idempotency_key: str) -> IngestIdempotency | None:
    stmt = select(IngestIdempotency).where(
        IngestIdempotency.user_id == user_id,
        IngestIdempotency.idempotency_key == idempotency_key,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_record(
    db: Session,
    *,
    user_id: UUID,
    idempotency_key: str,
    request_hash: str,
    response_json: dict,
    status_code: int,
) -> IngestIdempotency:
    record = IngestIdempotency(
        user_id=user_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_json=response_json,
        status_code=status_code,
        created_at=dt.datetime.now(dt.UTC),
    )
    db.add(record)
    db.flush()
    return record
