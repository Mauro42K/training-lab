# Phase 4.5 — Daily Domains & Summary Contracts (Apple-first)

**Status:** OPENING / ACTIVE DOCUMENTATION  
**Date:** 2026-03-11 (America/Mexico_City)

## 1) Contexto

Phase 4.0-4.3 cerraron la base operativa actual:
- ingest real desde HealthKit para workouts,
- persistencia PostgreSQL,
- recompute determinista por fechas afectadas para carga,
- contratos explícitos para `workouts`, `daily` y `training-load`,
- separación operacional `production | staging`.

Después del análisis estratégico y técnico comparando `Training Lab` con `open-wearables`, la decisión queda cerrada:
- **no** convertir `Training Lab` en una plataforma genérica multi-provider,
- **no** adoptar `open-wearables` como base arquitectónica,
- **sí** abrir una nueva fase Apple-first para dominios diarios y contratos explícitos.

Phase 4.4 queda **on hold**. Puede reutilizarse más adelante el patrón de recompute por fechas afectadas, pero su scope de reconciliación histórica y cleanup de workouts no forma parte de Phase 4.5.

## 2) Objetivo

Construir la base mínima, clara y escalable para dominios diarios Apple-first que desbloqueen Home y Trends, manteniendo el patrón:

`normalized -> derived -> query`

Phase 4.5 debe congelar semántica, naming, guardrails y reglas transversales antes de tocar implementación. El foco no es una UI final ni un score final, sino contratos diarios explícitos y trazables.

## 3) Alcance

Dominios en scope:
- `sleep_sessions`
- `daily_sleep_summary`
- `daily_recovery`
- `daily_activity`
- `body_measurements`

Cobertura Apple-first mínima esperada para esta fase:
- sueño,
- HRV,
- RHR,
- pasos,
- walking/running distance,
- active energy opcional,
- peso,
- composición corporal solo si llega limpia y confiable desde HealthKit.

Resultados esperados de Phase 4.5:
- naming estable por dominio,
- reglas transversales explícitas,
- modelo por capas documentado,
- contratos conceptuales por dominio,
- guardrails anti-scope-creep,
- base documental para que Home y Trends consuman derivados claros sin reabrir semántica.

## 4) No-objetivos

Phase 4.5 **no incluye**:
- readiness final,
- battery final,
- baselines 7d/28d,
- scoring,
- explicabilidad premium,
- endpoint genérico `/timeseries`,
- arquitectura multi-provider,
- Redis, Celery, OAuth, webhooks o portal web,
- persistencia de blobs raw completos,
- reconciliación histórica y cleanup de workouts de Phase 4.4,
- expansión de `GET /v1/daily` para cubrir estos dominios.

## 5) Decisiones Cerradas

### 5.1 Naming obligatorio
- capa normalizada de sueño: `sleep_sessions`
- capa derivada diaria de sueño: `daily_sleep_summary`

No usar `daily_sleep` como nombre de tabla/contrato derivado diario en esta fase.

### 5.2 Daily recovery
- `daily_recovery` es una **capa de inputs consolidados**.
- No incluye score final `0-100`.
- Debe considerar ingest mínima Apple-first para:
  - HRV,
  - RHR,
  - `daily_sleep_summary`,
  - contexto de `daily_activity`,
  - contexto de carga existente cuando aplique.

### 5.3 Home summary
- `GET /v1/home/summary` podrá existir en una fase de implementación posterior.
- Si se introduce, deberá componerse **exclusivamente** desde contratos/tablas derivadas ya definidos en Phase 4.5.
- No debe introducir semántica nueva ni reglas paralelas.

### 5.4 Body measurements
- `body_measurements` se mantiene pragmático.
- `weight_kg` es la métrica mínima obligatoria.
- composición corporal solo si llega limpia y confiable desde HealthKit.
- No generalizar ni sobrediseñar el dominio en esta fase.

