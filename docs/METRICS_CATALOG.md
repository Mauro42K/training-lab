# Training Lab — Catálogo de Métricas y Modelos de Cálculo (v0.1)

**Propósito:** Este documento es la **fuente única de verdad** para todas las métricas, scores y modelos usados por la app.  
**metrics_model_version:** `1`  
Esta versión cambia solo cuando cambian fórmulas, definiciones o reglas que afectan la interpretación de una métrica o su histórico.  
Cada cambio debe registrarse en `docs/CHANGELOG.md` y en este `docs/METRICS_CATALOG.md`.  
**Regla:** Ninguna métrica se muestra en UI si no está definida aquí (inputs, fórmula, fallbacks, data completeness, edge cases).  
**UI:** Cada métrica visible debe incluir: **Qué es** + **Cómo se calcula (alto nivel)** + acción **“Ver cálculo”** → referencia a esta sección.

---

## 0) Convenciones

### 0.1 Unidades
- Distancia: metros (m) internamente; mostrar km/mi según settings.
- Tiempo: segundos internamente; mostrar h:mm:ss.
- HR: bpm.
- HRV: ms (SDNN).
- Energía: kcal.
- Fechas: ISO en storage; UI local.

### 0.2 Data completeness
Cada score/metric debe exponer:
- `inputs_present`: lista de inputs presentes
- `inputs_missing`: lista de inputs faltantes
- `completeness_ratio`: ejemplo 3/5 drivers

Para Phase 4.5:
- `complete` = están presentes todos los inputs requeridos del dominio
- `partial` = existe row emitida, pero faltan uno o más inputs requeridos/objetivo
- `missing` = no existe row derivada emitida para ese día

Guardrail:
- no usar rows vacías con `nulls` para representar `missing` en los dominios diarios de Phase 4.5

### 0.3 Etiquetas obligatorias
- Si una métrica es estimada: `Estimated` / `Estimado`
- Si es proxy: `Proxy`
- Si no hay data suficiente: `Insufficient data` / `Datos insuficientes`

### 0.4 Apertura documental Phase 4.5

Phase 4.5 abre la foundation Apple-first de dominios diarios sin introducir todavía scores finales nuevos.

Guardrails explícitos:
- `daily_recovery` en Phase 4.5 es una capa de inputs consolidados, no un score `0-100`.
- No se introducen baselines `7d/28d`, scoring ni explicabilidad premium en esta apertura.
- `GET /v1/daily` no se expande para cubrir los dominios de Phase 4.5.
- Naming congelado:
  - `sleep_sessions`
  - `daily_sleep_summary`

Provenance mínima obligatoria para derivados diarios de Phase 4.5:
- `provider`
- `source_count`
- `has_mixed_sources`
- `primary_device_name`

Regla para `primary_device_name`:
- si puede determinarse con confianza, se llena
- si no puede determinarse con confianza, queda `null`
- no introducir heurísticas complejas de resolución en Phase 4.5

---

## 1) TRIMP (core)

### 1.1 TRIMP (Real, con HR)
**UI label:** TRIMP  
**Qué es:** Carga interna del entrenamiento basada en intensidad y duración.  
**Dónde aparece:** Home (Trend Card / contexto de carga), Trends, Workouts detail.

**Inputs (HealthKit / normalizado)**
- Duración del workout (segundos)
- Serie de HR (bpm) durante el workout, o HR promedio si es lo único disponible
- HRrest y HRmax (cuando existan; si no, defaults configurables en Settings)

**Fórmula (v1 — Banister clásico con HRr)**
Usamos el modelo Banister TRIMP clásico con HRr (frecuencia cardíaca relativa):

- `HRr = clamp((HR_avg - HRrest) / (HRmax - HRrest), 0, 1)`
- `y (Hombre) = 0.64 * exp(1.92 * HRr)`
- `TRIMP = duration_min * HRr * y`

En v1 usamos los coeficientes masculinos; en el futuro se podrá parametrizar para mujeres u otros.

Si existen muestras de HR, se calcula HR_avg como promedio de las muestras; si solo hay HR promedio, se usa y se marca como “partial HR”.

**Fallbacks**
- Si HR es insuficiente → usar TRIMP estimado (sección 1.2).

