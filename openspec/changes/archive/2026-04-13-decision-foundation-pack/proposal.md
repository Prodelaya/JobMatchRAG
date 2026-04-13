# Proposal: Decision Foundation Pack

## Intent

Cerrar decisiones P0/P1 de producto y arquitectura que hoy bloquean specs fiables. El objetivo es ordenar primero la utilidad real del sistema y sus guardrails operativos antes de bajar a diseño fino o implementación.

## Scope

### In Scope
- Confirmar foundation técnica: stack backend, límites del monolito modular y modelo de jobs/runs.
- Definir producto V1: usuario principal, objetivo real del sistema, alcance, no-alcance, priorización de fuentes y política pública de freshness/error.
- Cerrar guardrails de scraping, dedupe+republicación, scoring baseline+umbrales y explicabilidad mínima.
- Fijar decisiones mínimas de auth admin, retención/privacidad, observabilidad y presupuesto/degradación.

### Out of Scope
- Implementación de código, schemas físicos, adapters concretos o UI final.
- Contrato detallado de RAG/chatbot, chunking, prompts y UX visual del dashboard.
- Multi-candidate real, API pública, microservicios o métricas públicas avanzadas.

## Capabilities

### New Capabilities
- `product-definition-guardrails`: usuario principal, objetivo del producto, alcance V1, exposición pública y priorización inicial de fuentes.
- `platform-foundation-decisions`: stack/backend, boundaries, auth admin y política base de retención.
- `ingestion-governance`: jobs/runs, contrato de adapters y guardrails operativos/legal-risk por fuente.
- `offer-canonicalization-baseline`: dedupe, republicación, URL principal y confianza de consolidación.
- `scoring-calibration-baseline`: fórmula inicial, señales explícitas vs inferidas, umbrales y dataset de calibración.
- `cost-observability-controls`: presupuesto por componente, degradación y observabilidad mínima operativa.

### Modified Capabilities
- None.

## Approach

Usar `sdd/open-gaps-discovery/explore` como input principal y convertirlo en un pack corto de decisiones/specs secuenciadas. El orden será: definición de producto → foundation técnica → ingesta/guardrails → canonización → scoring → controles operativos. El chatbot y el escaparate público quedan desacoplados hasta que la base útil esté cerrada.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/decision-foundation-pack/proposal.md` | New | Propuesta base del change |
| `openspec/specs/` | Modified | Futuras specs derivadas de las capacidades listadas |
| `docs/*.md` | Referenced | PRD, blueprint y open questions usados como fuente |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Discovery demasiado amplio | Med | Limitarlo a decisiones P0/P1 que desbloquean specs |
| Mezclar producto con implementación | Med | Explicitar fuera de scope y no bajar a código/schema |
| Mantener huecos críticos | High | Exigir cierre de definición de producto, auth, retención y costes antes de spec detallada |

## Rollback Plan

Descartar este change sin impacto técnico: solo crea artefactos de decisión. Si queda sobredimensionado, dividir luego en spec packs más pequeños sin arrastrar implementación.

## Dependencies

- Exploración existente `sdd/open-gaps-discovery/explore`
- Documentos base: `docs/PRD-JobMatchRAG.md`, `docs/Architecture-Execution-Blueprint-JobMatchRAG.md`, `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md`

## Success Criteria

- [ ] Queda definido un orden de decisión que habilita `sdd-spec` sin inventar fundamentos.
- [ ] El alcance cubre explícitamente discovery de producto + foundation técnica + guardrails operativos.
- [ ] Se documenta qué queda fuera para evitar adelantar chatbot/UI/implementación.
