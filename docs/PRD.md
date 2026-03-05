# Training Lab — PRD (v0.1)

**Proyecto:** Training Lab  
**Repositorio:** `training-lab`  
**Plataformas:** iPhone + Mac (SwiftUI, código único)  
**Fuente de datos oficial:** Apple Fitness / Apple Health (HealthKit)  
**Enfoque principal:** Enfocado en correr, con soporte multi-deporte (Bicicleta/Fuerza/Caminar soportados)  
**Estrella del Norte:** Organizar y conectar el contexto de entrenamiento + salud en un dashboard premium → Analíticas tipo Athlytic → Coach AI (tipo Runna)

---

## 1) Declaración del Problema

Apple Fitness/Health contiene los datos, pero están fragmentados:
- La carga de entrenamiento vs contexto de recuperación no está conectado (sueño/HRV/RHR/pasos/peso/métricas corporales).
- Las tendencias clave se pierden.
- No existe una vista de “momento de la verdad” (antes/después del entrenamiento) que explique la preparación y la carga juntas.

Training Lab proveerá una experiencia coherente, premium y al estilo Apple que:
- Hace visible la carga de entrenamiento desde el día 1 (**TRIMP hero chart**).
- Explica la preparación de forma transparente (**Battery** con drivers + completitud de datos).
- Mantiene la carrera como la narrativa principal, respetando fuerza/bici/caminar.

---

## 2) Usuario Objetivo y Casos de Uso

### Usuario primario
- Mauricio (corredor serio), también entrena fuerza y bicicleta.
- Quiere claridad rápida antes del entrenamiento y confirmación/aprendizaje después del entrenamiento.

### Momentos clave
1) **Pre-entrenamiento (momento de la verdad #1)**  
   “¿Cómo estoy hoy?” (Battery/Recuperación + drivers) y “¿qué debería hacer?”
2) **Post-entrenamiento (momento de la verdad #2)**  
   “¿Qué hice y qué significa?” (Impacto TRIMP + tendencia)

### Casos de uso principales (v1)
- Ver tendencia TRIMP inmediatamente (28d) con filtros por deporte.
- Entender la preparación (Battery) y por qué cambió (Sueño/HRV/RHR/Esfuerzo/Movimiento).
- Profundizar en detalle tocando anillos/tarjetas.
- Seguir tendencias de peso + medidas corporales (pestaña Body).

---

## 3) Arquitectura de Información (Tabs v0.2)

1) **Home**  
Dashboard diario enfocado en el momento previo al entrenamiento.  
Presenta recuperación, recomendación del día y contexto de carga.

2) **Trends**  
Analíticas a largo plazo de carga, fitness, fatiga y forma.  
Incluye visualizaciones tipo CTL / ATL / TSB y tendencias fisiológicas.

3) **Workouts**  
Historial completo de entrenamientos.  
Lista de sesiones, tarjetas resumen y pantalla de detalle del entrenamiento.

4) **Calendar**  
Vista mensual del entrenamiento para evaluar consistencia y distribución de carga.  
Permite navegar días y acceder rápidamente a sesiones pasadas.

5) **Body**  
Tendencias de peso y métricas corporales.  
Incluye integración con Apple Health y potencial integración futura con Speediance.

6) **More**  
Configuración, permisos HealthKit, idioma, calibración, privacidad y perfil del atleta.

7) **Coach (futuro)**  
Recomendaciones adaptativas, planificación de entrenamiento y chat con AI.


---

## 3.1) Localización (i18n)

- App soporta Español e Inglés.  
- Idioma por defecto: “Sistema”.  
- En **More → Settings → Language** se puede forzar idioma.  
- Regla: no hardcodear strings; usar String Catalog / Localizable.  
- Nota UX: diseñar para textos más largos (truncation, dynamic type).

---

## 3.2) Lenguaje, términos técnicos y glosario

