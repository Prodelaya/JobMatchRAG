# Design: Source Search Strategy

## Technical Approach

Keep canonical semantics as product authority by inserting a provider-agnostic `capture profile` ahead of provider adapters. The profile owns bilingual search families, canonical target filters, ambiguity policy, and degradation rules. A canonical execution planner derives provider pushdown opportunities, but unsupported semantics always fall back to post-fetch filtering. Scoring and bounded LLM steps remain strictly downstream consumers of already-filtered survivors.

## Architecture Decisions

| Decision | Options | Choice | Rationale |
|---|---|---|---|
| Semantic authority | Provider params vs canonical profile | Canonical profile | Preserves product policy even when providers expose only partial filters. |
| Execution split | Provider-only vs hybrid pushdown/post-fetch | Hybrid | Narrows volume early without surrendering canonical rules. |
| Ambiguity policy | Exclude on hints vs preserve unless explicit | Preserve unless explicit/reliable | Matches product requirement that ambiguity survives for explanation and later ranking. |
| AVE reference | Ad hoc external lookup vs in-repo curated dataset | In-repo curated evidence dataset | Makes the initial eligibility reference deterministic, reviewable, versioned, and available offline. |
| Consultancy evidence | Text-only vs company-list-only vs mixed | Mixed evidence with ambiguity preserved | Explicit language is the only hard-exclusion trigger; company knowledge improves review without overblocking. |

## Data Flow

```text
CaptureProfile
   │
   ├─ search_families
   ├─ target_filters
   └─ degradation_rules
          │
          ▼
CanonicalExecutionPlanner
   │ classifies each filter as pushdown | post_fetch | ambiguity_only
   ▼
ProviderExecutionPlan ──> infojobs-search-mapping ──> InfoJobs request/checkpoint flow
   │                                                  │
   └──────────── raw offers + derived provider params ┘
                         │
                         ▼
PostFetchCanonicalFilterEngine
   │
   ├─ AVEHybridEligibilityEvaluator ──> curated hybrid-city dataset
   ├─ ConsultancyEvidenceEvaluator ──> explicit text signals + provisional company dataset
   └─ CanonicalFilterOutcome[]
                         │
                         ▼
Eligible survivors ──> normalization/canonicalization ──> scoring ──> bounded LLM
```

## Sequence Diagram

```text
Job config
  -> Capture profile builder: define canonical families + target filters
  -> Canonical execution planner: split pushdown vs post-fetch
  -> Provider adapter: emit derived InfoJobs params only
  -> Provider discovery: fetch raw offers
  -> Post-fetch filter engine: evaluate canonical rules
      -> AVE evaluator: resolve city evidence version + attendance rule
      -> Consultancy evaluator: combine text evidence + company hints
  -> Outcome tracer: persist passed/excluded/ambiguous with evidence refs
  -> Downstream pipeline: normalize, score, optionally enrich with LLM
```

## Curated Reference Datasets

### AVE / Hybrid-Eligibility Dataset

Conceptually, the AVE reference is a versioned in-repo curated dataset owned by JobMatchRAG, seeded from the user-provided April 2026 city list and treated as the initial evidence baseline for hybrid eligibility outside Madrid.

Recommended structure:

| Path | Role |
|---|---|
| `src/jobmatchrag/source_ingestion/reference/hybrid_cities/manifest.yaml` | Dataset identity, seed provenance, semantic version, effective date. |
| `src/jobmatchrag/source_ingestion/reference/hybrid_cities/cities.yaml` | Curated city/station records consumed at runtime. |
| `tests/fixtures/source_ingestion/hybrid_cities/` | Stable fixtures for versioned evaluator tests. |

Record model:

```text
HybridCityRecord
- city_key
- display_name
- province?
- station_name?
- supports_monthly_hybrid: bool
- aliases: [str]
- seed_source: user-city-list-apr-2026
- provenance_note
- dataset_version
- effective_from
- reviewed_at
- status: active | provisional | deprecated
```

Versioning and provenance rules:

