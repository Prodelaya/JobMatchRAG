# Proposal: Source Search Strategy

## Intent

Definir la semántica canónica de búsqueda/captura de JobMatchRAG sin convertir params provider-side en fuente de verdad. El producto necesita `target filters` agnósticos a proveedor que siempre apliquen antes del downstream LLM, usando pushdown solo cuando una fuente lo soporte.

## Scope

### In Scope
- Definir un `capture profile` canónico con familias bilingües de búsqueda y `target filters` explícitos.
- Fijar cuáles filtros se empujan al proveedor cuando existe soporte y cuáles deben aplicarse post-fetch cuando no lo hay.
- Formalizar ambigüedad, degradación y handoff a `infojobs-search-mapping` + downstream distillation/enrichment.

### Out of Scope
- Implementar aún el mapping InfoJobs ni cambiar adapters concretos.
- Reabrir scoring, canonicalización o delegar hard exclusions al LLM.

## Capabilities

### New Capabilities
- `source-search-strategy`: Estrategia canónica de captura con search families, `target filters`, ambigüedad y degradación agnósticas a proveedor.

### Modified Capabilities
- `source-ingestion-framework`: Extender `filter intent`/traceabilidad para distinguir target filters canónicos vs provider params derivados.
- `infojobs-source-ingestion`: Aclarar que `q`, ubicación, `sinceDate` y demás params son capa de ejecución optimizada, no semántica del producto.

## Approach

Usar un artefacto liviano de `capture profile` con tres search families: automatización interna + IA/LLM/agentes, automatización interna sin IA explícita y adyacencia Odoo. El perfil define `target filters` canónicos para seniority alta, geografía/modalidad incompatibles, body-shopping evidente y frescura confiablemente >15 días. Si el proveedor soporta un target filter, se hace pushdown; si no, se captura más amplio y se filtra post-fetch dentro del pipeline propio. En ambos casos, la distillation/enrichment LLM sigue después y nunca reemplaza exclusiones duras ni target filters.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/specs/source-search-strategy/spec.md` | New | Capability canónica de search strategy. |
| `openspec/specs/source-ingestion-framework/spec.md` | Modified | Handoff y trazabilidad de target filters vs params provider-side. |
| `openspec/specs/infojobs-source-ingestion/spec.md` | Modified | Boundary con `infojobs-search-mapping` y pushdown optimizado. |
| `docs/architecture/ingestion-and-sources.md` | Modified | Política de pushdown vs post-fetch filtering. |
| `docs/architecture/domain-data-overview.md` | Modified | Evidencia de filtros aplicados y casos ambiguos. |
| `docs/architecture/scoring-foundation.md` | Modified | Confirmar que hard filters preceden al LLM. |
| `docs/architecture/vertical-roadmap.md`, `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md`, `docs/PRD-JobMatchRAG.md`, `docs/sources/infojobs-api-reference.md` | Modified | Alinear roadmap, framing y superficie real del provider. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Mezclar semántica canónica con params InfoJobs | Med | Especificar target filters como fuente de verdad y params como optimización. |
| Sobreexclusión por señales semánticas incompletas | Med | Descartar temprano solo ante evidencia explícita/confiable; lo ambiguo sigue vivo. |
| Drift con scoring/docs abiertas | High | Actualizar living docs del mismo boundary en el mismo change. |

## Rollback Plan

Revertir proposal/specs/docs de este change y volver al estado actual donde solo existen `provider_filters` advisory sin estrategia canónica intermedia.

## Dependencies

- `first-source-infojobs` cerrado.
- Exploration `sdd/source-search-strategy/explore` vigente en Engram/OpenSpec.

## Success Criteria

- [ ] Queda definido un `capture profile` con search families y `target filters` canónicos.
- [ ] La spec separa pushdown provider-side de post-fetch filtering sin cambiar la semántica del producto.
- [ ] El LLM queda explícitamente aguas abajo y no reemplaza hard exclusions ni target filters.
