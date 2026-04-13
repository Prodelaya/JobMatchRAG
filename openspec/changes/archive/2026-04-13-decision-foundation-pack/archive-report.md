# Archive Report: Decision Foundation Pack

**Change**: decision-foundation-pack  
**Mode**: hybrid  
**Date**: 2026-04-13  
**Status**: archived

## Artifact Traceability

| Artifact | Engram observation ID | Filesystem path |
|---|---:|---|
| proposal | 292 | `openspec/changes/archive/2026-04-13-decision-foundation-pack/proposal.md` |
| spec | 307 | `openspec/changes/archive/2026-04-13-decision-foundation-pack/specs/*/spec.md` |
| design | 312 | `openspec/changes/archive/2026-04-13-decision-foundation-pack/design.md` |
| tasks | 313 | `openspec/changes/archive/2026-04-13-decision-foundation-pack/tasks.md` |
| apply-progress | 316 | Engram only |
| verify-report | 324 | `openspec/changes/archive/2026-04-13-decision-foundation-pack/verify-report.md` |

## Main Specs Synced

Created the following source-of-truth specs from the accepted delta specs because `openspec/specs/` had no prior materialized main specs:

- `openspec/specs/product-definition-guardrails/spec.md`
- `openspec/specs/platform-foundation-decisions/spec.md`
- `openspec/specs/ingestion-governance/spec.md`
- `openspec/specs/offer-canonicalization-baseline/spec.md`
- `openspec/specs/scoring-calibration-baseline/spec.md`
- `openspec/specs/cost-observability-controls/spec.md`

## Documentation Closure

- Archived the transitional blueprint physically under `docs/archive/Architecture-Execution-Blueprint-JobMatchRAG.md` so it no longer competes with the active foundation docs.
- Kept `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` as the live backlog for unresolved product naming, recruiter-chat placement, public metrics depth/cadence, and later RAG-detail decisions.
- Recorded the execution sequence as `project-tooling-bootstrap` first, then `source-ingestion-framework`.

## Deferred Warnings (Accepted Out of Scope)

- `openspec/config.yaml` remains absent.
- No automated test/build harness exists yet.

These tooling warnings were explicitly deferred by user decision to the future change `project-tooling-bootstrap` and are not reopened in this archive step.

## Archive Verification

- [x] Main specs updated in `openspec/specs/`
- [x] Transitional blueprint archived physically outside active docs root
- [x] Active backlog doc remains limited to unresolved items only
- [x] Change folder moved to `openspec/changes/archive/2026-04-13-decision-foundation-pack/`

## Recommended Next Changes

1. `project-tooling-bootstrap`
2. `source-ingestion-framework`
