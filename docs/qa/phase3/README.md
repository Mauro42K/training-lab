# Phase 3 QA Evidence README

## Fecha / Entorno
- Fecha de ejecución: 2026-03-05 23:02:35 EST
- Host: macOS 26.3 (Build 25D125)
- Simulador iOS usado: iPhone 17 Pro
- Repo: `/Users/mauro/Training-lab`

## Comandos ejecutados

### API pública
```bash
curl -si https://api.training-lab.mauro42k.com/health \
  | tee docs/qa/phase3/backend_health.log

curl -si "https://api.training-lab.mauro42k.com/v1/workouts?from=2026-01-01T00:00:00Z&to=2026-01-02T00:00:00Z" \
  | tee docs/qa/phase3/backend_auth_401.log
```

### API autenticada
```bash
curl -si -H "X-API-KEY: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/workouts?from=2026-01-01T00:00:00Z&to=2026-01-02T00:00:00Z" \
  | tee docs/qa/phase3/backend_workouts_200.log

curl -si -H "X-API-KEY: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/daily?from=2026-01-01&to=2026-01-07" \
  | tee docs/qa/phase3/backend_daily_200.log
```

### Idempotency
```bash
# payload base
cat >/tmp/phase3-ingest-payload.json <<'JSON'
{
  "workouts": [
    {
      "healthkit_workout_uuid": "00000000-0000-0000-0000-000000000001",
      "sport": "run",
      "start": "2026-01-01T10:00:00Z",
      "end": "2026-01-01T10:30:00Z",
      "duration_sec": 1800,
      "distance_m": 5000.0,
      "energy_kcal": 400.0,
      "source_bundle_id": null,
      "device_name": null
    }
  ]
}
JSON

# payload conflicto (duration_sec distinto)
cat >/tmp/phase3-ingest-payload-conflict.json <<'JSON'
{
  "workouts": [
    {
      "healthkit_workout_uuid": "00000000-0000-0000-0000-000000000001",
      "sport": "run",
      "start": "2026-01-01T10:00:00Z",
      "end": "2026-01-01T10:30:00Z",
      "duration_sec": 1810,
      "distance_m": 5000.0,
      "energy_kcal": 400.0,
      "source_bundle_id": null,
      "device_name": null
    }
  ]
}
JSON

# replay (mismo key + mismo body)
curl -si -X POST "https://api.training-lab.mauro42k.com/v1/ingest/workouts" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $TRAINING_LAB_API_KEY" \
  -H "X-Idempotency-Key: phase3-docs-test-001" \
  --data @/tmp/phase3-ingest-payload.json \
  | tee docs/qa/phase3/backend_idempotency_replay_200.log

# conflict (mismo key + body distinto)
curl -si -X POST "https://api.training-lab.mauro42k.com/v1/ingest/workouts" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: $TRAINING_LAB_API_KEY" \
  -H "X-Idempotency-Key: phase3-docs-test-001" \
  --data @/tmp/phase3-ingest-payload-conflict.json \
  | tee docs/qa/phase3/backend_idempotency_conflict_409.log
```

### Builds
```bash
xcodebuild -project DesignSystemDemo/DesignSystemDemo.xcodeproj -scheme DesignSystemDemo \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build \
  | tee docs/qa/phase3/ios-build.log

xcodebuild -project DesignSystemDemo/DesignSystemDemo.xcodeproj -scheme DesignSystemDemo \
  -destination 'platform=macOS' build \
  | tee docs/qa/phase3/macos-build.log
```

## Resultados esperados/observados
- `/health`: 200
- `/v1/workouts` sin key: 401
- `/v1/workouts` con key: 200
- `/v1/daily` con key: 200
- replay idempotency: 200 + `idempotent_replay=true`
- conflict idempotency: 409
- build iOS: PASS
- build macOS: PASS

## Evidencia UI (manual)
No se capturaron screenshots automáticamente desde Codex en este bloque.
Tomar manualmente y guardar con estos nombres exactos en `docs/qa/phase3/screenshots/`:
- `ios_gate_missing_key.png`
- `ios_gate_ready.png`
- `ios_gallery_done.png`
- `macos_gate.png`

Validaciones manuales requeridas:
- B: sin `TRAINING_LAB_API_KEY` en Scheme -> gate controlado + Gallery accesible.
- C: con `TRAINING_LAB_API_KEY` temporal en Scheme -> gate en ready + Gallery accesible.
- D: macOS -> app sin crash.
