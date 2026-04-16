# Implementation Progress

**Change**: source-search-strategy  
**Mode**: Strict TDD

## Completed Tasks
- [x] 1.1 Extend strategy tests for curated AVE lookup, explicit consultancy text, and known-company ambiguity.
- [x] 1.2 Seed in-repo curated datasets for hybrid cities and provisional known consultancies.
- [x] 1.3 Add dataset loader/versioned lookup helpers.
- [x] 2.1 Implement canonical capture profile and post-fetch offer evaluation.
- [x] 2.2 Export stable strategy/data helpers from the package boundary.
- [x] 2.3 Extend contract tests for canonical outcomes and provider execution plans.
- [x] 2.4 Add canonical trace/value objects for dataset snapshots and evidence refs.
- [x] 3.1 Extend orchestrator tests for canonical intent, dataset versions, and ambiguity/exclusion handoff.
- [x] 3.2 Snapshot canonical execution trace in runs and filter excluded offers before downstream handoff.
- [x] 3.3 Extend InfoJobs discovery tests for derived-param-only pushdown boundaries.
- [x] 3.4 Preserve supported-pushdown-only InfoJobs discovery behavior with auditable derived request details.
- [x] 4.1 Add integration coverage for seeded-city survival, known-company ambiguity, and explicit consultancy exclusion.
- [x] 4.2 Record canonical trace data through integration runs before downstream stages.
- [x] 4.3 Refactor review complete; existing fixture duplication stayed explicit enough, so no extra consolidation was needed.
- [x] 5.1-5.3 Update living docs and roadmap/open-questions alignment for the new source-search boundary.
- [x] Corrective verify batch: enforce post-fetch seniority/freshness and add direct runtime proof for capture-profile authority, ambiguous hybrid survival, downstream-only AI preference, and framework-side exclusion when provider filters miss ineligible offers.

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `src/jobmatchrag/source_ingestion/data/ave_hybrid_cities.json` | Created | Seeded curated hybrid-city dataset with version/provenance metadata. |
| `src/jobmatchrag/source_ingestion/data/known_consultancies.json` | Created | Added provisional known-consultancies dataset for ambiguity evidence. |
| `src/jobmatchrag/source_ingestion/data_loader.py` | Created | Added cached dataset loaders and stable alias lookups. |
| `src/jobmatchrag/source_ingestion/search_strategy.py` | Created | Implemented capture profile, provider execution plan, offer normalization, and canonical post-fetch evaluation. |
| `src/jobmatchrag/source_ingestion/contracts.py` | Modified | Added canonical outcome, evidence ref, dataset snapshot, and provider plan contracts. |
| `src/jobmatchrag/source_ingestion/models.py` | Modified | Added canonical run/offer trace models to preserve intent and evaluation outcomes. |
| `src/jobmatchrag/source_ingestion/orchestrator.py` | Modified | Snapshots canonical trace and filters excluded offers before downstream handoff. |
| `src/jobmatchrag/source_ingestion/__init__.py` | Modified | Exported stable strategy/data/canonical-trace helpers. |
| `tests/unit/source_ingestion/test_search_strategy.py` | Created | Added RED/GREEN coverage for datasets, geography, consultancy rules, and package exports. |
| `tests/unit/source_ingestion/test_contracts.py` | Modified | Added contract coverage for evidence refs and execution-plan boundaries. |
| `tests/unit/source_ingestion/test_orchestrator.py` | Modified | Added canonical trace and survivor-handoff coverage. |
| `tests/unit/source_ingestion/test_infojobs_discovery.py` | Modified | Added pushdown-boundary coverage for derived InfoJobs params. |
| `tests/integration/source_ingestion/test_job_run_flow.py` | Modified | Added integration coverage for ambiguity preservation and hard exclusions. |
| `docs/architecture/ingestion-and-sources.md` | Modified | Documented capture-profile authority, curated datasets, and pushdown/post-fetch split. |
| `docs/architecture/domain-data-overview.md` | Modified | Documented canonical trace/evidence refs and curated dataset participation in runs. |
| `docs/architecture/scoring-foundation.md` | Modified | Clarified hard-exclusion semantics, ambiguity preservation, and LLM boundary. |
| `docs/PRD-JobMatchRAG.md` | Modified | Added canonical source-search framing to V1 scope/policy. |
| `docs/architecture/vertical-roadmap.md` | Modified | Marked change as in verification and moved next recommendation to `infojobs-search-mapping` after closure. |
| `docs/sources/infojobs-api-reference.md` | Modified | Clarified InfoJobs params as derived execution details only. |
| `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` | Modified | Removed resolved AVE/company-list uncertainty from the recommended next work. |
| `README.md` / `AGENTS.md` | Modified | Re-aligned bootstrap wording so the existing verification contract stays green. |
| `src/jobmatchrag/source_ingestion/search_strategy.py` | Modified | Added real post-fetch seniority/freshness enforcement plus deterministic freshness parsing helpers. |
| `tests/unit/source_ingestion/test_search_strategy.py` | Modified | Added runtime proof for capture-profile authority, ambiguous hybrid-without-attendance, and seniority/freshness post-fetch exclusion. |
| `tests/integration/source_ingestion/test_job_run_flow.py` | Modified | Added runtime proof that AI preference stays downstream-only and framework-side exclusion still removes ineligible offers when provider filters miss them. |

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/unit/source_ingestion/test_search_strategy.py` | Unit | N/A (new) | ✅ Written | ✅ Passed (6/6) | ✅ 6 cases | ✅ Clean |
| 1.2 | `tests/unit/source_ingestion/test_search_strategy.py` | Unit | N/A (new) | ✅ Written | ✅ Passed (6/6) | ✅ Seeded + unknown lookup paths | ➖ Structural data file |
| 1.3 | `tests/unit/source_ingestion/test_search_strategy.py` | Unit | N/A (new) | ✅ Written | ✅ Passed (6/6) | ✅ Lookup + export paths | ✅ Cached loader cleanup |
| 2.1 | `tests/unit/source_ingestion/test_search_strategy.py` | Unit | N/A (new) | ✅ Written | ✅ Passed (6/6) | ✅ Passed/ambiguous/excluded cases | ✅ Clean |
| 2.2 | `tests/unit/source_ingestion/test_search_strategy.py` | Unit | ✅ 5/5 | ✅ Written | ✅ Passed (6/6) | ➖ Single structural export surface | ✅ Clean |
| 2.3 | `tests/unit/source_ingestion/test_contracts.py` | Unit | ✅ 4/4 | ✅ Written | ✅ Passed (6/6) | ✅ Outcome + execution-plan paths | ✅ Clean |
| 2.4 | `tests/unit/source_ingestion/test_contracts.py`, `tests/unit/source_ingestion/test_orchestrator.py` | Unit | ✅ 4/4 | ✅ Written | ✅ Passed (37/37 relevant) | ✅ Dataset/evidence/run-trace paths | ✅ Clean |
| 3.1 | `tests/unit/source_ingestion/test_orchestrator.py` | Unit | ✅ 29/29 | ✅ Written | ✅ Passed (31/31) | ✅ Passed + ambiguous/excluded handoff | ✅ Clean |
| 3.2 | `tests/unit/source_ingestion/test_orchestrator.py` | Unit | ✅ 29/29 | ✅ Written | ✅ Passed (31/31) | ✅ Trace + survivor filtering paths | ✅ Clean |
| 3.3 | `tests/unit/source_ingestion/test_infojobs_discovery.py` | Unit | ✅ 21/21 | ✅ Written | ✅ Passed (22/22) | ✅ Supported vs canonical-only params | ✅ Clean |
| 3.4 | `tests/unit/source_ingestion/test_infojobs_discovery.py` | Unit | ✅ 21/21 | ✅ Written | ✅ Passed (22/22) | ✅ Advisory `sinceDate` + post-fetch-only filters | ➖ Behavior already aligned |
| 4.1 | `tests/integration/source_ingestion/test_job_run_flow.py` | Integration | ✅ 3/3 | ✅ Written | ✅ Passed (5/5) | ✅ Seeded city + ambiguous company + exclusion cases | ✅ Clean |
| 4.2 | `tests/integration/source_ingestion/test_job_run_flow.py` | Integration | ✅ 3/3 | ✅ Written | ✅ Passed (5/5) | ✅ Trace snapshots + survivor ordering | ✅ Clean |
| 4.3 | `tests/unit/source_ingestion/test_orchestrator.py`, `tests/integration/source_ingestion/test_job_run_flow.py` | Unit/Integration | ✅ 34/34 | ✅ Written | ✅ Passed | ➖ Refactor unnecessary after review | ➖ None needed |
| 5.1-5.3 | `tests/test_uv_bootstrap_alignment.py`, full verification contract | Unit/Repo | N/A (docs) | ✅ Written/updated against living-doc drift | ✅ Passed | ✅ README/AGENTS alignment + full contract rerun | ✅ Clean |
| VF.1 | `tests/unit/source_ingestion/test_search_strategy.py` | Unit | ✅ 6/6 | ✅ Written | ✅ Passed (10/10) | ✅ Capture-profile authority + ambiguous hybrid + seniority/freshness paths | ✅ Extracted reusable freshness parsing helpers |
| VF.2 | `tests/integration/source_ingestion/test_job_run_flow.py` | Integration | ✅ 5/5 | ✅ Written | ✅ Passed (7/7) | ✅ Downstream-only AI preference + provider-miss exclusion paths | ➖ None needed |

## Test Summary
- **Total tests written**: 14
- **Total tests passing**: 127
- **Layers used**: Unit (10 additions), Integration (4 additions), E2E (0)
- **Approval tests** (refactoring): None — no behavior-preserving refactor required beyond export cleanup review.
- **Pure functions created**: 7

## Deviations from Design
None — implementation matches design. The only pragmatic simplification is storing the first curated datasets as JSON files under `src/jobmatchrag/source_ingestion/data/` instead of the design sketch's YAML/reference folders while preserving versioning, provenance, and read-only runtime use.

## Issues Found
None.

## Remaining Tasks
- [ ] None.

## Status
15/15 tasks complete. Corrective verify findings fixed; ready for archive/verify re-run.