### 5.5 Sleep
- `daily_sleep_summary` no debe quedar bloqueado por sleep stages inconsistentes o ausentes.
- La prioridad inicial es:
  - duración total,
  - sesión principal,
  - naps,
  - asignación correcta por día.

### 5.6 Provenance mínima

Phase 4.5 congela el set mínimo obligatorio de provenance:
- `provider`
- `source_count`
- `has_mixed_sources`
- `primary_device_name`

No agregar más campos de lineage en esta fase salvo necesidad muy clara.

## 6) Reglas Transversales

Aplican a todos los dominios diarios de Phase 4.5:

- `local_date` es obligatoria en todos los derivados diarios.
- Timezone IANA explícita; backend resuelve `local_date`.
- Recompute por fechas afectadas.
- Idempotencia en ingest y recompute.
- `null != 0`.
- `measured != estimated`.
- Provenance mínima obligatoria.
- No introducir silent fallbacks semánticos entre dominios.

Implicaciones:
- ausencia de una métrica se representa como `null`, no como `0`,
- un valor estimado debe etiquetarse explícitamente,
- cambios que muevan una observación de un día a otro deben forzar recompute de todas las fechas afectadas.

### 6.1 Timezone autoritativa

- La timezone autoritativa de Phase 4.5 es la timezone IANA enviada por iOS en cada sync/ingest de dominios HealthKit.
- Backend usa esa timezone para derivar `local_date` de los registros afectados por ese request.
- Backend actualiza además la timezone persistida del usuario como default operativo actual.
- Fallback permitido:
  - `users.timezone` persistida si el request no trae timezone válida,
  - timezone fallback del backend solo como última defensa.

### 6.2 `local_date` por dominio

- workouts:
  - `local_date = date(start_at en timezone autoritativa)`
- `sleep_sessions`:
  - asignación operativa por `end_at` local
- `daily_sleep_summary`:
  - `local_date = día de despertar del main sleep`
- `daily_activity`:
  - `local_date = day bucket calendario de HealthKit en timezone autoritativa`
- `body_measurements`:
  - `local_date = date(measured_at en timezone autoritativa)`
- `daily_recovery`:
  - `local_date = día consolidado que combina inputs fisiológicos y contexto del mismo día`

### 6.3 Missing vs row emitida

- `missing` significa: no existe row derivada emitida para ese día.
- Phase 4.5 no usa rows vacías con `nulls` para representar `missing`.
- `partial` significa:
  - la row sí existe,
  - pero uno o más inputs requeridos/objetivo faltan o son ambiguos.

### 6.4 Provenance mínima

Campos mínimos congelados:
- `provider`
- `source_count`
- `has_mixed_sources`
- `primary_device_name`

Regla para `primary_device_name`:
- si puede determinarse con confianza, se llena,
- si no puede determinarse con confianza, queda `null`,
- no introducir heurísticas complejas de resolución en Phase 4.5.

### 6.5 `measured` vs `estimated`

- `measured`:
  - valor observado o agregado directamente desde HealthKit con semántica confiable para ese dominio
- `estimated`:
  - valor derivado por fallback/modelo cuando no existe medición suficiente

Guardrail de Phase 4.5:
- `sleep`, `daily_activity` y `body_measurements` se mantienen `measured` en esta fase.
- `daily_recovery` consolida inputs mayoritariamente `measured`; si arrastra contexto estimado upstream, debe marcarlo explícitamente en ese input.

## 7) Modelo por Capas

### 7.1 Normalized

Almacenamiento canónico Apple-first por tipo de dato.

Ejemplos esperados:
- `sleep_sessions`
- inputs fisiológicos normalizados para HRV/RHR
- inputs/agregados de actividad diaria
- `body_measurements`

La capa normalizada existe para conservar identidad estable, timestamps relevantes, provenance mínima y datos necesarios para recompute, sin derivar semántica de producto final en esta fase.

### 7.2 Derived

Resúmenes diarios con reglas explícitas y recompute por fechas afectadas.

Ejemplos esperados:
- `daily_sleep_summary`
- `daily_activity`
- `daily_recovery`