- En la UI en español se permiten términos técnicos de entrenamiento en inglés cuando la traducción es ambigua o el término en inglés es estándar en la industria.  
- Los términos **Load** y **Training Load** permanecerán en inglés en la UI en español.  
- Cada métrica debe incluir micro-definición y link de cálculo, siguiendo la regla de transparencia y consistencia establecida en la sección de localización.  
- Para términos de UI, la fuente única de verdad es `docs/GLOSARIO.md`.

---

## 4) Especificación Pantalla Home (v0.3)

La pantalla **Home** representa el *momento previo al entrenamiento*.

Objetivo: permitir al atleta entender su estado actual en menos de **30 segundos**.

Home debe sentirse como un **panel de inteligencia del atleta**, no un dashboard complejo.

### Orden de layout (de arriba hacia abajo)

**A) TARJETA HERO: RECOVERY / READINESS**

Métrica principal del día que resume el estado fisiológico actual.

Elementos:
- Score de recuperación (0–100)
- Estado textual (Ready / Moderate / Recover)
- Contexto visual minimalista

Drivers posibles:
- HRV
- RHR
- Sueño
- Fatiga reciente
- Carga de entrenamiento reciente

La tarjeta debe ser visualmente dominante y fácil de interpretar en segundos.

---

**B) RECOMMENDED TODAY**

Recomendación simple de entrenamiento basada en el estado actual del atleta.

Ejemplo:

Z2 Endurance Run  
45 min

Objetivo:
Convertir la app en un **entrenador contextual**, no solo un dashboard de datos.

La recomendación debe ser clara, breve y accionable.

---

**C) CORE METRICS**

Tres métricas compactas que explican el estado de carga actual.

- **7-Day Load** (TRIMP acumulado)
- **Fitness** (CTL)
- **Fatigue** (ATL)

Estas métricas proporcionan contexto fisiológico del entrenamiento reciente.

---

**D) TREND CARD**

Gráfico simple de tendencia de carga.

Ejemplo:

Load vs Capacity  
últimos 7 días

Objetivo:
Mostrar rápidamente si la carga está aumentando, estabilizándose o excediendo la capacidad del atleta.

---

### Principios de diseño (Home)

- Métricas numéricas dominan el diseño.
- Texto mínimo.
- No más de **4 tarjetas visibles** en la pantalla inicial.
- Interacciones simples y claras.

Home debe permitir al atleta responder rápidamente:

• ¿Cómo estoy hoy?  
• ¿Qué debería hacer hoy?  
• ¿Cómo viene mi carga reciente?


---


---

## 4.1) Especificación Pantalla Activity Detail (v0.1)

La pantalla **Activity Detail** explica qué ocurrió durante un entrenamiento específico.

Objetivo: permitir al atleta entender rápidamente **qué hizo, cómo rindió y qué tan exigente fue la sesión**.

La pantalla debe sentirse como una **herramienta de análisis de entrenamiento de nivel profesional**, manteniendo la estética premium y minimalista de la app.

La arquitectura de la pantalla es **modular y multi‑deporte**: la estructura visual se mantiene constante, mientras que las métricas y gráficos cambian según los datos disponibles.

---

### Estructura de layout (de arriba hacia abajo)

**A) ACTIVITY HEADER**

El header muestra el contexto del entrenamiento.

Elementos:

- Nombre del entrenamiento (editable)
- Hora de inicio
- Visualización superior adaptativa

Ejemplo:

Morning Threshold Run  
06:45 AM

Visualización superior:

- **Si existe GPS:** mostrar mini‑visualización de la ruta.
- **Si no existe GPS (treadmill, rowing, indoor bike):** mostrar una curva simple de esfuerzo (pace o heart rate).

Esto permite soportar actividades indoor sin mostrar mapas vacíos.

---

**B) SUMMARY METRICS**

Fila compacta con las métricas principales del entrenamiento.

Ejemplo running:

