# Design: Decision Foundation Pack

## Technical Approach

Convert the current single blueprint into a transversal foundation pack: product framing in `docs/PRD-JobMatchRAG.md`, architectural backbone in `docs/architecture/*.md`, operational guardrails in `docs/operations/*.md`, and recruiter-chat framing in `docs/product/recruiter-chat.md`. This change defines shared boundaries, contracts, and lifecycle rules that future vertical changes must consume without re-deciding foundations.

## Architecture Decisions

| Decision | Options | Choice | Rationale |
|---|---|---|---|
| System shape | Microservices / layered monolith / modular monolith | Modular monolith on FastAPI + Celery | Matches low-cost V1, shared data model, and strong coupling across ingestion→canonicalization→scoring→publication. |
| Foundation scope | Build verticals now / define transversal base first | Foundation first | Prevents each vertical from inventing its own contracts, data stages, and ops rules. |
| Documentation model | Keep mega-blueprint / split by concern | Split into 8 target docs | Makes product, architecture, scoring, ingestion, and operations independently evolvable and auditable. |
| Pipeline contract | Source-specific flows / canonical staged flow | `source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified` | Preserves traceability and allows recalculation without corrupting history. |
| Source integration | Ad hoc adapters / common contract | Common adapter contract per source | Lets InfoJobs land first without coupling future sources to V1 quirks. |
| Hybrid scoring | LLM-first / rules-only / rules+LLM | Hard filters + rules + bounded LLM adjustment | Keeps cost and auditability under control while allowing semantic uplift. |

## Data Flow

`SourceAdapter.fetch()` -> `RawOfferSnapshot` -> `NormalizedOffer` -> `CanonicalOffer + OfferEvidence` -> `EligibilityGate` -> `RuleScore` -> `LLMAdjustment?` -> `FinalScore/Status` -> `DashboardProjection` + `TelegramNotification`

Cross-cutting controls wrap every stage: `RunRecord`, retention class, metrics, error policy, and admin-triggered reprocessing.

## File Changes

| File | Action | Description |
|---|---|---|
| `openspec/changes/decision-foundation-pack/design.md` | Create | Technical design for the transversal foundation. |
| `docs/PRD-JobMatchRAG.md` | Modify | Keep product goals, V1 framing, public visibility, and explicit out-of-scope. |
| `docs/architecture/system-overview.md` | Create | Boundaries, modular-monolith shape, end-to-end pipeline, and module map. |
| `docs/architecture/domain-data-overview.md` | Create | Core entities, stage transitions, evidence model, and future `candidate_id` boundary. |
| `docs/architecture/scoring-foundation.md` | Create | Eligibility gates, rule score, LLM adjustment limits, thresholds, and explainability contract. |
| `docs/architecture/ingestion-and-sources.md` | Create | Source registry, adapter contract, run model, and source onboarding policy. |
| `docs/operations/policies-and-controls.md` | Create | Retention, backups, degradation order, and admin/security policy. |
| `docs/operations/observability-and-security.md` | Create | Metrics, alerts, audit trail, and protected-surface controls. |
| `docs/product/recruiter-chat.md` | Create | Secondary-product framing and limits, without full RAG implementation detail. |
| `docs/Architecture-Execution-Blueprint-JobMatchRAG.md` | Modify then archive | Redistribute resolved sections into target docs; leave only migration note until archived. |
| `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` | Modify | Retain only unresolved items (public naming, chat placement, advanced public metrics, later RAG details). |

## Interfaces / Contracts

```text
SourceAdapter
- source_key
- fetch(run_context) -> RawOfferSnapshot[]
- normalize(raw) -> NormalizedOffer
- classify_error(error) -> retryable | terminal

Canonicalization
- match(normalized) -> canonical_offer_id?
- consolidate(matches) -> CanonicalOffer + OfferEvidence[] + confidence
- detect_republication(canonical, normalized) -> bool

ScoringFlow
- check_eligibility(canonical) -> pass | reject(reason[])
- compute_rule_score(canonical) -> score_breakdown
- apply_llm_adjustment(score_breakdown, evidence) -> bounded_delta
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Adapter contract, canonicalization rules, eligibility/scoring math | Contract fixtures and deterministic cases |
| Integration | End-to-end stage transitions and run traceability | Pipeline tests over raw→published projections |
| E2E | Public dashboard visibility, admin protection, Telegram trigger thresholds | Minimal smoke flows after vertical implementation |

## Migration / Rollout

1. Treat `docs/Architecture-Execution-Blueprint-JobMatchRAG.md` as source inventory, not source of truth. 2. Redistribute sections into the target docs above. 3. Update `Open-Questions...` to keep only real pending decisions. 4. Future vertical changes MUST reference these global docs and only define vertical-specific design/detail. Foundation owns contracts, stage model, guardrails, and ops policies; verticals own concrete adapters, schemas, APIs, UI flows, and execution logic.

## Open Questions

- [ ] Public product name and branding.
- [ ] Exact recruiter-chat placement in the public site.
- [ ] Depth and cadence of public-facing metrics beyond basic freshness/activity.