- `manifest.yaml` carries `dataset_version`, `seed_source`, `seeded_at`, and changelog notes.
- Every `CanonicalFilterOutcome` for hybrid geography stores the `dataset_version` actually consulted.
- Offer evaluations are immutable with respect to the version used at evaluation time; later dataset edits do not silently rewrite past outcomes.
- Manual curation is the only write path in this vertical; external refresh/import is explicitly deferred.

Consumption boundary:

- Runtime logic loads the dataset through a read-only reference loader inside `search_strategy.py`.
- The AVE evaluator uses this dataset only for hybrid eligibility checks that already have explicit attendance `<3 days/month`.
- Madrid onsite/remote-in-Spain rules remain canonical policy and do not depend on the dataset.
- Missing city, unmatched aliases, deprecated entries, or absent attendance details produce `ambiguous`, never hard exclusion.

### Provisional Known-Companies Dataset

The company list is a second in-repo curated reference, intentionally narrower than a provider/company master. It is a provisional evidence source for consultancy/body-shopping suspicion, not an authoritative exclusion registry.

Recommended structure:

| Path | Role |
|---|---|
| `src/jobmatchrag/source_ingestion/reference/company_signals/manifest.yaml` | Dataset identity, version, curator notes. |
| `src/jobmatchrag/source_ingestion/reference/company_signals/known_consultancies.yaml` | Normalized company aliases and suspicion metadata. |
| `tests/fixtures/source_ingestion/company_signals/` | Fixtures covering ambiguity and explicit-exclusion combinations. |

Record model:

```text
KnownCompanySignal
- company_key
- canonical_name
- aliases: [str]
- signal_kind: consultancy | body-shopping | recruiter-outsourcing
- confidence: low | medium
- source_note
- dataset_version
- reviewed_at
- status: active | provisional | deprecated
```

Maintenance boundary:

- This dataset is curated manually and versioned exactly like the hybrid-city dataset.
- It stores only normalized names/aliases plus suspicion metadata; it does not become a CRM, enrichment source, or hard blacklist.
- A hit from this dataset contributes evidence for review and traceability, but without explicit/reliable textual signals the final status remains `ambiguous`.

## Evidence Combination Design

### AVE / Hybrid Eligibility

```text
Inputs:
- modality evidence
- attendance evidence
- normalized city text
- HybridCityRecord lookup result

Rules:
1. onsite outside Madrid => excluded
2. remote anywhere in Spain => passed
3. hybrid in Madrid => passed only if attendance <3 days/month, else excluded/ambiguous per explicitness
4. hybrid outside Madrid =>
   - attendance explicit and <3 days/month + active/provisional city record => passed
   - attendance explicit and >=3 days/month => excluded
   - city lookup missing/low-confidence or attendance missing => ambiguous
```

### Consultancy / Body-Shopping

```text
Evidence sources:
- explicit/reliable textual signals from title, description, employer text, recruiter phrasing
- provisional company signal matches by normalized company name / alias

Decision policy:
- explicit/reliable textual signal => excluded
- company signal match + no explicit/reliable textual signal => ambiguous
- weak text hint only => ambiguous
- no evidence => passed
```

This preserves the core boundary: only explicit/reliable semantics can hard-exclude. Curated company knowledge improves detection coverage without letting metadata-only heuristics overrule product policy.

## Interfaces / Contracts

```text
CaptureProfile
- search_families: [SearchFamily]
- target_filters: [CanonicalTargetFilter]
- degradation_policy: DegradationPolicy

CanonicalFilterOutcome
- filter_key
- status: passed | excluded | ambiguous
- reason_code
- evidence_refs
- applied_stage: pushdown | post_fetch
- policy_version

EvidenceRef
- evidence_type: hybrid_city_dataset | attendance_text | consultancy_text | company_signal
- locator
- dataset_version?
- confidence

ProviderExecutionPlan
- canonical_profile_ref
- derived_provider_params
- pushed_down_filters
- post_fetch_filters
- degradation_notes

ReferenceDatasetSnapshot
- dataset_key: hybrid_cities | company_signals
- dataset_version
- loaded_at
```