La capa derivada es la fuente de verdad diaria para Home y Trends.

### 7.3 Query

Contratos explícitos por dominio.

Reglas:
- sin generic timeseries,
- sin multiplexar tipos heterogéneos en un endpoint genérico,
- Home summary solo compone derivados ya existentes.

## 8) Contratos por Dominio

### 8.1 `sleep_sessions`

Dominio normalizado Apple-first de sesiones de sueño.

Debe incluir, como mínimo:
- identidad estable,
- ventana temporal,
- tipo básico de sesión cuando exista,
- provenance mínima,
- datos suficientes para recompute y asignación por día.

No requiere resolver stages de forma completa para que la fase avance.

### 8.2 `daily_sleep_summary`

Contrato derivado diario de sueño.

Debe priorizar:
- duración total,
- sesión principal,
- naps,
- asignación correcta por `local_date`.

Los sleep stages son opcionales y no bloqueantes en Phase 4.5.

Definiciones operativas:
- `main_sleep`:
  - episodio de sueño más largo del día,
  - duración `>= 3h`,
  - `end_at_local` entre `03:00` y `15:00`,
  - tras fusionar bloques adyacentes con gap `<= 30 min`
- tie-breaker:
  - si hay empate, gana el episodio con `end_at` más tardío
- fallback:
  - si no existe candidato `>= 3h`, usar el episodio más largo `>= 90 min` en la misma ventana y degradar a `partial`
- `nap`:
  - sesión no elegida como `main_sleep`,
  - duración `>= 20 min` y `< 180 min`,
  - `start_at_local` entre `09:00` y `21:00`
- si no hay stages:
  - no bloquea el dominio,
  - se usa solo ventana temporal y duración
- si hay múltiples bloques nocturnos:
  - primero fusionar gaps cortos,
  - luego elegir un único `main_sleep`,
  - los bloques diurnos que califiquen cuentan como `nap`

### 8.3 `daily_activity`

Contrato derivado diario de movimiento no-workout.

Debe cubrir, al menos:
- `steps`,
- `walking_running_distance_m`,
- `active_energy_kcal` opcional,
- completeness,
- provenance mínima.

`daily_activity`:
- es contexto de movimiento diario,
- no sustituye workouts,
- no reemplaza el dominio de carga,
- no reemplaza TRIMP.

Semántica operativa:
- representa el agregado diario Apple Health del movimiento del día calendario,
- no intenta aislar “solo no-workout movement” de forma algorítmica en Phase 4.5,
- no se usa para recalcular carga ni para sustituir sesiones de workout.

Política de agregación:
- una row derivada por `local_date`,
- basada en agregados diarios canónicos de HealthKit.

Política anti-doble-conteo:
- delegar deduplicación y consolidación a los agregados canónicos de HealthKit,
- no sumar manualmente Watch + iPhone para construir este dominio.

### 8.4 `body_measurements`

Dominio pragmático de medidas corporales.

Reglas:
- `weight_kg` es obligatorio para la salida mínima útil,
- body composition solo si la señal llega limpia,
- sin generalización prematura,
- sin obligar cobertura amplia de biometría en esta fase.

Canonicalización diaria:
- para múltiples mediciones válidas el mismo día, gana la última medición válida por métrica
- `weight_kg` manda la emisión útil del dominio diario
- si no existe `weight_kg` válido en el `local_date`, no se emite row diaria útil del dominio
- body composition incompleta:
  - si llega limpia el mismo día, se adjunta
  - si no llega o es ambigua, queda `null`
  - no bloquea la emisión si `weight_kg` sí existe

### 8.5 `daily_recovery`

Contrato derivado diario de inputs consolidados.

Inputs esperados:
- `daily_sleep_summary`,
- HRV,
- RHR,
- contexto de `daily_activity`,
- contexto de carga existente cuando aplique.

Debe exponer:
- inputs presentes,
- inputs faltantes,
- completeness,
- flags `measured/estimated`,
- provenance mínima.

