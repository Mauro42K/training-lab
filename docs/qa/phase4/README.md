# Phase 4 QA Evidence README

## Fecha / Entorno
- Fecha de ejecución: 2026-03-06 (America/New_York)
- Repo: `/Users/mauro/Training-lab`
- Backend validado:
  - local: `http://127.0.0.1:8000`
  - real: `https://api.training-lab.mauro42k.com`
- Simulador iOS: iPhone 17

## Runtime config persistente (iOS/macOS app)
1. Copiar `DesignSystemDemo/Config/Runtime.Local.example.xcconfig` a `DesignSystemDemo/Config/Runtime.Local.xcconfig`.
2. Definir:
   - `TRAINING_LAB_API_BASE_URL`
   - `TRAINING_LAB_API_KEY`
3. Ejecutar app sin `launchctl setenv`.

Notas:
- `Runtime.Local.xcconfig` está ignorado por git.
- La API key inyectada en build settings queda accesible en metadatos del bundle.
- Solo usar keys de dev/local/staging. Nunca credenciales sensibles de producción en cliente.

## Validaciones backend
```bash
curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/training-load?days=28&sport=all"

curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/training-load?days=28&sport=run"

curl -sS -H "X-API-Key: $TRAINING_LAB_API_KEY" \
  "https://api.training-lab.mauro42k.com/v1/training-load?days=28&sport=strength"
```

Resultado esperado:
- `items.length = 28`
- filtro `all` y `run` con `today > 0` cuando hay carga en el día.
- filtro `strength` con `today = 0` cuando no hay sesiones de fuerza hoy.

## Validaciones iOS (runtime)
- pantalla `Training Load` visible.
- summary `Today/7d/28d` renderiza valores reales.
- filtros `all`, `run`, `strength` actualizan chart y summary.
- tap en día abre detalle.
- detalle muestra sesiones separadas cuando hay multi-session.

## Validaciones 4.1 UX/UI + macOS
- eje temporal del chart legible (28d/21d/14d/7d/Today).
- jerarquía de estados estable: `selected > today > hover > normal`.
- baseline fix validado: valores 0 anclados abajo.
- macOS: hover visible y detalle diario cierra correctamente sin bloquear la app.
- runtime config persistente: sin `launchctl setenv`.

## Cierre de inconsistencia Today
- `today_local`: `2026-03-06`
- último item serie `/v1/training-load` (`all`): `date=2026-03-06`
- estado: PASS (alineados)

## Pendiente trasladado a Phase 4.2
- HealthKit/Apple Fitness ingest real end-to-end no queda resuelto en Phase 4.1.
- Ese alcance se mueve formalmente a Phase 4.2 (HealthKit Real Ingest Enablement).
