# Delta for InfoJobs Source Ingestion

## MODIFIED Requirements

### Requirement: Listing-based discovery
The system MUST use `GET /offer` as the primary discovery mechanism for InfoJobs offers. Listing behavior SHALL support paginated retrieval and provider parameters derived from the canonical capture profile, while preserving both the canonical target-filter intent and the effective InfoJobs request as part of run traceability. The InfoJobs request MUST remain an execution artifact rather than semantic authority.
(Previously: listing discovery allowed declared source-side query/filter parameters, but it did not explicitly anchor them as derived execution details from canonical intent.)

#### Scenario: Offers are discovered from InfoJobs
- GIVEN an InfoJobs ingestion run starts with declared filter intent
- WHEN discovery executes
- THEN offers are retrieved from `GET /offer`
- AND the effective listing query remains auditable for that run

#### Scenario: Derived query stays non-authoritative
- GIVEN the canonical profile requests bilingual automation families
- WHEN the adapter emits `q` terms for InfoJobs
- THEN those terms are recorded as derived params
- AND semantic authority remains in the canonical profile

### Requirement: `sinceDate` and source filters are optimization only
The system MAY use InfoJobs source-side filters, including `q`, geography/modality-related params, and `sinceDate`, to reduce capture volume. These filters MUST remain advisory optimizations only, MUST NOT replace canonical target filters or framework checkpoints, and MUST NOT narrow product semantics beyond the canonical capture profile. Unsupported canonical filters SHALL be applied post-fetch within JobMatchRAG.
(Previously: `sinceDate` and source filters were optimization only, but the boundary for all InfoJobs params and unsupported canonical filters was not explicit.)

#### Scenario: Relative time window is requested
- GIVEN a run uses `sinceDate`
- WHEN continuity is evaluated after the run
- THEN the framework checkpoint remains the canonical continuation record
- AND `sinceDate` is treated only as source-side narrowing

#### Scenario: Provider cannot encode a canonical rule
- GIVEN the canonical profile excludes senior roles semantically
- WHEN InfoJobs lacks an equivalent provider param
- THEN the adapter captures broadly enough to preserve intent
- AND seniority exclusion still runs post-fetch
