## Exploration: source-ingestion-framework

### Current State
La foundation ya cerró las decisiones base de ingesta: InfoJobs official API como primera fuente, pipeline canónico por etapas, `SourceAdapter` común de alto nivel, `RunRecord` con trazabilidad mínima, errores `retryable|terminal`, autoridad final de filtros internos y baseline de observabilidad/retención. Pero `docs/architecture/ingestion-and-sources.md` deja explícitamente para esta vertical la conversión de esa foundation en una capacidad implementable, y todavía no fija varias semánticas operativas necesarias para proponer sin ambigüedad.

### Affected Areas
- `docs/architecture/ingestion-and-sources.md` — define contrato, runs, errores y deja esta vertical abierta.
- `docs/architecture/system-overview.md` — fija pipeline, módulo `source-ingestion` y background execution reutilizable.
- `docs/architecture/domain-data-overview.md` — fija `Source`, `RunRecord`, `RawOfferSnapshot` y la frontera de trazabilidad.
- `docs/operations/policies-and-controls.md` — fija retención, operaciones protegidas y guardrails operativos.
- `docs/operations/observability-and-security.md` — fija métricas, alertas y audit trail mínimos.
- `docs/PRD-JobMatchRAG.md` — fija alcance V1 y autoridad de filtros internos.
- `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` — confirma que este vertical es el siguiente cambio recomendado, no una decisión ya cerrada.

### Approaches
1. **Ir directo a propuesta** — asumir que la foundation ya alcanza.
   - Pros: menos fricción inicial.
   - Cons: deja ambigüedad en contrato real del adapter, semántica de runs/retries, límites y frontera exacta del vertical.
   - Effort: Low

2. **Mini discovery enfocada** — cerrar solo los gaps reales que bloquean una propuesta precisa para este vertical.
   - Pros: reduce ambigüedad, evita scope creep y mantiene alineación con la living documentation.
   - Cons: agrega una ronda breve de decisión previa.
   - Effort: Low

### Recommendation
Hacer una mini discovery enfocada. La foundation ya cerró el gobierno general, pero no alcanza todavía para una propuesta limpia de `source-ingestion-framework` sin decidir algunas semánticas concretas del framework: frontera exacta del vertical, detalle mínimo del contrato del adapter, modelo de run/job, política de retries parciales, filtros permitidos del lado de la fuente, trazabilidad mínima y si este vertical debe o no cerrar límites operativos por defecto.

### Risks
- Saltar discovery puede mezclar framework común con decisiones específicas de InfoJobs o con verticales futuras.
- Proposal/spec podría reabrir foundation cerrada o dejar ambigüedad operativa en runs y errores.

### Ready for Proposal
No — conviene cerrar primero una mini discovery de ~6 gaps: scope boundary, adapter contract depth, run/job model, retry/partial semantics, source-side filter policy, traceability/minimum operational defaults.