No debe exponer score final `0-100` en Phase 4.5.

Reglas operativas:
- condición mínima de emisión:
  - se emite `daily_recovery` solo si existe al menos uno de estos inputs fisiológicos en el `local_date`:
    - `daily_sleep_summary`
    - HRV
    - RHR
- estado `complete`:
  - requiere `sleep + HRV + RHR`
- estado `partial`:
  - existe row confiable, pero falta uno o más de esos inputs
- estado `missing`:
  - no se emite row derivada para ese día
- `daily_activity` y contexto de carga:
  - enriquecen el dominio,
  - no bastan por sí solos para emitir `daily_recovery`

## 9) Guardrails Anti-Scope-Creep

- No introducir semántica final de producto antes de estabilizar contratos diarios.
- No mezclar foundation data contracts con explicabilidad premium.
- No resolver analytics futuros en esta fase.
- No convertir Home summary en un dominio nuevo con reglas propias.
- No absorber reconciliación histórica de workouts.
- No abrir abstracciones para providers no existentes.
- No usar `GET /v1/daily` como shortcut para resolver esta fase.
- No introducir infraestructura async extra solo para anticipar escalamiento futuro.

## 10) QA Esperado

La apertura de fase congela la matriz mínima esperada para QA posterior.

### 10.1 Sueño
- sesión overnight cruzando medianoche,
- naps el mismo día,
- ausencia de stages,
- correcta asignación por `local_date`.

### 10.2 Recovery
- HRV faltante,
- RHR faltante,
- sueño faltante,
- completeness correcta sin score final.
- no emitir row cuando falten todos los inputs fisiológicos base.

### 10.3 Activity
- día con solo pasos,
- día con distance pero no steps,
- active energy ausente,
- `null != 0`.

### 10.4 Body
- peso presente,
- composición corporal ausente,
- múltiples mediciones válidas el mismo día,
- provenance mínima siempre presente.
- `primary_device_name = null` si no puede resolverse con confianza.

### 10.5 Transversales
- cambio de timezone/local_date,
- recompute por fechas afectadas,
- `measured != estimated`,
- idempotencia en replay.

La validación real en staging y en iPhone físico se define como parte de la implementación posterior, no de esta apertura documental.

## 11) Dependencias y Riesgos

Dependencias principales:
- definición explícita de timezone autoritativa,
- estrategia Apple-first para ingest de HRV/RHR/activity,
- decisión pragmática de canonicalización diaria para body measurements.

Riesgos principales:
- convertir `daily_recovery` en score antes de tiempo,
- contaminar Phase 4.5 con Phase 4.4,
- sobre-modelar `body_measurements`,
- introducir semántica nueva en un futuro `home/summary`,
- usar `GET /v1/daily` como atajo impropio.

## 12) Relación con Phase 4.4 On Hold

Phase 4.4 queda formalmente pausada:
- status operativo: **on hold**
- no forma parte del alcance de Phase 4.5
- no debe mezclarse con los contratos diarios Apple-first

Phase 4.5 puede reutilizar más adelante el patrón de recompute por fechas afectadas, pero no toma como sub-scope:
- reconciliation histórica,
- deleted workout cleanup,
- duplicate cleanup histórico.

Toda referencia a Phase 4.4 durante la implementación de 4.5 debe tratarse como dependencia pausada, no como trabajo concurrente.

## 13) Huecos Pendientes de Definición

Estos huecos no bloquean la apertura documental, pero deben cerrarse antes o durante la implementación:

- Ingest Apple-first de HRV/RHR:
  - falta decidir si la capa normalizada guardará observaciones puntuales o valores diarios consolidados.
- `daily_activity`:
  - falta congelar si la normalización será diaria desde origen o si existirá granularidad subdiaria previa.
- `body_measurements`:
  - falta decidir si el dominio usa row derivada separada o si se mantiene como canonicalización diaria sobre el normalizado.
- `GET /v1/home/summary`:
  - queda definido como composición futura habilitada por 4.5, no como entregable inicial de esta apertura.
