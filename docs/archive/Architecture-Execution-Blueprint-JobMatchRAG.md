# Architecture & Execution Blueprint — JobMatchRAG

**Estado:** archivado tras cierre de `decision-foundation-pack`  
**Rol actual:** inventario histórico del foundation pack, ya NO source of truth operativo.

---

## 1. Migration status

El contenido resuelto de este blueprint fue redistribuido al foundation pack documental del proyecto. A partir de ahora, este archivo queda solo como puente de migración y referencia histórica hasta su archivo/remoción definitiva.

La source of truth vive en:

- `docs/PRD-JobMatchRAG.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/domain-data-overview.md`
- `docs/architecture/ingestion-and-sources.md`
- `docs/architecture/scoring-foundation.md`
- `docs/operations/policies-and-controls.md`
- `docs/operations/observability-and-security.md`
- `docs/product/recruiter-chat.md`
- `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md`

---

## 2. Redistribution map

| Blueprint concern | New source of truth |
| --- | --- |
| framing de producto V1, visibilidad pública y Telegram | `docs/PRD-JobMatchRAG.md` |
| forma general del sistema, boundaries y pipeline | `docs/architecture/system-overview.md` |
| entidades, lifecycle, evidencia, canonización y republicación | `docs/architecture/domain-data-overview.md` |
| gobernanza de fuentes, contrato de adapters, runs y errores | `docs/architecture/ingestion-and-sources.md` |
| hard filters, scoring híbrido, thresholds y explicabilidad | `docs/architecture/scoring-foundation.md` |
| retención, backups, degradación y baseline de privacidad | `docs/operations/policies-and-controls.md` |
| métricas mínimas, alertas, audit trail y superficie protegida | `docs/operations/observability-and-security.md` |
| framing, límites y dependencias del recruiter chat | `docs/product/recruiter-chat.md` |
| pendientes reales que siguen abiertos | `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` |

---

## 3. What this file no longer does

Este archivo ya NO debe usarse para:

- redefinir arquitectura base;
- listar backlog completo de decisiones abiertas;
- mezclar recomendaciones preliminares con decisiones aceptadas;
- actuar como documento maestro único del proyecto.

Si algo parece contradecir a los documentos foundation, ganan los documentos foundation.

---

## 4. Recommended execution after migration

Con la foundation documental ya cerrada, la secuencia recomendada pasa a ser:

1. `project-tooling-bootstrap`
2. `source-ingestion-framework`

Razón: primero conviene cerrar el bootstrap de tooling (`openspec/config.yaml` + harness mínimo de verificación) y recién después convertir las decisiones aceptadas en una capacidad ejecutable sin reabrir producto, boundaries, scoring base u operaciones mínimas.

---

## 5. Archive note

Este archivo se conserva solo como rastro histórico en `docs/archive/`. La source of truth activa permanece en el foundation pack documental y en `openspec/specs/`.
