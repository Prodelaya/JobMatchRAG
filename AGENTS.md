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
| `docs/architecture/vertical-roadmap.md` | Recommended order of vertical changes, dependencies, and sequencing rules | roadmap order, dependencies, or change decomposition changes |
| `docs/operations/policies-and-controls.md` | Retention, backups, degradation order, admin policy | operational controls or retention rules change |
| `docs/operations/observability-and-security.md` | Metrics, alerts, auditability, protected-surface controls | observability/security baseline changes |
| `docs/product/recruiter-chat.md` | Recruiter-chat purpose, limits, allowed scope | recruiter-chat behavior or boundaries change |
| `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` | Real pending decisions only | a pending item is resolved or a new real open question appears |

## Continuous update rule

If a change modifies a documented decision, contract, policy, threshold, boundary, or flow, update the corresponding living document in the same change. If that cannot happen, leave an explicit blocking follow-up instead of letting docs drift.

Before opening a new change, clarify the specific gaps of that vertical; if real decisions are still missing, do a brief discovery round before proposal/spec.

When a change starts, finishes, splits, or changes the recommended sequence, update `docs/architecture/vertical-roadmap.md` in the same change so the current status and next recommended change stay visible.

When a pending decision is resolved or a supposed open question is no longer real, update `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` in the same change so it stays limited to true pending items only.

If a change creates, replaces, or archives a source-of-truth document, update the living-doc index in `AGENTS.md` in the same change.

Before closing a change, explicitly review whether `docs/PRD-JobMatchRAG.md`, architecture docs, operations docs, `docs/architecture/vertical-roadmap.md`, or `docs/Open-Questions-Architecture-Decisions-JobMatchRAG.md` need updates; if yes, update them in the same change.

## Local verification

Recommended local bootstrap:

- `uv venv .venv`
- `uv pip install -e .[dev]`

This recommended local bootstrap preserves the existing `.venv/bin/python -m ...` verification contract.
It does not adopt `uv sync`, `uv run`, lockfiles, hooks, CI, Docker, runtime, or functional scope changes.

- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m mypy src`
- `.venv/bin/python -m pytest`

## External docs

- For external library or framework documentation, verify first with Context7 via MCP before assuming APIs or behavior; if Context7 is unavailable or insufficient, use the official docs.
- Useful Context7 flow: resolve the library ID first, then query docs. Likely useful libraries here include FastAPI, Celery, Next.js, and Vercel AI SDK if those stacks are adopted.

## Do not

- Do not use archived docs as source of truth.
- Do not reopen closed foundations without an explicit new change.
- Do not leave living docs outdated after changing the system.
- Do not expand small changes with unrelated scope.