**Data completeness**
- HR samples completos: HIGH
- Solo HR promedio: MEDIUM (marcar “partial HR”)
- Sin HR: LOW (Estimado)

**Edge cases**
- Pausas largas / HR spikes
- Indoor vs outdoor
- Doble sesión el mismo día

---

### 1.2 TRIMP (Estimado, sin HR) — OBLIGATORIO
**UI label:** TRIMP (Estimated) / TRIMP (Estimado)  
**Qué es:** Estimación de carga cuando no hay HR.

**Inputs**
- Duración (segundos)
- sport_family (Run/Bike/Strength/Walk)
- Opcional futuro: RPE post-workout

**Modelo (v1)**
- `TRIMP_est = duration_minutes * intensity_factor[sport_family]`
- Donde `intensity_factor` es una tabla configurable y documentada.

**Tabla de factores (v1 — propuesta inicial)**
> Nota: estos valores se calibran luego con datos reales.

- Run: 1.00
- Bike: 0.75
- Strength: 0.35 (secondary load)
- Walk: 0.25

Estos son valores heurísticos iniciales y serán calibrados con datos reales; siempre etiquetar como Estimado.

**Reglas**
- Siempre etiquetar como Estimado.
- Si falta duración confiable → excluir y marcar “Datos insuficientes”.

---

## 2) Load / Training Load (agregados)

### 2.1 Load (Daily)
**UI term:** Load (se mantiene en inglés)  
**Qué es:** Carga diaria agregada (principalmente desde TRIMP).

**Inputs**
- Σ TRIMP por día (real + estimado, con flags)

**Cálculo (v1)**
- `Load_day = sum(TRIMP_sessions_day)`
- Exponer además:
  - `Load_day_real`
  - `Load_day_estimated`

---

### 2.2 Training Load (Fitness / Fatigue / Form) — Trends
**UI term:** Training Load (se mantiene en inglés)  
**Qué es:** Modelo de carga crónica y aguda + balance.

**Inputs**
- Serie diaria `Load_day`

**Cálculo (v1)**
- `Fitness` = EMA de 42 días
- `Fatigue` = EMA de 7 días
- `Form` = Fitness - Fatigue

El EMA se calcula como:

- `EMA_today = EMA_yesterday + k * (Load_today - EMA_yesterday)`
- `k = 2 / (N + 1)`

donde N es la ventana (42 para Fitness, 7 para Fatigue).

**Notas**
- Mostrar “optimal range” como rango heurístico configurable (TBD pero descrito).

---

### 2.3 Capacity (Home Trend Card / Load domain)
**UI term:** Capacity  
**Qué es:** Métrica del dominio de carga usada para soportar el bloque Home **Load vs Capacity**. No pertenece al dominio de recovery/readiness.

**Estado**
- Phase 5.1 formaliza `Capacity` y la implementa dentro del contrato de `GET /v1/training-load`.
- `Capacity` ya puede mostrarse dentro del bloque `Load vs Capacity`.
- Sigue siendo una métrica del dominio de carga, no del dominio de recovery/readiness.

**Inputs**
- Serie diaria `Load_day`
- Modelo existente de Training Load (`Fitness` / `Fatigue` / `Form`)

**Cálculo (Phase 5.1 / v1)**
- `Capacity_day = Fitness_day`
- `Fitness_day = CTL = EMA 42d de Load_day`

Esto significa:
- `Capacity` se apoya principalmente en la base crónica de carga del atleta.
- `Capacity` no usa recovery diario ni señales del dominio `daily_recovery`.
- No se crea un motor paralelo; se deriva sobre la misma serie diaria de carga ya existente.

**Interpretación semántica del card**
- El card `Load vs Capacity` no interpreta el último `Load_day` aislado.
- `semantic_state` se deriva de **carga aguda suavizada vs capacidad**, es decir:
  - `Fatigue_day = ATL = EMA 7d de Load_day`
  - comparación = `ATL / CTL`

Estados semánticos v1:
- `Below capacity` si `ATL / CTL < 0.85`
- `Within range` si `0.85 <= ATL / CTL <= 1.0`
- `Near limit` si `1.0 < ATL / CTL <= 1.15`
- `Above capacity` si `ATL / CTL > 1.15`

Guardrail:
- estos umbrales viven centralizados en backend para recalibración futura sin reescribir el flujo del card.

