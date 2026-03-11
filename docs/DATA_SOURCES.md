# Training Lab — Fuentes de Datos (HealthKit) (v0.1)

**Fuente de verdad:** Apple Fitness / Apple Health (HealthKit)  
**Objetivo:** Definir qué datos pedimos, de dónde salen y cómo manejamos “missing data” sin inventar.

---

## 1) Principios (no negociables)

1) **HealthKit-first:** todo lo posible viene de HealthKit.
2) **Transparencia:** si falta data, lo mostramos como **Datos incompletos** y degradamos/ocultamos métricas según reglas.
3) **Anti-duplicados:** deduplicación obligatoria (misma sesión no puede sumar dos veces).
4) **Multi-deporte:** running es el foco, pero bike/strength/walk deben coexistir.
5) **Privacidad:** pedimos el mínimo permiso necesario por fase.

---

## 2) Tipos HealthKit requeridos (por fase)

### Fase MVP (TRIMP + Home TRIMP)
**Requeridos**
- **Workouts**: `HKWorkout`
  - Tipo (running/cycling/functional strength/etc.), start/end, duración, distancia (si aplica), energía (si existe), metadata (source/device).
- **Frecuencia cardiaca (para TRIMP real)**: `HKQuantityTypeIdentifier.heartRate`
  - Samples durante el workout o datos asociados al workout (según disponibilidad).

**Opcionales (pero deseables)**
- **Pasos**: `HKQuantityTypeIdentifier.stepCount`
- **Distancia caminando/corriendo diaria** (para Movement): `HKQuantityTypeIdentifier.distanceWalkingRunning`

> Nota: En MVP, si no hay HR, TRIMP se calcula **estimado** (documentado en METRICS_CATALOG).

---

### Home v1 (Rings + Drivers)
**Requeridos**
- **HRV**: `HKQuantityTypeIdentifier.heartRateVariabilitySDNN` (si está disponible)
- **RHR (Resting Heart Rate)**: `HKQuantityTypeIdentifier.restingHeartRate`
- **Sueño**: `HKCategoryTypeIdentifier.sleepAnalysis`
- **Pasos + distancia caminando** (Movement ring): `stepCount`, `distanceWalkingRunning`

**Opcionales**
- **Energía activa** (detalle Movement): `HKQuantityTypeIdentifier.activeEnergyBurned`

---

### Body v1 (Peso y medidas)
**Requeridos**
- **Peso**: `HKQuantityTypeIdentifier.bodyMass`

**Opcionales**
- **% grasa**: `HKQuantityTypeIdentifier.bodyFatPercentage` (si existe)
- **Masa magra**: `HKQuantityTypeIdentifier.leanBodyMass` (si existe)
- **Medidas corporales** (si el usuario las registra en Apple Health):
  - `HKQuantityTypeIdentifier.waistCircumference`
  - `HKQuantityTypeIdentifier.bodyMassIndex` (BMI) (opcional)

---

## 2.1 Apertura documental Phase 4.5 (Apple-first daily domains)

Phase 4.5 abre la base documental para dominios diarios Apple-first explícitos.

Dominios en scope:
- `sleep_sessions`
- `daily_sleep_summary`
- `daily_recovery`
- `daily_activity`
- `body_measurements`

Tipos mínimos de HealthKit implicados:
- **Sueño**: `HKCategoryTypeIdentifier.sleepAnalysis`
- **HRV**: `HKQuantityTypeIdentifier.heartRateVariabilitySDNN`
- **RHR**: `HKQuantityTypeIdentifier.restingHeartRate`
- **Pasos**: `HKQuantityTypeIdentifier.stepCount`
- **Distancia caminando/corriendo**: `HKQuantityTypeIdentifier.distanceWalkingRunning`
- **Energía activa**: `HKQuantityTypeIdentifier.activeEnergyBurned` (opcional)
- **Peso**: `HKQuantityTypeIdentifier.bodyMass`
- **% grasa**: `HKQuantityTypeIdentifier.bodyFatPercentage` (solo si llega limpia)
- **Masa magra**: `HKQuantityTypeIdentifier.leanBodyMass` (solo si llega limpia)

Guardrails documentales de Phase 4.5:
- No endpoint genérico `/timeseries`.
- No multi-provider.
- No blobs raw completos.
- No expandir `GET /v1/daily` para cubrir estos dominios.
- `daily_recovery` es capa de inputs consolidados, no score final.

---

## 3) Normalización (modelo interno recomendado)

### 3.1 Entidades base
- **WorkoutSession**
  - id interno
  - sport_family: Run | Bike | Strength | Walk | Other
  - start/end, duration_sec
  - distance_m (nullable)
  - active_energy_kcal (nullable)
  - source_name, device_name
  - has_hr (bool)
  - hr_samples_ref / hr_summary (según implementación)
