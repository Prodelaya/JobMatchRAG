# InfoJobs Source Ingestion Specification

## Purpose

Define the first concrete InfoJobs offer-ingestion capability on top of the shared ingestion framework without changing framework semantics.

## Requirements

### Requirement: Vertical boundary

The system MUST scope `infojobs-source-ingestion` to one concrete adapter for public InfoJobs offers. It MUST reuse the existing framework semantics for jobs, runs, checkpoints, filtering authority, retries, and traceability, and MUST NOT introduce canonicalization, scoring, publication, admin workflows, or framework redesign.

#### Scenario: Scope is validated against the framework
- GIVEN the InfoJobs capability is reviewed for acceptance
- WHEN its responsibilities are checked
- THEN it is limited to source capture and raw handoff under the shared framework
- AND no downstream or framework-redesign behavior is required

### Requirement: Framework-compatible adapter behavior

The InfoJobs adapter MUST declare and operate within framework capabilities rather than redefining them. Provider-specific quirks SHALL stay encapsulated inside the adapter, while the framework SHALL remain the authority for run lifecycle, canonical checkpoint meaning, error taxonomy, and internal filtering.

#### Scenario: Provider quirk appears during ingestion
- GIVEN InfoJobs exposes endpoint-specific shapes or parameters
- WHEN the adapter runs under the framework
- THEN the quirk is handled as adapter behavior
- AND framework semantics remain unchanged

### Requirement: Listing-based discovery

The system MUST use `GET /offer` as the primary discovery mechanism for InfoJobs offers. Listing behavior SHALL support paginated retrieval and provider parameters derived from the canonical capture profile, while preserving both the canonical target-filter intent and the effective InfoJobs request as part of run traceability. The InfoJobs request MUST remain an execution artifact rather than semantic authority.

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

### Requirement: New-offer-only detail enrichment

The system MUST use `GET /offer/{offerId}` only to enrich offers first discovered as new to JobMatchRAG. It MUST NOT perform regular detail refresh for offers already known to the system, even if those offers reappear in later listings.

#### Scenario: Newly seen offer receives detail enrichment
- GIVEN a listed offer is not yet known to the system
- WHEN the adapter evaluates enrichment
- THEN the offer is enriched through `GET /offer/{offerId}`

#### Scenario: Known offer is seen again
- GIVEN a listed offer is already known to the system
- WHEN the adapter evaluates enrichment
- THEN no regular detail re-enrichment is required
- AND the offer continues through the framework with listing evidence only for that run

### Requirement: `sinceDate` and source filters are optimization only

The system MAY use InfoJobs source-side filters, including `q`, geography/modality-related params, and `sinceDate`, to reduce capture volume. These filters MUST remain advisory optimizations only, MUST NOT replace canonical target filters or framework checkpoints, and MUST NOT narrow product semantics beyond the canonical capture profile. Unsupported canonical filters SHALL be applied post-fetch within JobMatchRAG.

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

### Requirement: Best-effort checkpoint semantics only

The system MUST treat the InfoJobs adapter checkpoint as best-effort continuation over the observed listing order, not as a deterministic exactly-once cursor. The adapter SHOULD anchor same-page resumption with the next expected offer identifier when available, and the documented contract MUST NOT promise stronger continuity than the provider listing can actually sustain.

#### Scenario: Listing order shifts before a resumed fetch
- GIVEN a checkpoint points to the next offer on a page
- WHEN the provider reorders or inserts items before the next fetch
- THEN the adapter resumes using the anchored offer identifier when possible
- AND if the anchor is no longer present it prefers defensive replay over silent skipping
- AND the spec still treats the checkpoint as best-effort rather than deterministic continuity

### Requirement: Distinct raw preservation and traceability

For every discovered offer, the system MUST preserve the listing raw payload with its effective query and run traceability. When detail enrichment occurs, the system MUST preserve the detail raw separately from the listing raw rather than treating detail as a replacement. The resulting handoff SHALL remain traceable to the run, source, offer identity, and payload origin (`list` or `detail`).

#### Scenario: List and detail shapes differ
- GIVEN an offer has both listing and detail payloads
- WHEN raw evidence is handed off downstream
- THEN list raw and detail raw remain distinct artifacts
- AND auditors can tell which fields came from listing versus detail capture

#### Scenario: New offer detail cannot complete in the same fetch
- GIVEN a listed offer is new to JobMatchRAG
- WHEN detail enrichment is blocked by request budget exhaustion or a detail `429`
- THEN the listing raw is still handed off for that offer
- AND the trace marks detail capture as deferred instead of dropping the offer silently

### Requirement: Explicit out-of-scope behavior

The system MUST NOT require OAuth2/private candidate endpoints, implemented dictionary-management features beyond minimum adapter needs, or regular backfill/re-enrichment strategies as part of this capability.

#### Scenario: Future expansion is proposed during this vertical
- GIVEN a request adds private endpoints or recurring refresh strategy
- WHEN scope is checked for `first-source-infojobs`
- THEN that behavior is rejected from this spec
- AND it is left for a later change
