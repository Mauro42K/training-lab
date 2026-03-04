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

---

## 7) Referencia de cálculo

Todos los modelos y fórmulas viven en:
- `docs/METRICS_CATALOG.md` (single source of truth)