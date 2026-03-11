from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.core.config import get_settings
from api.repositories.daily_domains_repository import (
    DailyActivityUpsert,
    get_existing_daily_activity_dates,
    upsert_daily_activity_rows,
)
from api.repositories.idempotency_repository import compute_request_hash, create_record, get_record
from api.repositories.user_repository import get_or_create_default_user, update_user_timezone_if_valid
from api.schemas.ingest import DailyActivityIngestRequest, IngestDailyActivityResponse
from api.services.daily_domain_recompute_service import DailyDomainRecomputeService
from api.services.daily_domain_rules import APPLE_HEALTH_PROVIDER, resolve_daily_activity_completeness
from api.services.daily_recovery_recompute_service import DailyRecoveryRecomputeService
from api.services.ingest_service import IdempotencyConflictError, PayloadLimitExceededError
from api.services.local_date import resolve_authoritative_timezone_name, resolve_daily_activity_local_date


@dataclass
class DailyActivityIngestService:
    db: Session

    def ingest_daily_activity(
        self,
        *,
        payload: DailyActivityIngestRequest,
        idempotency_key: str,
    ) -> IngestDailyActivityResponse:
        settings = get_settings()
        if len(payload.daily_activity) > settings.ingest_max_batch_size:
            raise PayloadLimitExceededError(
                f"Batch size {len(payload.daily_activity)} exceeds INGEST_MAX_BATCH_SIZE={settings.ingest_max_batch_size}"
            )

        user = get_or_create_default_user(self.db)
        payload_dict = payload.model_dump(mode="json")
        request_hash = compute_request_hash(payload_dict)

        existing = get_record(self.db, user.id, idempotency_key)
        if existing is not None:
            if existing.request_hash != request_hash:
                raise IdempotencyConflictError("Idempotency key already used with a different payload")
            replay_response = dict(existing.response_json)
            replay_response["idempotent_replay"] = True
            return IngestDailyActivityResponse.model_validate(replay_response)

        authoritative_timezone = resolve_authoritative_timezone_name(
            request_timezone=payload.timezone,
            stored_timezone=user.timezone,
            fallback_timezone=settings.trimp_timezone_fallback,
        )
        update_user_timezone_if_valid(
            self.db,
            user=user,
            timezone_name=authoritative_timezone,
        )

        rows_by_date: dict = {}
        for item in payload.daily_activity:
            local_date = resolve_daily_activity_local_date(
                bucket_start=item.bucket_start,
                user_timezone=authoritative_timezone,
                fallback_timezone=settings.trimp_timezone_fallback,
            )
            completeness = resolve_daily_activity_completeness(
                steps=item.steps,
                walking_running_distance_m=item.walking_running_distance_m,
                active_energy_kcal=item.active_energy_kcal,
            )
            rows_by_date[local_date] = DailyActivityUpsert(
                user_id=user.id,
                local_date=local_date,
                steps=item.steps,
                walking_running_distance_m=item.walking_running_distance_m,
                active_energy_kcal=item.active_energy_kcal,
                completeness_status=completeness or "partial",
                provider=APPLE_HEALTH_PROVIDER,
                source_count=item.source_count,
                has_mixed_sources=item.has_mixed_sources,
                primary_device_name=item.primary_device_name,
            )

        affected_dates = sorted(rows_by_date)
        existing_dates = get_existing_daily_activity_dates(
            self.db,
            user_id=user.id,
            dates=affected_dates,
        )
        reset_summary = DailyDomainRecomputeService().reset_daily_rows_for_dates(
            self.db,
            user_id=user.id,
            dates=affected_dates,
            include_sleep=False,
            include_activity=True,
            include_recovery=True,
        )
        upsert_daily_activity_rows(self.db, rows=list(rows_by_date.values()))
        DailyRecoveryRecomputeService(settings=settings).recompute_for_dates(
            self.db,
            user_id=user.id,
            dates=affected_dates,
        )

        response = IngestDailyActivityResponse(
            inserted=len(set(affected_dates) - existing_dates),
            updated=len(set(affected_dates).intersection(existing_dates)),
            total_received=len(payload.daily_activity),
            rebuilt_dates=len(affected_dates),
            invalidated_daily_recovery_dates=reset_summary.deleted_daily_recovery_rows,
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
