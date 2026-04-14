# Open Questions — JobMatchRAG Foundation

**Estado:** solo pendientes reales tras el foundation pack  
**Objetivo:** dejar visibles únicamente las decisiones que de verdad siguen abiertas, sin mezclar ya-resuelto con backlog futuro de verticales.

---

## 1. Pending items that remain open

| ID | Pregunta pendiente | Por qué sigue abierta | Cuándo conviene cerrarla |
| --- | --- | --- | --- |
| OQ-01 | **Nombre público definitivo del producto** | impacta branding, copy y URL, pero no bloquea la foundation técnica | antes de consolidar el escaparate público final |
| OQ-02 | **Ubicación exacta del recruiter chat en la experiencia pública** | afecta layout, discoverability, coste percibido y rate limiting UX | antes de la vertical pública/UI del chat |
| OQ-03 | **Profundidad y cadencia de métricas públicas** | la foundation ya cierra frescura/actividad básica, pero no cuánto detalle mostrar ni con qué actualización | antes de la vertical `public-dashboard` |
| OQ-04 | **Detalle fino posterior del stack y contrato RAG** | siguen abiertos chunking, retrieval, contrato conversacional, persistencia y defensas avanzadas de abuso | durante `recruiter-rag-corpus` y `recruiter-chat-experience` |

---

## 2. What is no longer open here

Este documento YA NO considera abiertas, dentro de la foundation:

- forma general del sistema: modular monolith;
- backend base: FastAPI;
- procesamiento background: Celery desde V1;
- pipeline canónico por etapas;
- InfoJobs como primera fuente de producción;
- hard filters antes de scoring;
- score por reglas antes de LLM;
- umbral Telegram >= 70 y bandas `buena` / `prioritaria`;
- retención por clase de dato;
- degradación empezando por recruiter chat;
- observabilidad mínima y baseline de superficie protegida.

Eso ya vive en los documentos foundation y NO debe reabrirse en verticales futuras salvo cambio explícito de strategy.

---

## 3. Reference docs for resolved decisions

- `docs/PRD-JobMatchRAG.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/domain-data-overview.md`
- `docs/architecture/ingestion-and-sources.md`
- `docs/architecture/scoring-foundation.md`
- `docs/operations/policies-and-controls.md`
- `docs/operations/observability-and-security.md`
- `docs/product/recruiter-chat.md`

---

## 4. Recommended next change

Con `decision-foundation-pack`, `project-tooling-bootstrap`, `uv-bootstrap-alignment` y `source-ingestion-framework` ya cerrados, la siguiente vertical recomendada es:

1. `first-source-infojobs`
   - implementar la primera fuente real sobre el framework común ya cerrado;
   - validar el contrato reusable de adapters, jobs/runs, errores, retries y guardrails con un proveedor concreto sin mezclar todavía normalización ni scoring.

La secuencia viva de changes recomendados se mantiene en `docs/architecture/vertical-roadmap.md`. Si el orden cambia o se inserta un change habilitador nuevo, ese roadmap manda sobre recomendaciones históricas de este documento.