Distance  
Time  
Avg Pace  
Elevation Gain  
Avg Heart Rate

Ejemplo:

Distance      Time      Avg Pace      Elev Gain      Avg HR  
12.4 km       58:30     4:42/km       +120 m         158 bpm

Reglas:

- máximo **5 métricas**
- números grandes
- etiquetas pequeñas
- consistentes con el estilo visual de Home

Si el entrenamiento es indoor:

- reemplazar **Elevation Gain** por **Average Incline** si existe.

---

**C) PERFORMANCE CHARTS**

Bloque principal de análisis del entrenamiento.

Incluye selector de gráficos tipo tabs.

Ejemplos de tabs disponibles:

- Pace
- Heart Rate
- Elevation
- Power (cycling)
- Cadence
- Grade / Incline

Reglas:

- mostrar solo gráficos con datos disponibles
- gráficos minimalistas
- línea suave con área sutil
- interacción táctil para explorar valores

---

**D) ELEVATION PROFILE**

Si existe información de elevación, incluir gráfico de elevación.

Estilo inspirado en Apple Fitness:

- línea suave
- área sutil
- grid mínimo
- fondo oscuro

Este gráfico es clave para analizar esfuerzo en **running outdoor y cycling**.

---

**E) INTENSITY ZONES**

Distribución de intensidad del entrenamiento.

Puede basarse en:

- Heart Rate Zones
- Pace Zones
- Power Zones

Visualización:

- barra horizontal segmentada
- porcentaje de tiempo por zona
- zona predominante destacada

Ejemplo:

Z1 22%  
Z2 48%  
Z3 20%  
Z4 10%

---

**F) SPLITS / INTERVALS**

Tabla de splits o intervalos.

Ejemplo running:

KM      Pace      HR      Elev Δ  
1       4:50      142     +5  
2       4:45      145     +3  
3       4:32      158     -2

Debe incluir:

- botón **View All Splits**
- soporte para auto‑laps si existen.

Para otros deportes:

Cycling → laps  
Rowing → splits /500m  
Strength → sets / reps

---

**G) INSIGHTS**

Breve interpretación del entrenamiento.

Máximo **1–3 insights**.

Ejemplos:

- Steady pacing until minute 35.  
- Heart rate drift detected in the final third.  
- Effort concentrated in the final elevation segment.

Objetivo: transformar datos en **feedback accionable**.

---

### Principios de diseño (Activity Detail)

- Diseño consistente con Home.
- Gráficos grandes y claros.
- Texto mínimo.
- UI basada en datos disponibles (data‑driven UI).
- Misma arquitectura para **run, bike, rowing, strength y walk**.

El layout nunca cambia; solo cambian métricas y gráficos según el deporte.

---


## 4.2) Especificación Pantalla Trends (v0.1)

La pantalla **Trends** provee análisis longitudinal del entrenamiento y del estado fisiológico del atleta.

Objetivo: permitir al atleta entender rápidamente **cómo evoluciona su fitness, su fatiga y su carga de entrenamiento** en el tiempo.

Trends debe sentirse como una **herramienta analítica premium**, no como una tabla de datos.  
La información debe comunicarse principalmente a través de **gráficos grandes, claros y jerarquía visual fuerte**.

La pantalla responde tres preguntas clave:

• ¿Cómo está evolucionando mi forma física?  
• ¿Estoy entrenando demasiado o demasiado poco?  
• ¿Cómo se distribuye mi intensidad de entrenamiento?

---

### Estructura de layout (de arriba hacia abajo)

**A) TRAINING STATUS (Hero Chart)**

Gráfico principal de la pantalla.

Visualiza la relación entre carga reciente y capacidad de entrenamiento.

Modelo utilizado:

- **Fitness (CTL)** — capacidad de entrenamiento a largo plazo  
- **Fatigue (ATL)** — carga reciente de entrenamiento  
- **Form (TSB)** — balance entre fitness y fatiga

