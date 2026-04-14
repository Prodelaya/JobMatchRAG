# Tasks: UV Bootstrap Alignment

## Phase 1: Bootstrap documentation alignment

- [x] 1.1 Update `README.md` with a minimal local setup section using `uv venv .venv` and `uv pip install -e .[dev]`, explicitly framing it as recommended bootstrap guidance.
- [x] 1.2 Extend `AGENTS.md` to mention the same `uv + .venv` bootstrap path while preserving the existing `.venv/bin/python -m ...` local verification contract unchanged.
- [x] 1.3 Review both docs together so they use the same wording for the preserved contract and explicitly exclude `uv sync`, `uv run`, lockfiles, hooks, CI, Docker, runtime, and functional scope.

## Phase 2: Roadmap and change consistency

- [x] 2.1 Update `docs/architecture/vertical-roadmap.md` to insert `uv-bootstrap-alignment` after `project-tooling-bootstrap` and move `source-ingestion-framework` to the next position.
- [x] 2.2 In the same roadmap entry, describe `uv-bootstrap-alignment` as a documentation/bootstrap alignment mini-change only, not a functional ingestion vertical.
- [x] 2.3 Final consistency check: confirm `openspec/config.yaml` still publishes `.venv/bin/python -m ...`, the changed docs match the accepted spec scenarios, and no extra files or tooling changes were introduced.
