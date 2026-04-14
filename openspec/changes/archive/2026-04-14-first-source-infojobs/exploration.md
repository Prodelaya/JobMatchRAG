## Exploration: first-source-infojobs

### Current State
The living docs already close the shared ingestion foundation, confirm InfoJobs as the first production source, and define the run/error/checkpoint/guardrail contract. What remains open is not framework design but a small set of InfoJobs-specific operating choices needed to keep the first adapter scoped and proposal-ready.

### Affected Areas
- `docs/architecture/ingestion-and-sources.md` — fixes the common adapter/run contract and leaves provider-specific choices to this vertical.
- `docs/sources/infojobs-api-reference.md` — documents the real InfoJobs endpoint behavior, payload differences, filters, pagination, and quirks that still need vertical-level decisions.
- `docs/architecture/domain-data-overview.md` — requires raw traceability, checkpoint semantics, and preservation of source evidence.
- `docs/architecture/vertical-roadmap.md` — marks `first-source-infojobs` as the next vertical and allows a brief discovery round when real gaps remain.

### Approaches
1. **Go straight to proposal with implicit defaults** — assume sensible adapter choices now and refine later.
   - Pros: fastest path to proposal.
   - Cons: high chance of mixing scope, hiding decisions, or baking accidental InfoJobs behavior into the wrong layer.
   - Effort: Low

2. **Run a mini discovery for the remaining InfoJobs-specific choices** — close only the operational gaps that shape the first adapter boundary.
   - Pros: keeps scope tight, avoids re-opening foundations, and gives proposal/spec a clean decision baseline.
   - Cons: adds a short interactive step before proposal.
   - Effort: Low

### Recommendation
Run a mini discovery first. The foundation is already closed, but the first concrete adapter still needs a few explicit provider-level choices: pull depth, initial source-side filtering, checkpoint/window semantics, and minimum raw preservation/operational limits. Those are small decisions, yet they materially shape the proposal.

### Risks
- Skipping discovery may blur what is IN vs OUT for `first-source-infojobs` and accidentally pull normalization/scoring concerns forward.
- Treating `sinceDate` or InfoJobs pagination as canonical checkpoint logic would conflict with the already-closed ingestion foundation.
- Assuming detail payload fully replaces list payload would break raw traceability because the docs explicitly state list/detail shapes differ.

### Ready for Proposal
No — a short discovery is still needed to close about 4 provider-specific scope decisions before `sdd-propose`.
