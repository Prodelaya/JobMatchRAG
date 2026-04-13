# AGENTS.md

## Project context

JobMatchRAG is a personal job-intelligence system for Pablo Laya. This repository uses living documentation as source of truth. The foundation pack is already closed; archived docs are historical reference only.

## Source-of-truth docs

| File | Purpose | Update when... |
| --- | --- | --- |
| `docs/PRD-JobMatchRAG.md` | Product framing, V1 scope, public visibility, Telegram baseline, recruiter-chat role | product scope, audience, visibility, or core promise changes |
| `docs/architecture/system-overview.md` | System shape, boundaries, canonical pipeline, module map | architecture boundaries or pipeline stages change |
| `docs/architecture/domain-data-overview.md` | Core entities, lifecycle, canonicalization/republication rules, evidence model | domain model or lifecycle rules change |
| `docs/architecture/ingestion-and-sources.md` | Source contract, onboarding policy, run/error model | source framework or ingestion governance changes |
| `docs/architecture/scoring-foundation.md` | Hard filters, scoring flow, thresholds, explainability contract | scoring rules, thresholds, or LLM adjustment policy changes |
| `docs/operations/policies-and-controls.md` | Retention, backups, degradation order, admin policy | operational controls or retention rules change |
| `docs/operations/observability-and-security.md` | Metrics, alerts, auditability, protected-surface controls | observability/security baseline changes |
| `docs/product/recruiter-chat.md` | Recruiter-chat purpose, limits, allowed scope | recruiter-chat behavior or boundaries change |
| `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` | Real pending decisions only | a pending item is resolved or a new real open question appears |

## Continuous update rule

If a change modifies a documented decision, contract, policy, threshold, boundary, or flow, update the corresponding living document in the same change. If that cannot happen, leave an explicit blocking follow-up instead of letting docs drift.

## Local verification

- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m mypy src`
- `.venv/bin/python -m pytest`

## Do not

- Do not use archived docs as source of truth.
- Do not reopen closed foundations without an explicit new change.
- Do not leave living docs outdated after changing the system.
- Do not expand small changes with unrelated scope.
