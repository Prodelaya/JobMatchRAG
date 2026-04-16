# Tasks: Source Search Strategy

## Phase 1: Curated evidence foundations

- [x] 1.1 RED: extend `tests/unit/source_ingestion/test_search_strategy.py` for the curated AVE city dataset, seeded-city lookup, explicit consultancy signals, and known-company-list ambiguity/exclusion scenarios.
- [x] 1.2 GREEN: create `src/jobmatchrag/source_ingestion/data/ave_hybrid_cities.json` from the April 2026 user city list and add `src/jobmatchrag/source_ingestion/data/known_consultancies.json` for the provisional company list.
- [x] 1.3 GREEN: add `src/jobmatchrag/source_ingestion/data_loader.py` to load/version curated datasets and expose stable lookups for strategy evaluation.

## Phase 2: Canonical strategy and evidence evaluation

- [x] 2.1 GREEN: create `src/jobmatchrag/source_ingestion/search_strategy.py` with `CaptureProfile`, AVE dataset-backed geography checks, and consultancy/body-shopping evaluation combining text evidence plus company-list hints.
- [x] 2.2 REFACTOR: export stable strategy/data helpers from `src/jobmatchrag/source_ingestion/__init__.py` only if downstream imports need them, keeping names aligned with the spec.
- [x] 2.3 RED: extend `tests/unit/source_ingestion/test_contracts.py` for `CanonicalFilterOutcome`, dataset evidence refs, known-company ambiguity markers, and `ProviderExecutionPlan` pushdown vs post-fetch traces.
- [x] 2.4 GREEN: update `src/jobmatchrag/source_ingestion/contracts.py` and `src/jobmatchrag/source_ingestion/models.py` so outcomes and snapshots carry dataset version, evidence refs, and explicit-vs-curated consultancy rationale.

## Phase 3: Run snapshots and provider boundary

- [x] 3.1 RED: extend `tests/unit/source_ingestion/test_orchestrator.py` so runs preserve canonical intent, AVE dataset version, pushed-down filters, post-fetch filters, and ambiguity outcomes before downstream handoff.
- [x] 3.2 GREEN: update `src/jobmatchrag/source_ingestion/orchestrator.py` to snapshot canonical profiles and derived provider params without making provider filters semantic authority.
- [x] 3.3 RED: extend `tests/unit/source_ingestion/test_infojobs_discovery.py` to prove InfoJobs consumes only derived params, keeps `sinceDate` advisory, and leaves AVE/consultancy rules canonical post-fetch.
- [x] 3.4 GREEN: update `src/jobmatchrag/source_ingestion/infojobs/discovery.py` to emit supported pushdown params only and preserve auditable derived request details.

## Phase 4: Integration verification

- [x] 4.1 RED: extend `tests/integration/source_ingestion/test_job_run_flow.py` for seeded-city hybrid eligibility, known-company ambiguity without text proof, and explicit consultancy exclusion overriding later stages.
- [x] 4.2 GREEN: update fixtures/helpers so integration traces record canonical intent, dataset versions, derived request params, ambiguity preserved, and survivor handoff ordering before scoring/LLM.
- [x] 4.3 REFACTOR: consolidate duplicated trace/evidence fixtures across unit and integration tests only if scenarios stay explicit.

## Phase 5: Living documentation and drift fixes

- [x] 5.1 Update `docs/architecture/ingestion-and-sources.md`, `docs/architecture/domain-data-overview.md`, and `docs/architecture/scoring-foundation.md` to document curated AVE seeding, provisional consultancy lists, and canonical post-fetch authority.
- [x] 5.2 Update `docs/PRD-JobMatchRAG.md`, `docs/architecture/vertical-roadmap.md`, and `docs/sources/infojobs-api-reference.md` so product framing, roadmap sequencing, and InfoJobs usage reflect the revised source-search boundary.
- [x] 5.3 Update `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` to remove the AVE-owner and consultancy-list risks now closed, leaving only true follow-ups if any remain.
