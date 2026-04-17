# Tasks: InfoJobs Search Mapping

## Phase 1: Canonical handoff contracts

- [x] 1.1 RED: extend `tests/unit/source_ingestion/test_contracts.py` and `tests/unit/source_ingestion/test_search_strategy.py` for canonical family/language/reinforcement contracts and to prove provider params never become semantic authority.
- [x] 1.2 GREEN: update `src/jobmatchrag/source_ingestion/contracts.py` and `src/jobmatchrag/source_ingestion/models.py` with provider-agnostic canonical handoff types plus projection/audit records carrying `authority=canonical`, trust labels, degradations, and pending post-fetch checks.
- [x] 1.3 GREEN: refactor `src/jobmatchrag/source_ingestion/search_strategy.py` so it emits bilingual canonical families, justified mixed variants, and reinforcement metadata without emitting InfoJobs-native semantics.

## Phase 2: InfoJobs projection layer

- [x] 2.1 RED: add `tests/unit/source_ingestion/test_infojobs_mapping.py` for bilingual family plans, tactical probes, light origin exclusions, trust-level assignment, and degraded semantics staying post-fetch.
- [x] 2.2 GREEN: create `src/jobmatchrag/source_ingestion/infojobs/mapping.py` to translate the canonical handoff into auditable `InfoJobsExecutionPlan` family plans using only approved InfoJobs pushdown/support/optimization params.
- [x] 2.3 RED: extend `tests/unit/source_ingestion/test_infojobs_discovery.py` and `tests/unit/source_ingestion/test_infojobs_adapter.py` to prove discovery/request building consumes only mapped provider params and never reconstructs canonical meaning.
- [x] 2.4 GREEN: update `src/jobmatchrag/source_ingestion/infojobs/discovery.py` and `src/jobmatchrag/source_ingestion/infojobs/adapter.py` so listing requests serialize mapped params only while preserving effective-request traceability per emitted query.

## Phase 3: Orchestration and audit trace wiring

- [x] 3.1 RED: extend `tests/unit/source_ingestion/test_orchestrator.py` for canonical handoff snapshots, mapped family plans, projection trust metadata, and explicit pushdown-vs-post-fetch trace persistence.
- [x] 3.2 GREEN: update `src/jobmatchrag/source_ingestion/orchestrator.py` to build the canonical handoff, invoke `infojobs.mapping`, persist both artifacts on the run trace, and pass only projected params into `FetchContext`.
- [x] 3.3 RED: extend `tests/integration/source_ingestion/test_infojobs_adapter_flow.py` so end-to-end runs show degraded semantics, effective InfoJobs requests, and canonical authority surviving adapter execution.
- [x] 3.4 REFACTOR: update `src/jobmatchrag/source_ingestion/__init__.py` and any affected helper imports only as needed to expose stable provider-agnostic contracts without leaking InfoJobs assumptions outward.

## Phase 4: Verification and living docs

- [x] 4.1 Verify unit/integration coverage for every spec scenario: bilingual baselines, justified mixed queries, partial `experienceMin`, optimization-only `sinceDate`, support-only `teleworking`, and explainable degradations.
- [x] 4.2 Update `docs/sources/infojobs-api-reference.md` and `docs/architecture/ingestion-and-sources.md` with the adapter/projection boundary, approved param trust levels, and run-trace requirements.
- [x] 4.3 Update `docs/architecture/scoring-foundation.md`, `docs/PRD-JobMatchRAG.md`, and `docs/architecture/vertical-roadmap.md` so scoring/product/roadmap language keeps canonical intent authoritative and marks this vertical’s new status/next step.
- [x] 4.4 Review `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md`; update it only if this vertical truly resolves or creates an architecture question about multi-provider mapping.
