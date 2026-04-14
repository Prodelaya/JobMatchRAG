# Tasks: First Source InfoJobs

## Scope Guardrails

- Stay inside `src/jobmatchrag/source_ingestion/` plus required living docs.
- Do not add normalization, scoring, publication, admin flows, or framework redesign.
- Keep `GET /offer` as discovery, detail only for new offers, `sinceDate` as optimization, and list/detail raw as distinct captures.

## Phase 1: Boundaries and contracts

- [x] 1.1 Align `src/jobmatchrag/source_ingestion/contracts.py` and package exports for an InfoJobs adapter seam; completion: adapter dependencies and raw handoff shape are named without moving checkpoint/error authority out of the framework.
- [x] 1.2 Add RED tests in `tests/unit/source_ingestion/test_infojobs_discovery.py` for listing pagination, `sinceDate` as advisory only, and known-vs-new detail gating; depends on 1.1; completion: failing cases map to spec scenarios.
- [x] 1.3 Add RED tests in `tests/unit/source_ingestion/test_infojobs_raw_handoff.py` and `test_infojobs_errors.py` for sibling list/detail captures and error translation; depends on 1.1; completion: failures prove provenance and taxonomy requirements.

## Phase 2: Provider adapter seams

- [x] 2.1 Create `src/jobmatchrag/source_ingestion/infojobs/client.py` and `discovery.py` for Basic Auth list/detail requests, query planning, and continuation state; depends on 1.2; completion: unit tests for request context and pagination pass.
- [x] 2.2 Create `src/jobmatchrag/source_ingestion/infojobs/raw_handoff.py` and `errors.py` for traceable list/detail envelopes and provider-to-framework error mapping; depends on 1.3; completion: raw/error unit tests pass.
- [x] 2.3 Create `src/jobmatchrag/source_ingestion/infojobs/adapter.py` and `__init__.py` to orchestrate one-page fetch, adapter-local known-offer checks, selective detail enrichment, and request-budget stop rules; depends on 2.1-2.2; completion: adapter returns framework-compatible `FetchOutcome` without re-enrichment of known offers.

## Phase 3: Framework wiring and integration

- [x] 3.1 Wire the adapter into `src/jobmatchrag/source_ingestion/orchestrator.py` and related registration points only as a concrete source option; depends on 2.3; completion: framework run flow can invoke InfoJobs without semantic changes.
- [x] 3.2 Add integration tests in `tests/integration/source_ingestion/test_infojobs_adapter_flow.py` for `job -> run -> raw handoff`, partial page closure under request budgeting, and no detail fetch for known offers; depends on 3.1; completion: spec-critical scenarios pass end-to-end with stubs.

## Phase 4: Living docs and verification

- [x] 4.1 Update `docs/sources/infojobs-api-reference.md`, `docs/architecture/ingestion-and-sources.md`, and `docs/architecture/domain-data-overview.md`; depends on 3.2; completion: docs reflect adapter seams, raw provenance, and unchanged checkpoint semantics.
- [x] 4.2 Update `docs/architecture/vertical-roadmap.md` with tasks/apply progress for `first-source-infojobs`; depends on 4.1; completion: current vertical status and next recommended phase stay accurate.
- [x] 4.3 Run planned verification `.venv/bin/python -m ruff check .`, `.venv/bin/python -m mypy src`, `.venv/bin/python -m pytest` after implementation; depends on 3.2 and 4.1-4.2; completion: results are ready for `sdd-verify` review.
