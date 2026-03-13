

# Training Lab — Glosario (v0.1)

Este glosario define los **términos oficiales de UI** y su **significado**.

## 1) Regla de lenguaje (ES + términos técnicos EN)

- La app soporta **Español e Inglés**, pero en español permitimos **términos técnicos en inglés** cuando:
  - la traducción es ambigua (ej. “carga”), o
  - el término se usa comúnmente en entrenamiento (ej. HRV, TRIMP, Zone 2).
- En UI en español:
  - **Mostramos el término EN** y una **micro-definición** breve en español.
  - En pantallas de detalle se incluye “Cómo se calcula” y link a `docs/METRICS_CATALOG.md`.

## 2) Términos oficiales (v0.1)

Regla congelada para Home v1:
- **Readiness** es el término rector del hero principal de Home.
- **Battery** se conserva solo como alias histórico/documental controlado para referencias previas a Phase 5.0.

> Nota: “Etiqueta ES” es opcional; si no aporta claridad, el término se deja en inglés.

| Término (UI EN) | Etiqueta ES sugerida | Definición corta (ES) | Notas |
|---|---|---|---|
| **TRIMP** | TRIMP | Carga interna del entrenamiento basada en intensidad/duración (HR o estimación). | Foco MVP. |
| **Load** | Load | Medida agregada de carga (no solo volumen). | Evitar “Carga” por ambigüedad. |
| **Training Load** | Training Load | Evolución de Load en el tiempo (ej. Fitness/Fatigue/Form). | Se usa en Trends. |
| **Exertion** | Esfuerzo | Cuánta carga acumulaste recientemente (basada en TRIMP/Load). | Debe ser transparente. |
| **Recovery** | Recuperación | Estado de recuperación usado como parte del estado de Readiness. | No es médico. |
| **Battery** | Battery | Alias histórico/documental del score de preparación. | No es el término rector de Home nuevo. |
| **Readiness** | Readiness | Preparación para entrenar hoy con drivers y completitud visibles. | Término rector del hero principal de Home. |
| **Sleep** | Sueño | Métricas de sueño (duración/calidad) desde HealthKit. | Driver del Readiness. |
| **Stress** | Stress | Estrés (si no hay señal real: **Stress (proxy)**). | Siempre indicar proxy. |
| **Stress (proxy)** | Stress (proxy) | Estimación basada en drivers (HRV/RHR/Sleep/Load) cuando falte señal real. | No presentarlo como “real”. |
| **HRV** | HRV | Heart Rate Variability (SDNN) desde HealthKit. | Driver clave. |
| **RHR** | RHR | Resting Heart Rate desde HealthKit. | Driver clave. |
| **Movement** | Movimiento | Actividad fuera de entrenos (steps + walking distance). | Energía activa en detalle. |
| **Steps** | Pasos | Conteo de pasos diario. | Parte de Movement. |
| **Walking Distance** | Distancia caminada | Distancia caminando/corriendo diaria. | Parte de Movement. |
| **Active Energy** | Energía activa | Calorías activas. | No es el driver principal del ring en v1. |
| **Zones** | Zonas | Zonas de intensidad (HR/pace). | Ej. Zone 2, Zone 3… |
| **Zone 2** | Zone 2 | Zona aeróbica baja (base). | Mantener en EN por uso común. |
| **Fitness / Fatigue / Form** | Fitness / Fatigue / Form | Componentes del modelo de Training Load. | Se define en métricas. |
| **Base Training** | Base Training | Rango de entrenamiento base (restorative/optimal/overreaching). | En Trends. |
| **Overreaching** | Overreaching | Exceso de carga relativo (riesgo). | UI debe ser cuidadosa. |
| **Optimal Training Range** | Optimal Range | Rango objetivo de carga. | Puede acortarse. |
| **Body** | Body | Peso y medidas corporales. | Pestaña dedicada. |
| **Weight** | Peso | Peso corporal. | HealthKit o manual. |
| **Body Fat %** | % Grasa | Porcentaje de grasa corporal (si existe). | Opcional. |
| **Lean Mass** | Masa magra | Masa magra (si existe). | Opcional. |

## 3) Convenciones de micro-definición (UI)

- Cada ring/card/score debe incluir:
  1) **Qué es** (1 línea)
  2) **Cómo se calcula** (1 línea, alto nivel)
  3) Link/acción: **“Ver cálculo”** → referencia a `docs/METRICS_CATALOG.md`

## 4) Cambios

- v0.1: Base inicial del glosario. Ajustar términos a medida que se definan modelos en `docs/METRICS_CATALOG.md`.
