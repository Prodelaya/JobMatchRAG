# System Overview — JobMatchRAG

## 1. Purpose

Este documento fija la columna vertebral del sistema para futuras verticales. No define implementación runtime; define shape, boundaries y contratos base que NO deben redecidirse en cada change.

## 2. System Shape

JobMatchRAG adopta un **modular monolith** sobre **FastAPI + Celery**.

- **FastAPI** sostiene las superficies HTTP públicas y protegidas.
- **Celery** ejecuta runs, reprocesos y tareas de background desde V1.
- El sistema comparte un modelo de datos y una trazabilidad end-to-end.
- No se abren microservicios mientras la foundation siga siendo single-candidate, low-cost y fuertemente acoplada entre ingesta, canonicalización, scoring y publicación.

## 3. Canonical Pipeline

El flujo canónico del sistema es:

`source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`

### Stage intent

| Stage | Intent | Output principal |
|---|---|---|
| `source` | Ejecutar el adapter de una fuente bajo un contrato común | contexto de run + respuesta fuente |
| `raw` | Persistir el snapshot capturado tal como llega | `RawOfferSnapshot` |
| `normalized` | Mapear a shape común comparable | `NormalizedOffer` |
| `canonical` | Consolidar evidencia y una sola oferta de producto | `CanonicalOffer` + `OfferEvidence[]` |
| `eligibility` | Aplicar filtros duros previos al scoring | `EligibilityDecision` |
| `scored` | Calcular regla base y ajuste LLM acotado | `ScoreBreakdown` + `LLMAdjustment` |
| `published/notified` | Proyectar a dashboard y decidir alerta | `PublishedOfferProjection` + `TelegramNotification?` |

## 4. High-Level Boundaries

### 4.1 Public surface

- dashboard público de lectura;
- métricas visibles de actividad/frescura;
- recruiter chat secondary-facing, siempre desacoplado del core de ingesta/scoring.

### 4.2 Protected surface

- operaciones admin dedicadas;
- lanzamiento de ingestas y reprocesos;
- reindexados o tareas internas futuras;
- acceso separado, MFA-ready y nunca mezclado con rutas públicas.

### 4.3 Background execution

Toda operación de duración no trivial corre fuera del request/response directo:

- runs de fuentes;
- reprocesos por etapa;
- tareas de scoring/ajuste costosas;
- notificaciones y trabajos operativos.

## 5. Module Map

La foundation se organiza por capacidades, no por capas técnicas globales.

| Module | Responsibility |
|---|---|
| `source-ingestion` | framework común adapter-agnostic para `job -> run`, capabilities, retries, guardrails y snapshots raw; NO define adapters concretos ni downstream stages |
| `offer-normalization` | shape común, calidad mínima de campos, mapping por fuente |
| `offer-canonicalization` | dedupe, evidencias, empresa/oferta canónica, republicación |
| `offer-eligibility` | filtros duros previos al scoring |
| `offer-scoring` | score por reglas, ajuste LLM acotado, estados finales |
| `publication-dashboard` | proyecciones públicas y reglas de visibilidad |
| `notifications` | Telegram y registro de envíos |
| `recruiter-chat` | experiencia secundaria sobre corpus de Pablo |
| `admin-operations` | acciones protegidas para operar el sistema |
| `platform-shared` | auth admin, configuración, auditoría, retención, observabilidad |

## 6. Cross-Cutting Controls

Los siguientes controles envuelven todo el pipeline:

- **RunRecord** para trazabilidad por ejecución;
- snapshot de capabilities/filter intent por run dentro de `source-ingestion`;
- políticas de retención por clase de dato;
- métricas mínimas de éxito, fallo, volumen y latencia operativa;
- clasificación de errores retryable vs terminal;
- posibilidad de reproceso administrativo sin romper histórico.

## 7. Publication Contract

Una oferta solo entra en la superficie pública después de pasar por `eligibility` y `scored`.

- el dashboard trabaja sobre proyecciones ya calculadas;
- Telegram solo se dispara para oportunidades nuevas con **score >= 70**;
- la frescura se comunica en la experiencia pública;
- el histórico completo se preserva internamente aunque la vista por defecto favorezca lo reciente.

## 8. Recruiter Chat Positioning

Recruiter chat es una capacidad **secundaria**. Depende de la foundation, pero no la define.

- no puede imponer su propio modelo de datos core;
- no puede degradar primero la ingesta, scoring o publication;
- responde solo desde corpus y contexto profesional de Pablo.

## 9. What Future Vertical Changes Must Reuse

Todo change vertical posterior debe reutilizar estas decisiones:

- modular monolith sobre FastAPI + Celery;
- pipeline canónico por etapas;
- separación explícita entre superficie pública y operaciones protegidas;
- módulos organizados por capacidad;
- `source-ingestion` entrega raw + trazabilidad y NO absorbe normalización, eligibility ni scoring;
- cross-cutting controls de runs, retención, métricas y reproceso.

Si una vertical necesita más detalle, lo agrega sin reabrir esta foundation.
