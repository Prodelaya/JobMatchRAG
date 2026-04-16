# AGENTS.md

## Contexto del proyecto

JobMatchRAG es un sistema personal de inteligencia de empleo para Pablo Laya. Este repositorio usa documentación viva como fuente de verdad. El foundation pack ya está cerrado; los documentos archivados son solo referencia histórica.

## Documentos fuente de verdad

| Archivo | Propósito | Actualizar cuando... |
| --- | --- | --- |
| `docs/PRD-JobMatchRAG.md` | Framing del producto, alcance de V1, visibilidad pública, baseline de Telegram, rol del recruiter chat | cambien el alcance del producto, la audiencia, la visibilidad o la promesa central |
| `docs/architecture/system-overview.md` | Forma del sistema, boundaries, pipeline canónico, mapa de módulos | cambien los boundaries de arquitectura o las etapas del pipeline |
| `docs/architecture/domain-data-overview.md` | Entidades core, lifecycle, reglas de canonicalización/republicación, modelo de evidencia | cambie el modelo de dominio o las reglas de lifecycle |
| `docs/architecture/ingestion-and-sources.md` | Contrato de fuentes, política de onboarding, modelo de runs/errores | cambien el framework de fuentes o la gobernanza de ingesta |
| `docs/sources/infojobs-api-reference.md` | Referencia específica del proveedor para auth de InfoJobs, endpoints, diccionarios, errores y comportamiento de API relevante para ingesta | cambien los supuestos de integración con InfoJobs, endpoints útiles o notas operativas específicas del proveedor |
| `docs/architecture/scoring-foundation.md` | Filtros duros, flujo de scoring, umbrales, contrato de explicabilidad | cambien las reglas de scoring, umbrales o la política de ajuste LLM |
| `docs/architecture/vertical-roadmap.md` | Orden recomendado de cambios verticales, dependencias y reglas de secuencia | cambien el orden del roadmap, las dependencias o la descomposición de cambios |
| `docs/operations/policies-and-controls.md` | Retención, backups, orden de degradación, política administrativa | cambien los controles operativos o las reglas de retención |
| `docs/operations/observability-and-security.md` | Métricas, alertas, auditabilidad, controles de superficie protegida | cambie el baseline de observabilidad/seguridad |
| `docs/product/recruiter-chat.md` | Propósito, límites y alcance permitido del recruiter chat | cambie el comportamiento o los boundaries del recruiter chat |
| `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` | Solo decisiones realmente pendientes | se resuelva un pendiente o aparezca una nueva pregunta abierta real |

## Regla de actualización continua

Si un cambio modifica una decisión documentada, contrato, política, umbral, boundary o flujo, actualizá el documento vivo correspondiente dentro del mismo cambio. Si eso no puede pasar, dejá un seguimiento bloqueante explícito en vez de permitir que la documentación derive.

Después de cada cambio importante, ejecutá una review `judgment-day` de todo el proyecto antes de considerar el trabajo cerrado. Tratá esa review como validación final obligatoria, no como un extra opcional.

Antes de abrir un cambio nuevo, aclarà los huecos específicos de ese vertical; si todavía faltan decisiones reales, hacé una ronda breve de discovery antes de propuesta/spec.

Cuando un cambio empieza, termina, se divide o modifica la secuencia recomendada, actualizá `docs/architecture/vertical-roadmap.md` en el mismo cambio para que el estado actual y el siguiente cambio recomendado sigan visibles.

Cuando una decisión pendiente se resuelve o una supuesta pregunta abierta deja de ser real, actualizá `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` en el mismo cambio para que quede limitado solo a pendientes verdaderos.

Si un cambio crea, reemplaza o archiva un documento fuente de verdad, actualizá el índice de documentación viva en `AGENTS.md` dentro del mismo cambio.

Antes de cerrar un cambio, revisá explícitamente si `docs/PRD-JobMatchRAG.md`, los documentos de arquitectura, los documentos de operaciones, `docs/architecture/vertical-roadmap.md` o `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` necesitan actualización; si la necesitan, actualizalos en el mismo cambio.

## Verificación local

Recommended local bootstrap:

Bootstrap local recomendado:

- `uv venv .venv`
- `uv pip install -e .[dev]`

Este bootstrap local recomendado preserva el contrato existente de verificación `.venv/bin/python -m ...`.
No adopta `uv sync`, `uv run`, lockfiles, hooks, CI, Docker, runtime ni cambios de alcance functional scope.

- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m mypy src`
- `.venv/bin/python -m pytest`

## Documentación externa

- Para documentación externa de librerías o frameworks, verificá primero con Context7 vía MCP antes de asumir APIs o comportamientos; si Context7 no está disponible o no alcanza, usá la documentación oficial.
- Flujo útil con Context7: resolvé primero el ID de la librería y después consultá la documentación. Las librerías más probables acá incluyen FastAPI, Celery, Next.js y Vercel AI SDK si esos stacks se adoptan.

## No hacer

- No usar documentos archivados como fuente de verdad.
- No reabrir foundations cerradas sin un cambio nuevo explícito.
- No dejar la documentación viva desactualizada después de cambiar el sistema.
- No expandir cambios chicos con alcance no relacionado.
