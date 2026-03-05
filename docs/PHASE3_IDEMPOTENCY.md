# Phase 3 Idempotency Policy

## Scope
- Applies to `POST /v1/ingest/workouts`.
- Header `X-Idempotency-Key` is mandatory.

## Request Handling Rules
1. Compute `request_hash` from canonical JSON payload.
2. Lookup in `ingest_idempotency` by `(user_id, idempotency_key)`.
3. If key exists and `request_hash` differs: return `409 Conflict`.
4. If key exists and `request_hash` matches: replay stored response with `idempotent_replay=true`.
5. If key does not exist: process ingest, store `request_hash`, `response_json`, `status_code`, then return `200`.

## Retention / TTL
- Retain idempotency records for **14 days**.
- Cleanup can be manual in phase 3.

Manual SQL cleanup:

```sql
DELETE FROM ingest_idempotency
WHERE created_at < NOW() - INTERVAL '14 days';
```

## Notes
- Record-level dedupe for workouts is handled by DB unique constraint `(user_id, healthkit_workout_uuid)` with upsert.
- Rate limiting is intentionally deferred to **Phase 3.1**; phase 3 enforces payload limits.