**History / completeness states**
- `available` = 42+ días de cobertura calendario útil
- `partial` = 14–41 días de cobertura calendario útil
- `insufficient_history` = 1–13 días de cobertura calendario útil
- `missing` = 0 días

Regla de cobertura útil:
- se mide desde la primera fecha útil del dominio `daily_load` hasta `today_local`
- usa cobertura calendario, no solo conteo de días con workouts
- días reales de descanso dentro de una historia ya iniciada no degradan artificialmente el estado a `missing` o `insufficient_history`

Regla de UI:
- `semantic_state` puede mostrarse en `available` y `partial`
- en `partial`, la UI debe indicar explícitamente que la señal aún se está consolidando
- en `insufficient_history` o `missing`, no forzar una lectura semántica falsa del dominio de carga

Fallback local cache legacy (implementado en iOS Phase 5.1):
- si filas antiguas de cache no traen `history_status`, derivarlo desde la cobertura real de la historia cacheada de `Load/TRIMP`
- si filas antiguas de cache no traen `capacity`, reconstruir `Capacity` desde la misma historia real de `Load/TRIMP` usando la base `CTL = EMA 42d`
- no usar `0` como sustituto visual de `Capacity` cuando la historia real sí soporta reconstrucción
- si no existe historia real cacheada, el estado sigue siendo `missing`

**Guardrails**
- `Capacity` debe derivarse del dominio de carga, no del dominio de `daily_recovery`.
- No reutilizar `Readiness`/`Recovery` como sustituto de `Capacity`.
- `Capacity` pertenece al dominio de carga aunque el hero de Home sea `Readiness`.
- `Load vs Capacity` sigue siendo un bloque comparativo de carga, no un score aislado.

---

## 3) Exertion (Home ring)

**UI term:** Exertion  
**Qué es:** Carga reciente (rolling) para entender cuánta carga acumulaste.

**Inputs**
- Load_day serie

**Cálculo (v1)**
- Rolling 7d y 28d:
  - `Exertion_7d = sum(Load_day last 7)`
  - `Exertion_28d = sum(Load_day last 28)`
- Opcionalmente, un badge normalizado que representa el percentil respecto a los últimos 60 días (v1.1, no implementado en v1).

**Data completeness**
- Depende de cuántos días tengan datos.

---

## 4) Readiness / Recovery (transparente)

Nota de alcance:
- Las definiciones de score de esta sección siguen siendo referencia de producto futura.
- Phase 4.5 no implementa todavía este score final.

### 4.1 Readiness (Score + drivers)
**UI term:** Readiness  
**Alias histórico/documental controlado:** Battery  
**Qué es:** Preparación para entrenar hoy, explicada por drivers.

**Drivers v1**
- Sleep
- HRV
- RHR
- Exertion/Load (fatiga acumulada)
- Movement (no-workout movement)

**Inputs**
- Sueño (duración/calidad) si existe
- HRV (SDNN)
- RHR
- Exertion_7d (o Fatigue)
- Steps + walking distance

Nota Phase 4.5:
- la capa `daily_recovery` no implementa todavía este score
- condición mínima de emisión:
  - `daily_sleep_summary` o HRV o RHR
- `complete`:
  - requiere sleep + HRV + RHR
- `partial`:
  - row emitida con al menos uno de esos inputs, pero no todos
- `missing`:
  - no se emite row derivada

**Cálculo (v1 — estructura)**
- Score 0–100 con combinación ponderada de drivers:
  - Sleep 30%
  - HRV 25%
  - RHR 15%
  - Fatigue/Exertion 20%
  - Movement 10%
- Cada driver aporta:
  - valor actual
  - baseline = rolling 28 días
  - short-term = rolling 7 días (para comparar)
  - delta y contribución al score

**Nota v1 scoring:** Score 0–100 es combinación ponderada de subscores derivados del delta vs baseline; siempre mostrar drivers y completitud de datos.

**Data completeness**
- Mostrar `drivers_present / drivers_total`
- Si faltan drivers críticos → degradar o “Datos insuficientes”

---

## 5) Sleep (Home ring + driver)

**UI term:** Sleep  
**Qué es:** Indicadores de sueño usados para Readiness y trends.

