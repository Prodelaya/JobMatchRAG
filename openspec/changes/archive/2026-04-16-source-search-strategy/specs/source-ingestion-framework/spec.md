# Delta for Source Ingestion Framework

## MODIFIED Requirements

### Requirement: Filtering semantics
The system MUST treat canonical `target filters` from the capture profile as product authority. Provider-side filters SHALL remain advisory execution optimizations only. Supported target filters MAY be pushed down to the source, but unsupported target filters MUST still be evaluated post-fetch within JobMatchRAG. Hard exclusions MUST apply only on explicit or otherwise reliable evidence, while ambiguous cases SHALL remain eligible for downstream review/scoring.
(Previously: internal filtering was canonical, but target-filter authority, pushdown rules, and ambiguity handling were not explicit.)

#### Scenario: Source filter misses an ineligible item
- GIVEN a source returns an item outside desired filters
- WHEN internal eligibility is evaluated
- THEN internal filters decide the final outcome

#### Scenario: Ambiguous evidence is traced, not discarded
- GIVEN a source-side field suggests but does not prove incompatibility
- WHEN canonical target filters run
- THEN the item survives as ambiguous
- AND the framework does not convert ambiguity into a hard exclusion

### Requirement: Traceability and default guardrails
Each run MUST capture structured traceability including job identity, source identity, adapter capability snapshot, canonical filter intent, derived provider params, which target filters were pushed down, which were applied post-fetch, ambiguity preserved, checkpoints used, retry count, error category, rate-limit observations, and final status. The framework SHOULD define default guardrails for bounded retries, bounded run scope, and rate-limit-aware execution.
(Previously: traceability required filter intent and run guardrails, but not canonical-vs-derived filter evidence or ambiguity outcomes.)

#### Scenario: Run is audited after degraded execution
- GIVEN a run partially completes under rate limits
- WHEN the run record is inspected
- THEN the trace shows limits observed, retries attempted, and final status

#### Scenario: Pushdown boundary is audited
- GIVEN a provider executes only part of the canonical target filters
- WHEN the run trace is inspected
- THEN pushed-down and post-fetch filters are distinguishable
- AND derived provider params remain auditable as execution details
