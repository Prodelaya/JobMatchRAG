# Design: Source Ingestion Framework

## Technical Approach

Diseñar `source-ingestion` como un framework interno del modular monolith que orquesta ejecuciones `job -> run`, consume un `SourceAdapter` intermedio con capacidades declaradas y entrega `RawOfferSnapshot` + trazabilidad al pipeline canónico sin absorber normalización, elegibilidad ni scoring. Este change baja a diseño operativo lo cerrado en `ingestion-governance` y `source-ingestion-framework`, manteniendo la frontera adapter-agnostic.

## Architecture Decisions

| Decision | Options | Choice | Rationale |
|---|---|---|---|
| Orquestación del framework | 1) adapter ejecuta todo 2) core orquesta y adapter solo integra fuente | Opción 2 | Mantiene semántica común de runs, retries, guardrails y trazabilidad sin acoplar el sistema a un proveedor. |
| Modelo de ejecución | 1) run único 2) job + run | Opción 2 | Separa intención reusable (`job`) de intento ejecutado (`run`), habilitando auditoría, repetición y comparación histórica. |
| Clasificación de errores | 1) central rígida 2) adapter mapea a taxonomía compartida | Opción 2 | El adapter conoce la rareza fuente; el framework conserva una semántica transversal (`retryable`/`terminal` + categoría) para decidir retries y reporting. |
| Filtros source-side | 1) autoridad compartida 2) optimización advisory | Opción 2 | Preserva `eligibility` interna como autoridad de producto y evita secuestro por capacidades del portal. |

## Data Flow

```text
Admin/Celery trigger
        │
        ▼
IngestionJob ──creates──> IngestionRun
        │                    │
        │              loads adapter + capability snapshot
        ▼                    │
 source-ingestion core ──calls──> SourceAdapter.fetch(run context)
        │                    │
        │<── raw page/items / source error / checkpoint hint
        ▼
 RawOfferSnapshot store + run trace
        │
        └── handoff to normalization stage
```

Parciales no mezclan etapas: si un run captura material usable y luego encuentra incidencias retryables agotadas o límites operativos, cierra `partial`; si no produce material usable, cierra `failed`.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `openspec/changes/source-ingestion-framework/design.md` | Create | Diseño técnico del vertical. |
| `src/jobmatchrag/source_ingestion/__init__.py` | Create | Boundary del módulo de framework. |
| `src/jobmatchrag/source_ingestion/contracts.py` | Create | `SourceAdapter`, capability snapshot y tipos de contexto/outcome. |
| `src/jobmatchrag/source_ingestion/models.py` | Create | Modelos conceptuales de `IngestionJob`, `IngestionRun` y metadatos operativos. |
| `src/jobmatchrag/source_ingestion/orchestrator.py` | Create | Semántica común de ejecución, retries y guardrails. |
| `docs/architecture/ingestion-and-sources.md` | Modify | Expandir contrato, job/run, filtros, errores y guardrails. |
| `docs/architecture/system-overview.md` | Modify | Aclarar rol del framework dentro de `source-ingestion` y el handoff a downstream stages. |
| `docs/architecture/domain-data-overview.md` | Modify | Refinar `RunRecord`/`Source` con metadata operativa y parcialidad. |
| `docs/operations/policies-and-controls.md` / `docs/operations/observability-and-security.md` | Modify | Guardrails y trazabilidad operativa mínima por run. |

## Interfaces / Contracts

```text
SourceAdapter
- source_key
- capabilities: {pagination, time_windows, supported_filters, checkpoints, rate_limit}
- fetch(run_request) -> FetchBatch | FetchTerminalFailure
- classify_error(error) -> ErrorClassification
```

`IngestionJob`: intención reusable (source, schedule/trigger intent, filter intent, run-scope policy).  
`IngestionRun`: intento ejecutado (status, timestamps, counters, checkpoint_in/out, retry_count, capability_snapshot, filter_snapshot, rate_limit_observations, error_summary).  
`ErrorClassification`: categoría compartida + retryability. La taxonomía vive en el framework; el adapter solo traduce errores fuente a esa taxonomía.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Consumo de capacidades, clasificación y decisión de retry/status | Casos sobre core con adapters fake. |
| Integration | `job -> run -> raw handoff` y persistencia de trazabilidad | Flujos del módulo `source-ingestion` sin adapters reales. |
| Docs/spec alignment | Fronteras y políticas vivas | Verificar updates en docs autoritativos del change. |

## Migration / Rollout

No migration required. Primero se incorpora el framework común; adapters concretos quedan para verticales posteriores.

## Open Questions

- [ ] None at design level; thresholds numéricos finos de retry/backoff siguen siendo configuración operativa futura.

## Downstream Documentation Impact & Tradeoffs

La implementación deberá actualizar `docs/architecture/ingestion-and-sources.md`, `system-overview.md`, `domain-data-overview.md`, `policies-and-controls.md` y `observability-and-security.md`. Tradeoff principal: un contrato intermedio reduce acoplamiento y facilita nuevas fuentes, pero exige que el framework capture más metadata operativa por run para que las capacidades declaradas no se vuelvan “magia implícita”.