- **DailySummary**
  - date
  - trimp_total (all + por deporte)
  - steps, walk_distance_m
  - sleep_summary (si aplica)
  - hrv, rhr
  - weight/body metrics (si aplica)

### 3.2 Deduplicación (regla mínima v0.1)
Deduplicar sesiones potencialmente duplicadas comparando:
- start/end (o start + duración) dentro de una tolerancia pequeña
- tipo de workout
- distancia/energía similares
- source/device

**Resultado:** 1 sola sesión canónica. Las demás se marcan como “merged/duplicate” y **no suman**.

### 3.3 Foundation naming Phase 4.5

Naming congelado para la apertura documental:
- `sleep_sessions`: capa normalizada de sesiones de sueño
- `daily_sleep_summary`: capa derivada diaria de sueño
- `daily_activity`: derivado diario de movimiento no-workout
- `body_measurements`: normalizado pragmático de métricas corporales
- `daily_recovery`: derivado diario de inputs consolidados

Reglas transversales obligatorias:
- `local_date` explícita en derivados diarios
- timezone IANA explícita
- recompute por fechas afectadas
- `null != 0`
- `measured != estimated`
- `missing` = no row derivada emitida para ese día
- provenance mínima:
  - `provider`
  - `source_count`
  - `has_mixed_sources`
  - `primary_device_name`

Timezone autoritativa en Phase 4.5:
- iOS envía timezone IANA en cada sync/ingest
- backend deriva `local_date` con esa timezone
- backend actualiza la timezone persistida del usuario como default operativo actual
- fallback:
  - timezone persistida del usuario
  - fallback backend solo como última defensa

---

## 4) Reglas de “missing data” (comportamiento UX)

### 4.1 TRIMP
- Si hay HR suficiente → **TRIMP real**.
- Si no hay HR → **TRIMP estimado** (duración + tipo + factor) y se etiqueta **Estimated**.
- Si el workout es tan incompleto que no tiene ni duración confiable → excluir de TRIMP y marcar en detalle “Datos insuficientes”.

### 4.2 Battery/Recovery
- Battery siempre muestra:
  - **drivers** (Sleep, HRV, RHR, Exertion, Movement)
  - **data completeness** (ej. 3/5 drivers presentes)
- Si faltan drivers críticos (ej. sin HRV y sin sueño) → Battery se muestra como “Datos insuficientes” o se degrada con explicación.

Nota Phase 4.5:
- `daily_recovery` no define todavía el score final de Battery/Readiness.
- En esta fase solo se abre la capa diaria de inputs consolidados y completitud.
- condición mínima de emisión:
  - `daily_sleep_summary` o HRV o RHR
- `complete`:
  - requiere sleep + HRV + RHR
- `partial`:
  - row emitida, pero faltan uno o más de esos inputs
- `missing`:
  - no se emite row derivada

### 4.3 Stress
- Si no hay “señal real” de stress, usamos **Stress (proxy)** SOLO si hay inputs mínimos (definidos en METRICS_CATALOG).
- Si inputs insuficientes → ocultar card o mostrar “Insufficient data”.

### 4.4 Movement
- Ring principal: steps + walking distance.
- Si falta uno: se muestra el otro + completeness.
- Energía activa solo en detalle (no bloquea ring).

### 4.5 Body
- Si no hay peso en HealthKit → permitir entrada manual (Phase correspondiente).
- Si hay mezcla de fuentes → priorizar HealthKit, manual como fallback, deduplicar por fecha.

Nota Phase 4.5:
- `weight_kg` es la métrica mínima obligatoria.
- body composition solo se utiliza si llega limpia y confiable desde HealthKit.
- para múltiples mediciones válidas el mismo día, gana la última medición válida por métrica.

---

## 5) Permisos HealthKit (alto nivel)

- Solicitar permisos por fases (MVP primero):
  - Lectura workouts + HR para TRIMP
  - Luego HRV/RHR/sleep/steps
  - Luego weight/body metrics
- UX: explicar por qué se pide cada permiso (“para calcular TRIMP / Battery / Movement / Body”).

---

## 6) Validaciones mínimas (QA)

- Caso A: workouts con HR + sin HR (TRIMP real vs estimado).
- Caso B: día con doble sesión (run + strength).
- Caso C: 14–21 días sin entrenar.
- Caso D: sleep/HRV faltante → Battery degrada y lo explica.
- Caso E: potencial duplicado (misma sesión importada dos veces) → no suma doble.

QA adicional esperado para la foundation de Phase 4.5:
- sueño overnight asignado al día correcto,
- naps sin sleep stages confiables,
- HRV/RHR faltantes sin inventar score,
- día con solo pasos,
- peso presente y composición corporal ausente,
- `null != 0`,
- provenance mínima siempre presente,
- `missing` sin row vacía,
- `primary_device_name = null` cuando no pueda resolverse con confianza.

---

## 7) Referencia de cálculo

Todos los modelos y fórmulas viven en:
- `docs/METRICS_CATALOG.md` (single source of truth)