Visualización:

- Línea CTL
- Línea ATL
- Zona sombreada para TSB

Objetivo:

Permitir identificar rápidamente:

- acumulación de fatiga
- períodos de construcción de fitness
- fases de taper o recuperación

Este gráfico representa la **vista más importante de análisis del atleta**.

---

**B) FITNESS PROGRESS**

Tarjeta de métricas que resume el estado actual del modelo de carga.

Métricas:

- **Fitness (CTL)**
- **Fatigue (ATL)**
- **Form (TSB)**

Ejemplo visual:

Fitness (CTL)   52  
Fatigue (ATL)   61  
Form (TSB)      -9

Reglas visuales:

- números grandes
- texto mínimo
- color semántico para Form

Interpretación sugerida:

TSB > +10 → Fresh  
TSB -10 a +10 → Balanced  
TSB < -10 → Fatigued

---

**C) TRAINING LOAD TREND**

Gráfico de carga semanal.

Métrica principal:

- **Weekly TRIMP**

Visualización:

- gráfico de barras
- ventana típica: 8–12 semanas

Objetivo:

Mostrar la evolución del volumen de entrenamiento y detectar:

- fases de construcción
- mesetas
- reducciones de carga

---

**D) INTENSITY DISTRIBUTION**

Distribución de intensidad de entrenamiento.

Basado en:

- Heart Rate Zones
- Pace Zones (cuando sea relevante)

Visualización:

- barra horizontal segmentada
- porcentaje de tiempo por zona

Ejemplo:

Z1 22%  
Z2 48%  
Z3 20%  
Z4 10%

Objetivo:

Ayudar al atleta a evaluar si su entrenamiento sigue una distribución de intensidad adecuada.

---

**E) PERFORMANCE TRENDS**

Indicadores de rendimiento a lo largo del tiempo.

Ejemplos de métricas:

- Pace promedio
- Heart Rate promedio
- Efficiency (ritmo vs HR)

Visualización:

- mini‑gráficos de tendencia
- líneas suaves
- escala temporal consistente con el resto de la pantalla

Objetivo:

Detectar mejoras o regresiones de rendimiento.

Ejemplo de insight:

mismo HR promedio con ritmo más rápido → mejora de eficiencia.

---

### Principios de diseño (Trends)

- Gráficos dominan la pantalla.
- Texto mínimo.
- Cada bloque responde una pregunta analítica clara.
- Jerarquía visual clara: **Hero chart → métricas → tendencias → distribución**.
- La pantalla debe evitar apariencia de hoja de cálculo.

Trends debe sentirse comparable a herramientas analíticas avanzadas como:

- Athlytic
- Gentler Streak

pero manteniendo estética consistente con el ecosistema Apple.

---

### Relación con otras pantallas

Trends responde a la pregunta:

**“¿Cómo está evolucionando mi entrenamiento?”**

Mientras que:

Home → estado actual del atleta  
Workouts → detalle de sesiones  
Body → métricas fisiológicas (HRV, sueño, VO₂max, etc.)

---

## 4.3) Especificación Pantalla Body (v0.1)

La pantalla **Body** es el hub de **fisiología y biometría** del atleta.  
Aquí viven las métricas que describen **cómo está respondiendo el cuerpo** (sueño, recuperación, corazón, capacidad aeróbica y composición corporal).

Body responde a la pregunta:

**“¿Cómo está respondiendo mi cuerpo al entrenamiento?”**

Mientras que:

- **Trends** → “¿Cómo está evolucionando mi entrenamiento?” (carga/fitness/fatiga/forma)  
- **Workouts** → “¿Qué pasó en una sesión específica?”  
- **Home** → “¿Cómo estoy hoy y qué debería hacer?” (resumen diario)

---

### Principio clave (separación de dominios)

