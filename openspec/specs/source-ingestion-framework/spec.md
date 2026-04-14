# Source Ingestion Framework Specification

## Purpose
Define the shared, adapter-agnostic ingestion framework for source jobs and runs without introducing concrete source adapters.

## Requirements

### Requirement: Framework boundary
The system MUST define a common ingestion framework limited to shared contracts, lifecycle semantics, filtering semantics, error handling, traceability, and default guardrails. This change MUST NOT require or imply any concrete source adapter, canonicalization, scoring, or admin workflow behavior.

#### Scenario: Shared framework accepted without adapters
- GIVEN the framework spec is reviewed
- WHEN scope is validated
- THEN only common ingestion behavior is required
- AND concrete adapters remain out of scope

### Requirement: Source adapter capabilities contract
The system MUST expose a `SourceAdapter` contract at an intermediate abstraction level. Each adapter SHALL declare supported pagination, time-windowing, source-side filters, checkpoint support, and rate-limit support so orchestration can reason about available optimizations without changing canonical behavior.

#### Scenario: Adapter declares limited capabilities
- GIVEN an adapter lacks checkpoint support
- WHEN a job is configured for that adapter
- THEN the framework records checkpoint support as unavailable
- AND MUST NOT assume checkpoint-based continuation

### Requirement: Job and run lifecycle
The system MUST model execution as `job` plus `run`. A job SHALL describe reusable execution intent; each run SHALL represent one execution attempt with its own status, timestamps, counters, checkpoints, and outcome. Runs MUST be independently traceable from the parent job.

#### Scenario: Repeated execution of one job
- GIVEN one configured job
- WHEN it executes twice
- THEN two distinct runs are recorded
- AND each run keeps its own lifecycle data

### Requirement: Error taxonomy and selective retries
The system MUST classify run failures with a shared error taxonomy that distinguishes retryable from non-retryable outcomes. The framework SHALL retry only errors classified as retryable and MUST preserve terminal failures without reclassifying them as success.

#### Scenario: Non-retryable failure
- GIVEN a run ends with a non-retryable error category
- WHEN retry policy is evaluated
- THEN no automatic retry is scheduled
- AND the run remains terminally failed

### Requirement: Filtering semantics
The system MUST treat source-side provider filters as advisory optimization only. Internal filtering SHALL remain the canonical authority for product eligibility, even when an adapter declares source-side filtering support.

#### Scenario: Source filter misses an ineligible item
- GIVEN a source returns an item outside desired filters
- WHEN internal eligibility is evaluated
- THEN internal filters decide the final outcome

### Requirement: Traceability and default guardrails
Each run MUST capture structured traceability including job identity, source identity, adapter capability snapshot, filter intent, checkpoints used, retry count, error category, rate-limit observations, and final status. The framework SHOULD define default guardrails for bounded retries, bounded run scope, and rate-limit-aware execution.

#### Scenario: Run is audited after degraded execution
- GIVEN a run partially completes under rate limits
- WHEN the run record is inspected
- THEN the trace shows limits observed, retries attempted, and final status
