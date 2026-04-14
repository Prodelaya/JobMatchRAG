# Proposal: Source Ingestion Framework

## Intent

Establecer el framework común de ingesta para convertir la gobernanza ya cerrada en una capacidad reusable y trazable. El problema actual no es la falta de una fuente concreta, sino la ausencia de un marco estable para ejecutar jobs/runs, modelar adapters intermedios, clasificar errores y aplicar guardrails operativos sin mezclar decisiones de InfoJobs ni de verticales futuras.

## Scope

### In Scope
- Definir el framework común adapter-agnostic para `SourceAdapter`, `job` + `run`, checkpoints, rate-limit awareness y ventanas temporales.
- Fijar la semántica transversal de errores, retries selectivos, trazabilidad por run y guardrails operativos por defecto.
- Dejar explícita la frontera entre optimizaciones de filtrado en la fuente y autoridad canónica de filtros internos.

### Out of Scope
- Implementar adapters concretos, incluida InfoJobs.
- Normalización/canonicalización de ofertas, scoring, UI/admin tools u observabilidad hardening posterior.

## Capabilities

### New Capabilities
- `source-ingestion-framework`: Framework compartido para ejecutar ingesta multi-fuente con contrato intermedio, runs trazables y control operacional básico.

### Modified Capabilities
- `ingestion-governance`: Refinar el contrato de adapter/runs/errores desde gobernanza mínima hacia semántica operativa consistente.

## Approach

Extender la base de `ingestion-governance` con un contrato intermedio de adapter que declare capacidades, manteniendo el pipeline y los filtros internos ya definidos en docs como autoridad final. El vertical define shape y límites del framework; los adapters concretos quedan para cambios posteriores.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/specs/ingestion-governance/spec.md` | Modified | Delta de comportamiento para contrato, runs, errores y retries. |
| `openspec/specs/source-ingestion-framework/spec.md` | New | Capacidad nueva del framework común. |
| `docs/architecture/ingestion-and-sources.md` | Modified | Contrato, modelo job/run, errores, filtros y guardrails. |
| `docs/architecture/system-overview.md` | Modified | Rol del módulo `source-ingestion` dentro del pipeline. |
| `docs/architecture/domain-data-overview.md` | Modified | Semántica de `Source`, `RunRecord` y trazabilidad. |
| `docs/operations/policies-and-controls.md` | Modified | Guardrails y límites operativos por defecto. |
| `docs/operations/observability-and-security.md` | Modified | Trazabilidad estructurada mínima por run. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Framework demasiado abstracto | Med | Limitarlo a capacidades y semánticas ya cerradas en discovery. |
| Scope creep hacia InfoJobs/admin ops | Med | Mantener proposal adapter-agnostic y sin workflows concretos. |
| Duplicar autoridad de filtros | Low | Reafirmar que filtros source-side son solo optimización. |

## Rollback Plan

Revertir el artifact set de este change y mantener vigente solo `ingestion-governance` mínima, sin afectar verticales ya cerrados.

## Dependencies

- `uv-bootstrap-alignment` cerrado.
- Discovery de `source-ingestion-framework` cerrada y autoritativa para este proposal.

## Success Criteria

- [ ] El proposal deja una frontera clara entre framework común y adapters concretos.
- [ ] Specs/design pueden derivar contrato, runs, errores y trazabilidad sin reabrir foundations.
- [ ] Los living docs a actualizar quedan identificados para las siguientes fases.