- **Trends** contiene métricas del **modelo de carga** (TRIMP/CTL/ATL/TSB).  
- **Body** contiene métricas **fisiológicas** (Sleep/HRV/RHR/VO₂max/Weight).

No mezclar dominios en v0.1 para mantener claridad mental y consistencia de producto.

---

### Estructura de layout (de arriba hacia abajo)

**A) RECOVERY SNAPSHOT (Hero Card)**

Tarjeta principal que resume el estado fisiológico reciente con 2–4 indicadores.

Elementos sugeridos:

- **HRV (7d avg)** + tendencia (↑/→/↓)
- **RHR (7d avg)** + tendencia (↑/→/↓)
- **Sleep (last night)** (duración + score si existe)
- Estado textual breve (ej. “Stable”, “Improving”, “Stressed”) con explicación transparente

Reglas:

- números grandes
- texto mínimo
- mostrar badge de “Datos incompletos” si faltan fuentes para algún indicador

---

**B) SLEEP**

Bloque dedicado a sueño.

Contenido:

- Total sleep (última noche)
- 7d / 28d trend (línea suave)
- Consistencia (ej. hora de dormir / variabilidad) si existe

Visualización:

- gráfico principal de tendencia (mínimo grid)
- tarjetas compactas para “Last night” y “7d avg”

---

**C) RECOVERY (HRV / RHR)**

Bloque de recuperación centrado en corazón.

Contenido:

- HRV (RMSSD o métrica disponible en Apple Health) con tendencia 7d/28d
- Resting HR con tendencia 7d/28d

Visualización:

- dos mini‑gráficos (sparklines) + valor actual
- opción de alternar rango temporal (28d / 90d / 1y) (solo UI, sin interacción avanzada requerida aún)

Reglas:

- destacar cambios relevantes con flechas discretas
- evitar alarmismo; preferir lenguaje neutral

---

**D) CARDIORESPIRATORY (VO₂max)**

Bloque dedicado a capacidad aeróbica.

Contenido:

- VO₂max actual (último valor)
- tendencia 90d / 1y (línea suave)
- fecha del último update

Reglas:

- si no existe VO₂max, mostrar “No disponible” + guía breve de cómo se obtiene (transparente, no intrusivo)

---

**E) BODY COMPOSITION (Weight y opcionales)**

Bloque de composición corporal.

Contenido mínimo v0.1:

- Weight (actual)
- tendencia 28d / 90d

Opcional si existe en HealthKit:

- Body Fat %
- Lean Body Mass

Reglas:

- el usuario puede ocultar esta sección si no quiere trackear peso (futuro)
- mostrar claramente la fuente: Apple Health / manual

---

**F) DATA QUALITY / COMPLETITUD (Footer Card)**

Tarjeta breve de completitud de datos para evitar “caja negra”.

Ejemplo:

- Sleep: ✅
- HRV: ✅
- RHR: ✅
- VO₂max: ⚠️ (no disponible)
- Weight: ✅

Objetivo:

- aumentar confianza
- explicar por qué ciertos módulos aparecen/ocultan

---

### Principios de diseño (Body)

- Sensación **premium, calm, iOS‑native**.
- Texto mínimo, jerarquía numérica clara.
- Gráficos con líneas suaves y área sutil, sin ruido visual.
- Modular: si un dato no existe, el módulo se oculta o muestra estado “No disponible” con explicación breve.

---

### Reglas de datos (Body)

- Fuente principal: **HealthKit** (Apple Health).
- Body debe soportar datos intermitentes (p. ej., HRV no diario).
- Cuando existan múltiples fuentes, priorizar:
  1) Apple Watch / dispositivos validados
  2) manual (si el usuario lo ingresa)
- Todas las definiciones y cálculos asociados deben referenciar `docs/METRICS_CATALOG.md`.

---

## 4.4) Especificación Pantalla Calendar (v0.1)

