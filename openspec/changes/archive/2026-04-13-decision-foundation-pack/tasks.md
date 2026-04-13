# Tasks: Decision Foundation Pack

## Phase 1: Product framing and target doc skeleton

- [x] 1.1 Update `docs/PRD-JobMatchRAG.md` to keep V1 framing, public visibility, Telegram threshold baseline, recruiter-chat secondary role, and explicit out-of-scope aligned with the accepted specs.
- [x] 1.2 Create `docs/architecture/system-overview.md` with modular-monolith boundaries, canonical stage flow `source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`, and module map for future vertical changes.

## Phase 2: Core architecture foundation docs

- [x] 2.1 Create `docs/architecture/domain-data-overview.md` with core entities, evidence model, lifecycle transitions, canonical/republication rules, and the future `candidate_id` boundary without opening multi-candidate implementation.
- [x] 2.2 Create `docs/architecture/ingestion-and-sources.md` with source registry, `SourceAdapter` contract, run traceability, retry/error classes, and InfoJobs-first onboarding policy.
- [x] 2.3 Create `docs/architecture/scoring-foundation.md` with eligibility gates, rule-score baseline, bounded LLM adjustment, thresholds (`buena`, `prioritaria`, Telegram >=70), and explainability contract.

## Phase 3: Operations and secondary-product docs

- [x] 3.1 Create `docs/operations/policies-and-controls.md` with retention windows, backup expectations, degradation order, admin-only operations, and privacy/security policy baseline.
- [x] 3.2 Create `docs/operations/observability-and-security.md` with minimum metrics, alert signals, audit trail expectations, protected-surface controls, and run/error visibility rules.
- [x] 3.3 Create `docs/product/recruiter-chat.md` with recruiter-chat purpose, allowed scope, refusal policy, corpus boundary, and explicit dependency on the foundation docs rather than full RAG design.

## Phase 4: Blueprint redistribution and migration cleanup

- [x] 4.1 Redistribute resolved content from `docs/Architecture-Execution-Blueprint-JobMatchRAG.md` into the eight target docs, removing duplicated source-of-truth sections once captured in their destination files.
- [x] 4.2 Reduce `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` to real pending items only: public naming, exact recruiter-chat placement, advanced public metrics depth/cadence, and later RAG-detail decisions.
- [x] 4.3 Convert `docs/Architecture-Execution-Blueprint-JobMatchRAG.md` into a migration/archive note that points to the new foundation docs and marks the blueprint as transitional input, ready for later archive/removal.
- [x] 4.4 Run a final documentation consistency pass across `docs/PRD-JobMatchRAG.md`, `docs/architecture/*.md`, `docs/operations/*.md`, `docs/product/recruiter-chat.md`, and `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` to confirm the next vertical change can start as `source-ingestion-framework` without re-deciding foundations.

## Dependencies

- 1.1-1.2 unblock all later tasks.
- 2.1 depends on 1.2.
- 2.2 and 2.3 depend on 1.1-1.2; they can run in parallel.
- 3.1 depends on 2.2-2.3; 3.2 depends on 2.2 and 3.1; 3.3 depends on 1.1 and 2.3.
- 4.1 depends on Phases 1-3; 4.2-4.3 depend on 4.1; 4.4 depends on all prior tasks.

## Recommended Apply Batches

- Batch 1: 1.1, 1.2, 2.1
- Batch 2: 2.2, 2.3, 3.1, 3.3
- Batch 3: 3.2, 4.1, 4.2, 4.3, 4.4
