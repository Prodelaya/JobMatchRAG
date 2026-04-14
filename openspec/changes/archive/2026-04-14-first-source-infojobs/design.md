# Design: First Source InfoJobs

## Technical Approach

Add an InfoJobs-specific adapter package on top of the closed `source_ingestion` framework. The shared orchestrator keeps authority for `job -> run`, retries, guardrails, checkpoint lifecycle, and status closure; the adapter translates `FetchContext` into paginated `GET /offer` discovery plus selective `GET /offer/{offerId}` enrichment only for offers detected as new, then emits raw handoff envelopes that preserve list/detail evidence separately.

## Architecture Decisions

| Decision | Options | Choice | Rationale |
|---|---|---|---|
| Adapter placement | Extend framework core vs add provider subpackage | Provider subpackage | Preserves the closed adapter-agnostic framework and isolates InfoJobs quirks. |
| New-offer detection | Framework decides vs adapter-local collaborator | Adapter-local collaborator | “Known vs new” is needed only to decide provider detail calls; the framework must stay unaware of provider enrichment policy. |
| Raw preservation | Merge list/detail into one raw vs sibling captures | Sibling captures in one handoff envelope | Keeps provenance auditable when list and detail shapes differ. |
| `sinceDate` usage | Treat as checkpoint vs advisory filter | Advisory filter only | Keeps continuity under framework checkpoint semantics already closed in foundation docs. |

## Data Flow

```text
IngestionJob
   │
   ▼
IngestionOrchestrator ──creates──> IngestionRun
   │                               │
   └──────── calls InfoJobsAdapter.fetch(context)
                                   │
                     Query planner builds effective list request
                                   │
                             GET /offer (one page)
                                   │
                for each listed offer: KnownOfferIndex.is_new(...)
                         │ yes                          │ no
                         ▼                              ▼
                 GET /offer/{offerId}            skip detail
                         │                              │
                         └──── RawHandoffBuilder emits per-offer envelope
                                   │
                                   ▼
                     FetchOutcome(raw_items, next_checkpoint, exhausted)
```

Each `fetch()` handles one listing page plus bounded detail fan-out. If request pressure prevents finishing all required enrichments for the current page, the adapter stops at the last fully processed offer and returns an opaque continuation checkpoint; `sinceDate` is never used as that checkpoint.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `openspec/changes/first-source-infojobs/design.md` | Create | Technical design artifact for this vertical. |
| `src/jobmatchrag/source_ingestion/infojobs/__init__.py` | Create | Public boundary for the InfoJobs adapter package. |
| `src/jobmatchrag/source_ingestion/infojobs/adapter.py` | Create | `SourceAdapter` implementation and fetch orchestration for list/detail flow. |
| `src/jobmatchrag/source_ingestion/infojobs/client.py` | Create | Basic Auth HTTP client and endpoint-version-aware request surface. |
| `src/jobmatchrag/source_ingestion/infojobs/raw_handoff.py` | Create | Builder for distinct list/detail raw envelopes with traceability metadata. |
| `src/jobmatchrag/source_ingestion/infojobs/errors.py` | Create | Translation from InfoJobs/API errors to shared `ErrorClassification`. |
| `src/jobmatchrag/source_ingestion/infojobs/discovery.py` | Create | Query planning, pagination state, and new-offer/detail decision helpers. |
| `docs/sources/infojobs-api-reference.md` | Modify | Confirm adapter decisions: page-size ceiling, endpoint-version split, trace fields, and error mapping notes. |
| `docs/architecture/ingestion-and-sources.md` / `docs/architecture/domain-data-overview.md` / `docs/architecture/vertical-roadmap.md` | Modify | Reflect first concrete source boundary, raw evidence shape, and vertical progress. |

## Interfaces / Contracts

```text
InfoJobsAdapter(SourceAdapter)
- depends on: InfoJobsClient, KnownOfferIndex, InfoJobsRawHandoffBuilder
- fetch(context) -> FetchOutcome

KnownOfferIndex
- is_new(source_key, source_offer_id) -> bool

Raw handoff item
- source_key
- source_offer_id
- trace: {job_id, run_id, checkpoint_in, list_request, page_context}
- captures.list: required raw payload + endpoint/version metadata
- captures.detail: optional raw payload + endpoint/version metadata
```

The handoff envelope is the decision boundary to downstream `raw`: the framework forwards it unchanged; later stages may persist it as one `RawOfferSnapshot` with nested origins or split persisted artifacts, but the adapter must already preserve origin labels (`list`, `detail`).

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Query planning, pagination continuation, new-offer gating, raw envelope shape, error translation | Fake InfoJobs responses and known-offer index stubs. |
| Integration | `job -> run -> raw handoff` with selective detail enrichment and partial closure under rate-limit/budget pressure | Orchestrator + real adapter collaborators with stubbed HTTP client. |
| Docs/spec alignment | Fixed decisions remain unchanged | Verify living-doc updates for boundaries and traceability. |

## Migration / Rollout

No migration required. This is the first concrete adapter on top of an existing framework.

## Open Questions

- [ ] None blocking at design level; exact numeric request/detail budgets remain operational tuning, not architectural scope.

## Downstream Documentation Impact & Tradeoffs

Implementation must update `docs/sources/infojobs-api-reference.md`, `docs/architecture/ingestion-and-sources.md`, `docs/architecture/domain-data-overview.md`, and `docs/architecture/vertical-roadmap.md`. Main tradeoff: keeping detail only for newly known offers reduces provider cost and preserves V1 scope, but later changes in provider detail for already-known offers will not be refreshed in this vertical.
