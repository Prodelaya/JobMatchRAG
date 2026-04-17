# Delta for InfoJobs Source Ingestion

## MODIFIED Requirements

### Requirement: Listing-based discovery

The system MUST use `GET /offer` as the primary discovery mechanism for InfoJobs offers. Listing behavior SHALL support paginated retrieval and provider parameters derived from the canonical capture profile through the mapped InfoJobs execution plan, while preserving the canonical family intent, the mapped plan, and the effective InfoJobs request as run traceability. The InfoJobs request MUST remain an execution artifact rather than semantic authority, and the adapter MUST record pushed-down filters versus validations left for post-fetch.
(Previously: listing queries were derived from the canonical profile directly, without a required mapped-plan trace separating pushdown from post-fetch.)

#### Scenario: Offers are discovered from a mapped plan
- GIVEN an InfoJobs ingestion run starts from canonical family intent
- WHEN discovery executes
- THEN offers are retrieved from `GET /offer` using the mapped execution plan
- AND the run trace keeps both the family intent and the effective request

#### Scenario: Degraded query stays non-authoritative
- GIVEN the mapped plan cannot encode all modality or seniority semantics
- WHEN the adapter emits provider params
- THEN the trace marks those semantics as post-fetch pending
- AND the InfoJobs params do not become semantic authority