La pantalla **Calendar** entrega una vista mensual para evaluar **consistencia** y **distribución de carga**.
Su objetivo no es explorar historial (eso es **Workouts**), sino responder:

• ¿Estoy entrenando consistentemente?
• ¿Cómo se distribuye mi carga por semanas/días?
• ¿Qué hice un día específico?

Calendar debe sentirse como una **vista de patrones de entrenamiento**, no como un listado de sesiones.

---

### Principios de producto (Calendar)

- **Vista mensual primero** para detectar consistencia y patrones.
- Interacción principal: **tap en día → ver sesiones del día → Activity Detail**.
- **Calendar no reemplaza Workouts**.

Calendar responde a la pregunta:

**"¿Cómo se distribuye mi entrenamiento en el tiempo?"**

Mientras que:

Workouts → explorar sesiones
Activity Detail → analizar una sesión

---

### Estructura de layout (de arriba hacia abajo)

**A) TOP BAR**

Elementos:

- Título: Calendar
- Icono opcional de búsqueda
- Icono opcional de filtros

Reglas:

- Minimalista
- Consistente con Trends y Body

---

**B) MONTH HEADER**

Elementos:

- Mes y año centrado (ej: October 2023)
- Flecha izquierda → mes anterior
- Flecha derecha → mes siguiente

Opcional:

- Acción "Jump to Today"

---

**C) MONTH GRID (núcleo de Calendar)**

Grid mensual con:

- Días en formato

M T W T F S S

Cada día puede contener indicadores de estado.

Estados posibles (v0.1):

- **Done** → entrenamiento completado
- **Hard** → día con carga alta
- **Plan** → entrenamiento planificado

Visualización:

- puntos de color
- máximo 2–3 indicadores por día
- día seleccionado con halo sutil

Objetivo:

Permitir identificar rápidamente:

- días activos
- semanas con mayor carga
- consistencia de entrenamiento

---

**D) WEEK CONTEXT (opcional compacto)**

Resumen de la semana seleccionada o semana actual.

Métricas posibles:

- **Week Load (TRIMP)**
- **Sessions** (#)
- **Time** o **Distance**

Reglas:

- máximo 3 métricas
- visualización compacta
- no reemplaza la pantalla Trends

---

**E) DAY PANEL (detalle del día)**

Cuando el usuario toca un día en el calendario, aparece un panel con las sesiones del día.

Contenido:

- fecha (ej: Today, Oct 24)
- lista de sesiones

Cada sesión incluye:

- nombre
- tipo (Run / Bike / Strength / Row)
- resumen breve
- carga estimada (TRIMP o equivalente)
- estado (Completed / Planned)

Acciones:

- tap en sesión → **Activity Detail**

Este panel conecta Calendar con el análisis profundo del entrenamiento.

---

### Principios de diseño (Calendar)

- diseño oscuro consistente con el resto de la app
- indicadores visuales simples
- evitar saturación visual
- prioridad en reconocer patrones semanales y mensuales

Calendar debe sentirse más cercano a herramientas como:

- TrainingPeaks
- Strava calendar
- Gentler Streak consistency view

que a un calendario genérico de productividad.

---

### Reglas de datos (Calendar)

Fuente principal:

- Apple Health / HealthKit

Reglas:

- días con múltiples sesiones deben agregarse correctamente
- días sin HR pueden mostrar carga estimada
- sesiones deben ser accesibles desde el panel del día

La clasificación **Hard Day** puede derivarse de:

- carga diaria TRIMP relativa
- percentil de carga reciente

(la fórmula exacta se documentará en `docs/METRICS_CATALOG.md`).

---

### Relación con otras pantallas

Calendar responde:

**"¿Estoy entrenando consistentemente?"**

Mientras que:

Home → estado actual del atleta
Trends → evolución de carga y fitness
Workouts → historial navegable de sesiones

Body → métricas fisiológicas

## 4.5) Especificación Pantalla Workouts (v0.1)

