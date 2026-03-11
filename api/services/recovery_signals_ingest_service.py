from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.core.config import get_settings
from api.repositories.daily_domains_repository import (
    RecoverySignalUpsert,
    get_recovery_signal_snapshots_by_uuids,
    upsert_recovery_signals,
)
from api.repositories.idempotency_repository import compute_request_hash, create_record, get_record
from api.repositories.user_repository import get_or_create_default_user, update_user_timezone_if_valid
from api.schemas.ingest import IngestRecoverySignalsResponse, RecoverySignalsIngestRequest
from api.services.daily_domain_recompute_service import DailyDomainRecomputeService
from api.services.daily_domain_rules import APPLE_HEALTH_PROVIDER
from api.services.daily_recovery_recompute_service import DailyRecoveryRecomputeService
from api.services.ingest_service import IdempotencyConflictError, PayloadLimitExceededError
from api.services.local_date import resolve_authoritative_timezone_name, resolve_measurement_local_date


@dataclass
class RecoverySignalsIngestService:
    db: Session

    def ingest_recovery_signals(
        self,
        *,
        payload: RecoverySignalsIngestRequest,
        idempotency_key: str,
    ) -> IngestRecoverySignalsResponse:
        settings = get_settings()
        if len(payload.recovery_signals) > settings.ingest_max_batch_size:
            raise PayloadLimitExceededError(
                f"Batch size {len(payload.recovery_signals)} exceeds INGEST_MAX_BATCH_SIZE={settings.ingest_max_batch_size}"
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
            return IngestRecoverySignalsResponse.model_validate(replay_response)

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

        signal_uuids = [item.healthkit_signal_uuid for item in payload.recovery_signals]
        pre_snapshots = get_recovery_signal_snapshots_by_uuids(
            self.db,
            user_id=user.id,
            signal_uuids=signal_uuids,
        )
        inserted, updated = upsert_recovery_signals(
            self.db,
            rows=[
                RecoverySignalUpsert(
                    healthkit_signal_uuid=item.healthkit_signal_uuid,
                    user_id=user.id,
                    signal_type=item.signal_type,
                    measured_at=item.measured_at,
                    local_date=resolve_measurement_local_date(
                        measured_at=item.measured_at,
                        user_timezone=authoritative_timezone,
                        fallback_timezone=settings.trimp_timezone_fallback,
                    ),
                    signal_value=item.value,
                    source_bundle_id=item.source_bundle_id,
                    provider=APPLE_HEALTH_PROVIDER,
                    source_count=item.source_count,
                    has_mixed_sources=item.has_mixed_sources,
                    primary_device_name=item.primary_device_name,
                )
                for item in payload.recovery_signals
            ],
        )
        post_snapshots = get_recovery_signal_snapshots_by_uuids(
            self.db,
            user_id=user.id,
            signal_uuids=signal_uuids,
        )
        affected_dates = DailyDomainRecomputeService().collect_recovery_signal_affected_dates(
            pre_snapshots=pre_snapshots,
            post_snapshots=post_snapshots,
        )
        recompute_summary = DailyRecoveryRecomputeService(settings=settings).recompute_for_dates(
            self.db,
            user_id=user.id,
            dates=sorted(affected_dates),
        )

        response = IngestRecoverySignalsResponse(
            inserted=inserted,
            updated=updated,
            total_received=len(payload.recovery_signals),
            rebuilt_dates=recompute_summary.rebuilt_dates,
            rebuilt_daily_recovery_rows=recompute_summary.rebuilt_daily_recovery_rows,
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
