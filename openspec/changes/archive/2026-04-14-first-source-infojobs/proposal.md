# Proposal: First Source InfoJobs

## Intent

Deliver the first concrete source on top of the closed ingestion framework so JobMatchRAG can capture real public InfoJobs offers with auditable raw evidence and framework-native run traceability.

## Scope

### In Scope
- Add one concrete InfoJobs adapter for public offer ingestion under the existing framework.
- Pull via `GET /offer` and enrich with `GET /offer/{offerId}` only for newly seen offers.
- Preserve list raw and detail raw separately when detail exists.
- Use source-side filters only as capture optimizations.

### Out of Scope
- New framework semantics, canonical checkpoint redesign, or provider-specific retry redesign.
- Offer normalization, canonicalization, scoring, dashboard/Telegram publishing, or admin workflows.
- Regular re-enrichment of already known offers, OAuth2/private endpoints, or broad dictionary-management features beyond what the adapter minimally needs.

## Capabilities

### New Capabilities
- `infojobs-source-ingestion`: ingest public InfoJobs offers through the shared framework, preserving list/detail evidence and adapter-level provider behavior.

### Modified Capabilities
- None.

## Approach

Implement a provider adapter that plugs into the existing `job -> run` orchestration and declares InfoJobs capabilities explicitly. It uses `GET /offer` as primary discovery, treats `sinceDate` as source-side volume reduction only, enriches only new offers, and emits raw handoff material that keeps list/detail payloads distinct.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/jobmatchrag/source_ingestion/contracts.py` | Modified | Fit shared adapter contract to a concrete source |
| `src/jobmatchrag/source_ingestion/orchestrator.py` | Modified | Wire first adapter into existing run flow |
| `src/jobmatchrag/source_ingestion/` | New/Modified | Add InfoJobs-specific adapter/client surface |
| `openspec/specs/` | New | Add spec for `infojobs-source-ingestion` |
| `docs/sources/infojobs-api-reference.md` | Modified | Reflect chosen adapter boundaries |
| `docs/architecture/vertical-roadmap.md` | Modified | Keep vertical status visible |
| `docs/architecture/ingestion-and-sources.md` | Modified | Document first concrete source boundary if spec changes require it |
| `docs/architecture/domain-data-overview.md` | Modified | Confirm raw preservation implications if needed |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| InfoJobs list/detail shape drift causes lossy evidence handling | Med | Preserve both raws distinctly and spec it |
| Adapter leaks provider quirks into framework semantics | Med | Keep checkpoint/filter/retry authority in the framework |
| New-only enrichment misses later detail changes | Med | Accept as V1 tradeoff; defer refresh strategy |

## Rollback Plan

Remove the concrete InfoJobs adapter and related wiring while preserving the shared ingestion framework unchanged.

## Dependencies

- Closed `source-ingestion-framework`
- InfoJobs Basic Auth app credentials

## Success Criteria

- [ ] Proposal stays limited to the first concrete InfoJobs source.
- [ ] Specs can define adapter behavior, raw preservation, and enrichment boundaries without ambiguity.
- [ ] Affected living docs are identified for later updates.
