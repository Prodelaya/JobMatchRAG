# Preguntas abiertas — Foundation de JobMatchRAG

**Estado:** solo pendientes reales tras el foundation pack  
**Objetivo:** dejar visibles únicamente las decisiones que de verdad siguen abiertas, sin mezclar lo ya resuelto con el backlog futuro de verticales.

---

## 1. Pendientes que siguen abiertos

| ID | Pregunta pendiente | Por qué sigue abierta | Cuándo conviene cerrarla |
| --- | --- | --- | --- |
| OQ-01 | **Nombre público definitivo del producto** | impacta branding, copy y URL, pero no bloquea la foundation técnica | antes de consolidar el escaparate público final |
| OQ-02 | **Ubicación exacta del recruiter chat en la experiencia pública** | afecta layout, discoverability, coste percibido y UX de rate limiting | antes de la vertical pública/UI del chat |
| OQ-03 | **Profundidad y cadencia de métricas públicas** | la foundation ya cierra frescura/actividad básica, pero no cuánto detalle mostrar ni con qué actualización | antes de la vertical `public-dashboard` |
| OQ-04 | **Detalle fino posterior del stack y contrato RAG** | siguen abiertos chunking, retrieval, contrato conversacional, persistencia y defensas avanzadas contra abuso | durante `recruiter-rag-corpus` y `recruiter-chat-experience` |

---

## 2. Qué ya no está abierto acá

Este documento YA NO considera abiertas, dentro de la foundation:

- forma general del sistema: modular monolith;
- backend base: FastAPI;
- procesamiento background: Celery desde V1;
- pipeline canónico por etapas;
- InfoJobs como primera fuente de producción;
- filtros duros antes del scoring;
- score por reglas antes de LLM;
- umbral de Telegram >= 70 y bandas `buena` / `prioritaria`;
- retención por clase de dato;
- degradación empezando por recruiter chat;
- observabilidad mínima y baseline de superficie protegida.

Eso ya vive en los documentos foundation y NO debe reabrirse en verticales futuras salvo cambio explícito de estrategia.

---

## 3. Documentos de referencia para decisiones resueltas

- `docs/PRD-JobMatchRAG.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/domain-data-overview.md`
- `docs/architecture/ingestion-and-sources.md`
- `docs/architecture/scoring-foundation.md`
- `docs/operations/policies-and-controls.md`
- `docs/operations/observability-and-security.md`
- `docs/product/recruiter-chat.md`

---

## 4. Siguiente cambio recomendado

Con `decision-foundation-pack`, `project-tooling-bootstrap`, `uv-bootstrap-alignment`, `source-ingestion-framework`, `first-source-infojobs` y `source-search-strategy` ya cerrados y archivados, el foco recomendado hoy es:

1. **abrir `infojobs-search-mapping`**
   - ahora sí conviene traducir la estrategia canónica ya archivada a params nativos de InfoJobs sin contaminar la semántica del producto.

La secuencia viva de changes recomendados se mantiene en `docs/architecture/vertical-roadmap.md`. Si el orden cambia o se inserta un change habilitador nuevo, ese roadmap manda por encima de las recomendaciones históricas de este documento.