La pantalla **Workouts** muestra el historial completo de sesiones del atleta.

Objetivo: permitir explorar rápidamente entrenamientos recientes y acceder al análisis detallado de cada sesión.

Workouts responde a la pregunta:

**“¿Qué entrenamientos he realizado recientemente?”**

Mientras que:

- **Calendar** → consistencia y distribución en el tiempo (vista mensual/semanal)
- **Activity Detail** → análisis profundo de una sesión
- **Trends** → evolución longitudinal de carga/fitness/fatiga/forma

---

### Principios de producto (Workouts)

- **Feed cronológico**: más recientes primero.
- **Exploración rápida**: encontrar un entrenamiento en **< 5 segundos**.
- **Enfoque en resumen + acceso a detalle**: la lista no debe verse como base de datos.
- **Workouts no reemplaza Calendar**: Calendar es patrones; Workouts es historial navegable.

---

### Estructura de layout (de arriba hacia abajo)

**A) TOP BAR**

Elementos:

- Título: **Workouts**
- Icono de búsqueda (opcional)
- Icono de filtros (opcional)

Reglas:

- Minimalista
- Consistente con Trends/Body

---

**B) FILTER CHIPS (tipos de deporte)**

Chips horizontales para filtrar el feed por tipo de actividad.

Ejemplo:

All · Run · Bike · Strength · Walk · Row

Reglas:

- selección simple (1 activa)
- transición suave del feed
- mostrar solo deportes existentes en el rango actual

---

**C) LISTA CRONOLÓGICA (secciones por recencia)**

Lista principal scrollable.

Agrupación sugerida (v0.1):

- Today
- Yesterday
- Last 7 Days
- Older

Reglas:

- máximo 1 encabezado por bloque
- evita ruido visual

---

**D) WORKOUT CARD (resumen de sesión)**

Cada sesión se presenta como una tarjeta.

Contenido típico (running):

- Nombre (editable en detalle)
- Tipo (Run/Bike/Strength/Row)
- Resumen breve (ej. “Intervals • 4×8min Z4”)
- **3 métricas principales** (según deporte)
- **Training Load** (TRIMP o equivalente) con etiqueta/estado si es estimado

Ejemplo running:

Morning Threshold Run

Intervals • 4×8min Z4

12.4 km · 58:30 · 4:42/km

94 TRIMP

Reglas:

- números claros, etiquetas pequeñas
- texto mínimo
- icono del deporte visible

Opcional (si datos disponibles):

- mini‑sparkline (HR o Pace) para dar “lectura rápida” sin abrir el detalle

---

### Interacciones

- Tap en tarjeta → abre **Activity Detail**
- Long‑press (futuro) → acciones rápidas (pin, editar nombre, ocultar)

---

### Principios de diseño (Workouts)

- Cards limpias, respirables, estilo premium
- Jerarquía numérica clara
- Consistencia visual con Trends (mismos radios, sombras, tipografía)

Workouts debe sentirse comparable a:

- Strava activity feed
- Athlytic workouts list
- Apple Fitness history

---

### Reglas de datos (Workouts)

Fuente principal:

- Apple Health / HealthKit

Reglas:

- Días con múltiples sesiones se listan como sesiones separadas
- Evitar duplicados (dedupe obligatorio)
- Si falta HR: mostrar **TRIMP estimado** con etiqueta “Estimado”

La lógica de cálculo y fallback debe referenciar `docs/METRICS_CATALOG.md`.

## 5) Definición MVP (Entregable Fase 4)

**MVP = Motor TRIMP v1 + Tarjeta Hero TRIMP Home**

Capacidades mínimas:  
- Ingesta de entrenamientos (al menos 30 días).  
- Calcular TRIMP diario para All/Run/Bike/Strength/Walk.  
- Renderizar gráfico TRIMP 28d rápido desde caché local.  
- Tocar día → listar sesiones y totales.  
- Manejar HR faltante con fallback documentado.