**Inputs**
- `daily_sleep_summary` derivado de `sleep_sessions`
- prioridad v1 foundation:
  - duración total
  - sesión principal
  - naps
  - correcta asignación por `local_date`
- `asleep` vs `in_bed` y sleep stages solo si la señal es consistente

Definiciones operativas Phase 4.5:
- `main_sleep`:
  - episodio más largo del día
  - `>= 3h`
  - `end_at_local` entre `03:00` y `15:00`
  - fusionando bloques con gap `<= 30 min`
- tie-breaker:
  - si hay empate, gana el `end_at` más tardío
- fallback:
  - si no existe candidato `>= 3h`, usar el episodio más largo `>= 90 min` y degradar a `partial`
- `nap`:
  - no-main sleep
  - `>= 20 min` y `< 180 min`
  - `start_at_local` entre `09:00` y `21:00`
- si no hay stages:
  - no bloquea el dominio
- si hay múltiples bloques nocturnos:
  - fusionar gaps cortos antes de elegir el `main_sleep`

**Cálculo (v1)**
- SleepDurationHours (principal)
- Consistency (opcional)
- SleepScore (TBD) — si no hay suficiente data, mostrar solo duración.

---

## 6) Stress (proxy) — Home card

**UI term:** Stress (proxy)  
**Qué es:** Estimación cuando no existe señal real.

**Inputs mínimos (v1)**
- HRV + RHR + Sleep (ideal)
- + Load/Fatigue como contexto

**Cálculo (v1)**
- StressProxyScore 0–100 combina:
  - Delta HRV vs baseline (menor HRV aumenta stress)
  - Delta RHR vs baseline (mayor RHR aumenta stress)
  - Delta duración de sueño vs baseline (menor sueño aumenta stress)
  - Contexto Fatigue (mayor fatiga aumenta stress)
- Es un proxy transparente, etiquetado como `Stress (proxy)`, y se oculta o muestra “Datos insuficientes” si faltan inputs.

---

## 7) Movement (Home ring)

**UI term:** Movement  
**Qué es:** Movimiento fuera de entrenamientos.

**Inputs**
- `daily_activity`
- Steps
- Walking Distance
- Active Energy (solo detalle)

Semántica Phase 4.5:
- `daily_activity` representa el agregado diario canónico Apple Health del movimiento del día
- no intenta aislar algorítmicamente “solo no-workout movement”
- no sustituye workouts ni load
- la consolidación anti-doble-conteo se delega a HealthKit

**Cálculo (v1)**
- Ring progress basado en Steps + Distance (definir target)
- Completeness si falta uno de los dos

---

## 8) Strength (secondary load narrative)

**UI term:** Strength  
**Qué es:** Seguimiento de fuerza sin distorsionar endurance load.

**Inputs**
- Minutos/semana (workouts strength)
- Opcional: HR si existe

**Cálculo (v1)**
- StrengthMinutesWeek
- `SecondaryStrengthLoad = strength_minutes_day * 0.35` (heurístico)
- NO se suma 1:1 a TRIMP/Exertion; puede aparecer como driver en Readiness con contribución explícita.

---

## 9) Body (peso y medidas)

### 9.1 Weight
**UI term:** Weight  
**Inputs**
- `body_measurements.weight_kg` como mínimo útil
- HealthKit bodyMass o manual en fase posterior

**Cálculo**
- Promedios móviles simples (SMA) 7d y 28d para mostrar, y permitir seleccionar ventanas 30/90/365 para rango de gráfico.
- Dedup por fecha

**Regla Phase 4.5**
- `body_measurements` se mantiene pragmático.
- composición corporal solo se usa si llega limpia y confiable desde HealthKit.
- para múltiples mediciones válidas el mismo día, gana la última medición válida por métrica.
- no se emite row diaria útil del dominio si no existe `weight_kg` válido.

---

## 10) Pendientes para v0.2 (cuando tengamos datos)
- Calibrar factores de TRIMP estimado con datos reales.
- Definir/ajustar “optimal range” para Training Load.
- Recalibrar umbrales heurísticos de `Load vs Capacity` con datos reales.
- Definir objetivos (targets) del ring Movement.
- Refinar Readiness weights/baselines con evidencia y feedback.
- Refinar Stress proxy thresholds.
