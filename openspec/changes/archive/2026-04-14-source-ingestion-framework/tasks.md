# Tasks: Source Ingestion Framework

## Phase 1: Boundary and contracts

- [x] 1.1 Create `src/jobmatchrag/source_ingestion/__init__.py` to expose the module boundary only. Purpose: mark the shared framework seam. Depends on: none. Done when: imports identify `source_ingestion` as adapter-agnostic framework scope.
- [x] 1.2 Create `src/jobmatchrag/source_ingestion/contracts.py` with `SourceAdapter`, capability declarations, fetch context/outcome, and shared error-classification interfaces. Depends on: 1.1. Done when: pagination, time windows, source filters, checkpoints, and rate-limit support are declared without concrete adapters.
- [x] 1.3 Create `src/jobmatchrag/source_ingestion/models.py` with conceptual `IngestionJob` / `IngestionRun` records and traceability metadata fields. Depends on: 1.2. Done when: job intent, run lifecycle, counters, checkpoints, retry data, and final outcome can be represented separately.

## Phase 2: Core orchestration semantics

- [x] 2.1 Create `src/jobmatchrag/source_ingestion/orchestrator.py` for shared `job -> run` execution flow. Depends on: 1.2, 1.3. Done when: orchestration consumes capability snapshots and hands raw output forward without taking over normalization or scoring.
- [x] 2.2 Add retry/error handling semantics in `src/jobmatchrag/source_ingestion/orchestrator.py` using the shared taxonomy and selective retries only. Depends on: 2.1. Done when: retryable vs terminal outcomes and `partial` vs `failed` closure rules are explicit.
- [x] 2.3 Add default guardrail handling in `src/jobmatchrag/source_ingestion/orchestrator.py` for bounded retries, bounded run scope, and rate-limit-aware execution. Depends on: 2.1, 2.2. Done when: framework-level limits are enforced without provider-specific thresholds.

## Phase 3: Verification scaffolding

- [x] 3.1 Create `tests/unit/source_ingestion/test_contracts.py` for capability declarations and error classification expectations from the specs. Depends on: 1.2, 1.3. Done when: spec scenarios for limited capabilities and non-retryable failures are covered.
- [x] 3.2 Create `tests/unit/source_ingestion/test_orchestrator.py` for retry decisions, run status transitions, and guardrail behavior with fake adapters. Depends on: 2.1-2.3. Done when: repeated job runs, selective retries, and partial-run semantics are validated.
- [x] 3.3 Create `tests/integration/source_ingestion/test_job_run_flow.py` for `job -> run -> raw handoff` traceability. Depends on: 2.1-2.3. Done when: run records show capability snapshot, filter intent, checkpoints, rate-limit observations, and final status.

## Phase 4: Living docs and change governance

- [x] 4.1 Update `docs/architecture/ingestion-and-sources.md`, `docs/architecture/system-overview.md`, and `docs/architecture/domain-data-overview.md` to align boundaries, lifecycle, and traceability. Depends on: 1.2, 1.3, 2.1. Done when: docs keep internal filters canonical and framework scope excludes concrete adapters.
- [x] 4.2 Update `docs/operations/policies-and-controls.md` and `docs/operations/observability-and-security.md` with default guardrails and per-run traceability requirements. Depends on: 2.2, 2.3. Done when: retry/guardrail policy and audit expectations match the framework behavior.
- [x] 4.3 Review `docs/architecture/vertical-roadmap.md` and `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md`; update only if sequence/status or pending decisions changed because of this vertical. Depends on: 4.1, 4.2. Done when: living-doc governance is explicitly closed without reopening adapters or other verticals.