### TRIMP sin HR (fallback obligatorio)  
- Si un entrenamiento no tiene **datos de HR**, TRIMP debe ser **estimado** usando:  
  - duración  
  - deporte/tipo (run/bike/strength/walk)  
  - factor de intensidad por tipo (documentado)  
  - posible refinamiento futuro con check-ins usuario (RPE)  
- TRIMP estimado debe estar etiquetado en UI (ej. **Estimado**) y explicado en detalle de métrica.

Fuera del alcance para MVP:  
- Suite completa de Tendencias tipo Athlytic  
- Scoring completo Battery (puede aparecer después del MVP, pero debe ser transparente al introducirse)  
- Coach

---

## 6) Métricas Clave y Criterios de Éxito

### Éxito de producto (v1)  
- Uso diario: usuario puede revisar estado en < 30 segundos.  
- Confianza: puntuaciones nunca se sienten como caja negra (drivers visibles).  
- Estabilidad: no duplicados, sin contradicciones obvias.

### Éxito técnico  
- Home carga rápido (almacenamiento local + refresco incremental).  
- Permisos HealthKit y estados de datos faltantes se manejan limpio.  
- Reglas de layout consistentes cross-device (iPhone/Mac).

---

## 7) Restricciones y Guardrails

### 7.1 Integridad de datos  
- Se requiere deduplicación (evitar contar entrenos doble).  
- Días con múltiples sesiones deben agregarse correctamente.

### 7.2 Transparencia  
- Battery/Recuperación debe mostrar drivers y alertas de datos faltantes.  
- **Todos los modelos de cálculo** deben estar documentados en `docs/METRICS_CATALOG.md` (fuente única de verdad).  
- Cada métrica visible debe incluir micro-definición + link de cálculo.

### 7.3 Enfoque correr primero, multi-deporte  
- La carga de resistencia está anclada en TRIMP (principalmente run/bike).  
- La fuerza no debe distorsionar la carga de resistencia.

### 7.4 Manejo de estrés (sin señal “real”)  
- Si no hay señal directa de estrés, mostrar **Estrés (proxy)** solo cuando los inputs lo permitan.  
- Proxy debe ser transparente sobre inputs usados e indicar completitud de datos.  
- Si no hay inputs suficientes, ocultar tarjeta Estrés o mostrar “Datos insuficientes”.

### 7.5 Manejo de fuerza (carga secundaria)  
- Fuerza se trackea como **narrativa secundaria de carga** (ej. minutos/semana y componente opcional cardio ligero si hay HR).  
- No mezclar fuerza 1:1 en esfuerzo TRIMP/resistencia en v1.  
- Fuerza puede influir en Battery como driver explícito, con contribución claramente etiquetada.

### 7.6 Definición anillo de movimiento  
- Anillo de movimiento anclado en **movimiento fuera de entrenos**:  
  - Pasos + distancia caminada como primarios  
  - Energía activa puede aparecer en detalle pero no debe ser driver principal en v1

### 7.7 Diseño primero  
- No pantallas UI de features antes de aprobar tokens/componentes del Design System.

---

## 8) Fases Futuras (alto nivel)

- **Capa tipo Athlytic:** Tendencias más profundas, zonas, fitness/fatiga/forma, indicadores de riesgo.  
- **Integración Body:** Pipeline Speediance import (si es factible).  
- **Coach:** constructor de planes + recomendación diaria adaptativa + chat con guardrails.

---

## 9) Preguntas Abiertas (para resolver en Fase 1)

- Detalles fórmula TRIMP y factores intensidad para estimación sin HR.  
- Definición modelo proxy estrés (inputs, fórmula, umbrales).  
- Scoring Battery v1: pesos exactos de drivers y líneas base.  
- Fuentes de medidas corporales: Apple Health vs manual vs formato Speediance import.
