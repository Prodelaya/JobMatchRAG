# JobMatchRAG

JobMatchRAG is a personal job-intelligence system for Pablo Laya. Its V1 goal is to capture offers, filter hard incompatibilities, consolidate duplicates, compute an explainable score, and expose the result publicly as a living portfolio artifact.

## Current status

- documentation foundation: closed
- Python tooling bootstrap: closed
- local bootstrap alignment to `uv + .venv`: closed
- next recommended vertical: `source-ingestion-framework`

## Source of truth

The repository uses living documentation as source of truth. The most relevant entry points are:

- `docs/PRD-JobMatchRAG.md` — product framing and V1 scope
- `docs/architecture/system-overview.md` — system shape, boundaries and pipeline
- `docs/architecture/vertical-roadmap.md` — recommended change order and next vertical
- `AGENTS.md` — project working rules and living-doc maintenance expectations

## Recommended local bootstrap

Use this minimal bootstrap flow to prepare the local `.venv`:

1. `uv venv .venv`
2. `uv pip install -e .[dev]`

This recommended local bootstrap preserves the existing `.venv/bin/python -m ...` verification contract.
It does not adopt `uv sync`, `uv run`, lockfiles, hooks, CI, Docker, runtime, or functional scope changes.

## Local verification

- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m mypy src`
- `.venv/bin/python -m pytest`
