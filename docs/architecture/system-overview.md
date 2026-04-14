# Visión general del sistema — JobMatchRAG

## 1. Propósito

Este documento fija la columna vertebral del sistema para verticales futuras. No define implementación runtime; define la forma, los boundaries y los contratos base que NO deben volver a decidirse en cada change.

## 2. Forma del sistema

JobMatchRAG adopta un **modular monolith** sobre **FastAPI + Celery**.

- **FastAPI** sostiene las superficies HTTP públicas y protegidas.
- **Celery** ejecuta runs, reprocesos y tareas de background desde V1.
- El sistema comparte un modelo de datos y una trazabilidad end-to-end.
- No se abren microservicios mientras la foundation siga siendo single-candidate, low-cost y fuertemente acoplada entre ingesta, canonicalización, scoring y publicación.

## 3. Pipeline canónico

El flujo canónico del sistema es:

`source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`

### Intención de cada etapa

| Etapa | Intención | Salida principal |
|---|---|---|
| `source` | Ejecutar el adapter de una fuente bajo un contrato común | contexto de run + respuesta de la fuente |
| `raw` | Persistir el snapshot capturado tal como llega | `RawOfferSnapshot` |
| `normalized` | Mapear a una forma común comparable | `NormalizedOffer` |
| `canonical` | Consolidar evidencia y una sola oferta de producto | `CanonicalOffer` + `OfferEvidence[]` |
| `eligibility` | Aplicar filtros duros previos al scoring | `EligibilityDecision` |
| `scored` | Calcular regla base y ajuste LLM acotado | `ScoreBreakdown` + `LLMAdjustment` |
| `published/notified` | Proyectar al dashboard y decidir alerta | `PublishedOfferProjection` + `TelegramNotification?` |

## 4. Boundaries de alto nivel

### 4.1 Superficie pública

- dashboard público de lectura;
- métricas visibles de actividad/frescura;
- recruiter chat orientado de forma secundaria al público, siempre desacoplado del core de ingesta/scoring.

### 4.2 Superficie protegida

- operaciones administrativas dedicadas;
- lanzamiento de ingestas y reprocesos;
- reindexados o tareas internas futuras;
- acceso separado, MFA-ready y nunca mezclado con rutas públicas.

### 4.3 Ejecución en background

Toda operación de duración no trivial corre fuera del request/response directo:

- runs de fuentes;
- reprocesos por etapa;
- tareas costosas de scoring/ajuste;
- notificaciones y trabajos operativos.

## 5. Mapa de módulos

La foundation se organiza por capacidades, no por capas técnicas globales.

| Módulo | Responsabilidad |
|---|---|
| `source-ingestion` | framework común agnóstico al adapter para `job -> run`, capabilities, retries, guardrails y handoff raw trazable; NO define adapters concretos ni etapas downstream ni persiste todavía `RawOfferSnapshot` dentro de este módulo |
| `offer-normalization` | forma común, calidad mínima de campos, mapping por fuente |
| `offer-canonicalization` | dedupe, evidencias, empresa/oferta canónica, republicación |
| `offer-eligibility` | filtros duros previos al scoring |
| `offer-scoring` | score por reglas, ajuste LLM acotado, estados finales |
| `publication-dashboard` | proyecciones públicas y reglas de visibilidad |
| `notifications` | Telegram y registro de envíos |
| `recruiter-chat` | experiencia secundaria sobre el corpus de Pablo |
| `admin-operations` | acciones protegidas para operar el sistema |
| `platform-shared` | auth admin, configuración, auditoría, retención, observabilidad |

## 6. Controles transversales

Los siguientes controles envuelven todo el pipeline:

- **RunRecord** para trazabilidad por ejecución;
- snapshot de capabilities/filter intent por run dentro de `source-ingestion`;
- políticas de retención por clase de dato;
- métricas mínimas de éxito, fallo, volumen y latencia operativa;
- clasificación de errores `retryable` frente a terminales;
- posibilidad de reproceso administrativo sin romper el histórico.

## 7. Contrato de publicación

Una oferta solo entra en la superficie pública después de pasar por `eligibility` y `scored`.

- el dashboard trabaja sobre proyecciones ya calculadas;
- Telegram solo se dispara para oportunidades nuevas con **score >= 70**;
- la frescura se comunica en la experiencia pública;
- el histórico completo se preserva internamente aunque la vista por defecto favorezca lo reciente.

## 8. Posicionamiento del recruiter chat

Recruiter chat es una capacidad **secundaria**. Depende de la foundation, pero no la define.

- no puede imponer su propio modelo de datos core;
- no puede degradar antes la ingesta, el scoring o la publicación;
- responde solo desde el corpus y el contexto profesional de Pablo.

## 9. Qué deben reutilizar los cambios verticales futuros

Todo change vertical posterior debe reutilizar estas decisiones:

- modular monolith sobre FastAPI + Celery;
- pipeline canónico por etapas;
- separación explícita entre superficie pública y operaciones protegidas;
- módulos organizados por capacidad;
- `source-ingestion` entrega raw + trazabilidad y NO absorbe normalización, eligibility ni scoring;
- controles transversales de runs, retención, métricas y reproceso.

Si una vertical necesita más detalle, lo agrega sin reabrir esta foundation.
