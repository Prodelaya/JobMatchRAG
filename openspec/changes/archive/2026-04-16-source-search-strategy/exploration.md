## Exploration: source-search-strategy

### Current State
The shared ingestion foundation is already closed: source-side filters are advisory only, the framework preserves run/filter traceability, and InfoJobs currently consumes only provider-native `provider_filters` via `FilterIntent` before preserving the effective listing request in raw handoff. What is still missing is the middle layer between product search intent and provider mapping: a provider-agnostic capture strategy that defines query families, canonical early exclusions, ambiguity/degradation rules, and the handoff contract that `infojobs-search-mapping` will later translate into InfoJobs parameters without turning provider filters into product authority.

### Affected Areas
- `docs/architecture/ingestion-and-sources.md` — fixes that source-side filtering is optimization only and that adapters must not become the canonical policy layer.
- `docs/architecture/domain-data-overview.md` — defines where raw evidence, ambiguity, and later eligibility/scoring handoff must remain traceable.
- `docs/architecture/scoring-foundation.md` — already closes hard-filter-before-score order, but still needs this change to define what can be discarded early at capture time vs deferred as ambiguous.
- `docs/sources/infojobs-api-reference.md` — documents the real InfoJobs search/filter surface that the later mapping change must consume.
- `src/jobmatchrag/source_ingestion/models.py` — `FilterIntent` currently holds only provider-native filters plus a note that canonical eligibility stays internal.
- `src/jobmatchrag/source_ingestion/orchestrator.py` — snapshots and forwards advisory provider filters today, so any new strategy must hand off cleanly into the existing job/run contract.
- `src/jobmatchrag/source_ingestion/infojobs/discovery.py` — currently whitelists provider filters directly into the listing query and does not know about canonical search families yet.
- `docs/architecture/vertical-roadmap.md` / `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` — roadmap already says this is the next vertical, while Open Questions still points at `offer-normalization-canonicalization`, so guidance is currently inconsistent.

### Approaches
1. **Provider-first presets** — encode the search strategy directly as InfoJobs-flavored `provider_filters` bundles now.
   - Pros: fastest path to implementation; reuses current `FilterIntent` shape with minimal new concepts.
   - Cons: couples product intent to InfoJobs too early; makes `infojobs-search-mapping` redundant; weakens the provider-agnostic boundary the roadmap explicitly wants.
   - Effort: Low

2. **Fully canonical search DSL** — define a rich cross-provider query language that also tries to express semantic ambiguity and early eligibility in one layer.
   - Pros: strongest abstraction purity; future sources could map into one unified model.
   - Cons: too ambitious for this point in the roadmap; risks re-implementing eligibility/scoring prematurely; current ingestion code has no place for such a heavy abstraction yet.
   - Effort: High

3. **Capture profile + search families + degradation matrix** — define a small provider-agnostic search artifact with bilingual search families, canonical early-capture filters, ambiguity policy, and explicit degradation rules, then let `infojobs-search-mapping` translate that artifact into provider filters later.
   - Pros: preserves the roadmap split; stays compatible with current ingestion contracts; supports bilingual search, ambiguous-case retention, and provider-specific pragmatism without giving providers canonical authority.
   - Cons: requires one more explicit handoff contract before implementation; some edge semantics (hybrid AVE access, consultancy detection, stale-date reliability) will still depend on later provider mapping and downstream review/scoring evidence.
   - Effort: Medium

### Recommendation
Use **Approach 3**. The change should define a provider-agnostic **capture profile** made of: (a) bilingual search families ordered by value density, with a core family around internal automation + applied AI/LLM/agent integration, a still-valid internal automation family without explicit AI, and an adjacent Odoo family; (b) canonical early-capture filters that only discard explicit mismatches (senior/high-experience roles, clearly incompatible geography/modality, clearly body-shopping consultancies, reliably stale offers >15 days); (c) an ambiguity policy that keeps unclear modality, consultancy, freshness, and semantic-fit cases alive for later review/scoring; and (d) degradation rules that say unsupported provider capabilities must fall back to broader capture plus downstream internal filtering rather than silently narrowing the product intent. That gives `infojobs-search-mapping` a concrete target while keeping provider translation, not product strategy, as the provider-specific concern.

### Risks
- The current code has no first-class canonical search object yet, only `provider_filters`; without an explicit handoff artifact, implementation could accidentally smuggle product policy into provider-native params or opaque metadata.
- Geography/modality rules are partly semantic (`hybrid` outside Madrid only when office attendance is <3 days/month and city access is AVE-friendly), which most providers will not expose structurally; this guarantees a meaningful ambiguous/review bucket and requires careful documentation of what can be filtered early vs later.
- `docs/architecture/scoring-foundation.md` still states seniority exclusion as “por encima de 3 años”, while the clarified search context now uses a semantic senior/high-experience cutoff (5+ years, senior/lead/staff/principal, etc.); the living docs will need alignment in the next write phase to avoid policy drift.
- `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` still recommends `offer-normalization-canonicalization` as the next change, which conflicts with the living roadmap and can mislead later phases if not corrected in the change that formalizes this strategy.
- Provider freshness data may be incomplete or inconsistent; the strategy can define “discard only when reliably older than 15 days”, but later mappings must document which source timestamps are trustworthy enough to enforce that early.

### Ready for Proposal
Yes — the next phase should formalize the capture profile, search-family taxonomy, canonical early-exclusion rules, ambiguity/degradation policy, and the exact handoff boundary to `infojobs-search-mapping`.
