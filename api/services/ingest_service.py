from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.core.config import get_settings
from api.repositories.load_repository import get_workout_snapshots_by_uuids
from api.repositories.idempotency_repository import compute_request_hash, create_record, get_record
from api.repositories.user_repository import get_or_create_default_user
from api.repositories.workouts_repository import upsert_workouts
from api.schemas.ingest import IngestWorkoutsResponse, WorkoutsIngestRequest
from api.services.trimp_recompute_service import TrimpRecomputeService


class IdempotencyConflictError(Exception):
    pass


class PayloadLimitExceededError(Exception):
    pass


@dataclass
class IngestService:
    db: Session

    def ingest_workouts(
        self,
        *,
        payload: WorkoutsIngestRequest,
        idempotency_key: str,
    ) -> IngestWorkoutsResponse:
        settings = get_settings()
        if len(payload.workouts) > settings.ingest_max_batch_size:
            raise PayloadLimitExceededError(
                f"Batch size {len(payload.workouts)} exceeds INGEST_MAX_BATCH_SIZE={settings.ingest_max_batch_size}"
            )

        user = get_or_create_default_user(self.db)
        payload_dict = payload.model_dump(mode="json")
        request_hash = compute_request_hash(payload_dict)

        existing = get_record(self.db, user.id, idempotency_key)
        if existing is not None:
            if existing.request_hash != request_hash:
                raise IdempotencyConflictError(
                    "Idempotency key already used with a different payload"
                )
            replay_response = dict(existing.response_json)
            replay_response["idempotent_replay"] = True
            return IngestWorkoutsResponse.model_validate(replay_response)

        workout_uuids = [item.healthkit_workout_uuid for item in payload.workouts]
        pre_snapshots = get_workout_snapshots_by_uuids(
            self.db,
            user_id=user.id,
            workout_uuids=workout_uuids,
        )
        inserted, updated = upsert_workouts(
            self.db,
            user_id=user.id,
            workouts=payload.workouts,
        )
        recompute_service = TrimpRecomputeService(settings=settings)
        recompute_service.recompute_for_workout_uuids(
            self.db,
            user_id=user.id,
            user_timezone=user.timezone,
            workout_uuids=workout_uuids,
            pre_snapshots=pre_snapshots,
        )

        response = IngestWorkoutsResponse(
            inserted=inserted,
            updated=updated,
            total_received=len(payload.workouts),
            idempotent_replay=False,
        )

        create_record(
            self.db,
            user_id=user.id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_json=response.model_dump(mode="json"),
            status_code=200,
        )
        self.db.commit()
        return response