Handoff rules:

- `infojobs-search-mapping` receives only `ProviderExecutionPlan`, never raw product intent.
- Post-fetch filtering emits `CanonicalFilterOutcome[]` plus evidence refs and dataset versions.
- Scoring can consume ambiguity/explanation metadata but cannot overturn hard exclusions.
- LLM sees only already-eligible survivors and their bounded explanation context.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `openspec/changes/source-search-strategy/design.md` | Update | Revised technical design for closed evidence risks. |
| `src/jobmatchrag/source_ingestion/search_strategy.py` | Create | Canonical planner, filter engine, AVE/company evaluators, dataset loaders. |
| `src/jobmatchrag/source_ingestion/reference/hybrid_cities/manifest.yaml` | Create | Hybrid-city dataset manifest and provenance/version metadata. |
| `src/jobmatchrag/source_ingestion/reference/hybrid_cities/cities.yaml` | Create | Seeded curated city records for hybrid eligibility. |
| `src/jobmatchrag/source_ingestion/reference/company_signals/manifest.yaml` | Create | Provisional company-signal dataset manifest. |
| `src/jobmatchrag/source_ingestion/reference/company_signals/known_consultancies.yaml` | Create | Curated aliases and suspicion metadata for ambiguous company matches. |
| `src/jobmatchrag/source_ingestion/models.py` | Modify | Extend canonical intent and trace models with evidence/dataset versions. |
| `src/jobmatchrag/source_ingestion/contracts.py` | Modify | Type evidence refs, snapshots, and canonical outcome payloads. |
| `src/jobmatchrag/source_ingestion/orchestrator.py` | Modify | Record pushdown boundaries, dataset versions, and ambiguity outcomes per run. |
| `src/jobmatchrag/source_ingestion/infojobs/discovery.py` | Modify | Consume only derived provider params from the execution plan. |
| `src/jobmatchrag/source_ingestion/infojobs_search_mapping.py` | Create (next vertical) | Translate execution plan to InfoJobs params without becoming semantic authority. |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Search-family composition, pushdown classification, AVE evaluator, consultancy evidence combination, dataset alias resolution | Pure strategy tests with versioned fixtures. |
| Integration | `job -> run` trace captures pushed-down filters, post-fetch outcomes, evidence refs, and dataset versions | Orchestrator tests with fake provider plans and curated datasets. |
| Contract | `ProviderExecutionPlan`, `CanonicalFilterOutcome`, and downstream scoring payloads remain stable | Schema/fixture tests. |

## Migration / Rollout

No external storage migration is required. Rollout order:

1. Add reference dataset folders, manifests, and read-only loaders.
2. Introduce canonical planner/filter contracts with evidence refs and dataset snapshots.
3. Update orchestrator tracing and post-fetch evaluators.
4. In the next vertical, connect `infojobs-search-mapping` to the execution-plan contract.

## Resolved Risks

| Former Risk | Resolution |
|---|---|
| AVE reference source/owner unclear | Closed by adopting an in-repo curated hybrid-city dataset seeded from the April 2026 user list, versioned by manifest, and consumed read-only by the hybrid eligibility evaluator. |
| Consultancy detection boundary unclear | Closed by adopting mixed evidence: explicit/reliable text can exclude, provisional company-list matches only add ambiguous evidence. |

## Downstream Documentation Impact & Tradeoffs

Implementation must update `docs/architecture/ingestion-and-sources.md`, `docs/architecture/domain-data-overview.md`, `docs/architecture/scoring-foundation.md`, `docs/architecture/vertical-roadmap.md`, `docs/PRD-JobMatchRAG.md`, `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md`, and `docs/sources/infojobs-api-reference.md` if provider-boundary wording changes. Tradeoff: curated datasets add manual maintenance, but they make eligibility decisions auditable, deterministic, and safely ambiguity-preserving without leaking semantic authority into provider params.
