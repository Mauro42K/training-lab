<file name=0 path=/Users/mauro/Training-lab/docs/PRD.md># Training Lab — PRD (v0.1)

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

## 3) Arquitectura de Información (Pestañas v0.2)

1) **Home**  
- Dashboard “Hoy”: TRIMP primero, luego anillos de estado y tarjetas de drivers.  
2) **Trends**  
- Analíticas a largo plazo: carga, preparación vs esfuerzo, zonas, indicadores de fitness.  
3) **Workouts**  
- Historial de entrenamientos + tarjetas resumen + detalle de entrenamientos.  
4) **Body**  
- Tendencias de peso y medidas corporales (reemplaza pestaña Journal).  
5) **More**  
- Ajustes, permisos, calibración, unidades, privacidad.  
6) **Coach (futuro)**  
- Plan + recomendaciones adaptativas + chat.

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

## 4) Especificación Pantalla Home (v0.2)

### Orden de layout (de arriba hacia abajo)

**A) TARJETA HERO: TRIMP**  
- Gráfico de barras 28 días  
- Filtro toggle: All / Run / Bike / Strength / Walk  
- Badges: Hoy, total 7d, total 28d  
- Tocar un día → Hoja de día (lista de sesiones)

**B) FILA DE ANILLOS (lanzador)**  
- Recuperación (Battery)  
- Sueño  
- Esfuerzo  
- Movimiento

**C) TARJETAS DE DRIVERS (tocar → detalle)**  
- Salud: HRV + RHR (tendencia vs línea base)  
- Estrés (solo si está disponible; si no, proxy explícito o oculto — ver Guardrails)  
- Desglose Battery (“drivers” + completitud de datos)  
- Pasos & Meta (movimiento fuera de entrenamientos)  
- Fuerza & Cross-training (minutos/semana + narrativa secundaria de carga)

### No negociables (Home)  
- TRIMP es la primera tarjeta grande.  
- Todas las puntuaciones mostradas deben incluir **“¿Por qué?”** (drivers) y **“Completitud de datos”**.  
- Cada métrica mostrada debe tener una **micro-definición** (“qué es”) y un **link de cálculo** (“cómo lo calculamos”).

---

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
</file>
