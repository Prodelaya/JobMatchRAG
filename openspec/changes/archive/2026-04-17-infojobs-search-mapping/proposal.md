# Proposal: InfoJobs Search Mapping

## Intent

Traducir la `capture profile` canónica ya cerrada a planes de ejecución reales de InfoJobs sin ceder autoridad semántica al portal. El problema a resolver es capturar mejor los roles objetivo (internal tools, automation, AI aplicada para empleados) usando `q` y filtros fiables del proveedor, pero dejando la semántica fina, exclusiones duras y ambigüedad bajo control interno de JobMatchRAG.

## Scope

### In Scope
- Definir cómo familias canónicas por intención/idioma se convierten en query families InfoJobs auditables.
- Especificar qué filtros InfoJobs se usan como pushdown fiable (`q`, geografía/modality limitadas, `experienceMin`, `sinceDate`, `category`/`subcategory`, `teleworking`) y cómo degradan.
- Formalizar trazabilidad de family, language baseline, términos, filtros pusheados, degradaciones y filtros que quedan post-fetch.

### Out of Scope
- Reabrir la semántica canónica de `source-search-strategy` o volver a Odoo eje principal.
- Cambiar scoring, canonicalización o convertir InfoJobs en autoridad de seniority/geografía/elegibilidad.

## Capabilities

### New Capabilities
- `infojobs-search-mapping`: planificador/mapper que traduce familias canónicas a capacidades reales de InfoJobs con degradación explícita y auditoría completa.

### Modified Capabilities
- `infojobs-source-ingestion`: el adapter consume el plan mapeado y registra pushdown real vs post-fetch pendiente.
- `source-search-strategy`: aclara el boundary de handoff para que familias, idiomas y refuerzos tecnológicos sigan siendo intención canónica y no taxonomía del portal.

## Approach

Construir un execution plan por familia/idioma, centrado en intención de rol. Cada plan define baseline ES/EN y mezclas híbridas justificadas; usa `q` como señal importante pero no exclusiva; aplica solo pushdown fiable para ubicación/modalidad; trata `experienceMin` como señal fuerte pero parcial; usa `sinceDate` solo para optimización; deja semántica fina, exclusiones duras y validación final post-fetch. Tecnologías (Python, APIs, bots, LlamaIndex, LangChain) actúan como refuerzo o probes tácticos, no como eje primario.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/specs/infojobs-search-mapping/spec.md` | New | Capability de mapping canónico→InfoJobs. |
| `openspec/specs/infojobs-source-ingestion/spec.md` | Modified | Boundary adapter/mapping y auditoría del request derivado. |
| `openspec/specs/source-search-strategy/spec.md` | Modified | Contrato de handoff hacia planes por familia/idioma. |
| `docs/sources/infojobs-api-reference.md`, `docs/architecture/ingestion-and-sources.md`, `docs/architecture/scoring-foundation.md`, `docs/architecture/vertical-roadmap.md`, `docs/PRD-JobMatchRAG.md`, `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` | Modified | Alinear capacidades reales, boundary semántico y roadmap. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Sobreajustar queries al vocabulario InfoJobs | Med | Mantener familias por intención e idiomas como autoridad. |
| Pushdown agresivo o engañoso | Med | Limitarse a filtros claramente fiables y degradar explícitamente. |
| Auditoría insuficiente para tuning posterior | High | Exigir trazas por family/language/terms/pushdown/degradation/post-fetch. |

## Rollback Plan

Revertir proposal/specs/docs de este change y volver al estado actual: estrategia canónica existente + params InfoJobs ad hoc sin contrato de mapping específico.

## Dependencies

- `source-search-strategy` cerrado.
- `first-source-infojobs` cerrado.

## Success Criteria

- [ ] Existe un contrato explícito entre familia canónica y plan InfoJobs por idioma.
- [ ] Queda documentado qué se empuja al proveedor, qué degrada y qué sigue post-fetch.
- [ ] La traza del run explica mapping y degradaciones sin convertir InfoJobs en autoridad semántica.
