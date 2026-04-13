# Tasks: Project Tooling Bootstrap

## Phase 1: Verify contract foundation

- [x] 1.1 Create `openspec/config.yaml` with minimal SDD metadata plus explicit verify commands for `python -m ruff check .`, `python -m mypy src`, and `python -m pytest`.
- [x] 1.2 Set `openspec/config.yaml` `rules.verify` values so later changes can reuse `test_command`, keep `build_command` empty, and preserve zero coverage requirements for this bootstrap.

## Phase 2: Python baseline scaffold

- [x] 2.1 Create root `pyproject.toml` with project metadata and centralized `pytest`, `ruff`, and `mypy` configuration for the bootstrap package.
- [x] 2.2 Scope `pyproject.toml` static analysis to `src/jobmatchrag` so early `mypy` runs stay targeted and do not require runtime modules.
- [x] 2.3 Create `src/jobmatchrag/__init__.py` exposing only the minimal root namespace symbol (`__version__`) and no FastAPI, Celery, or ingestion runtime code.

## Phase 3: Smoke harness

- [x] 3.1 Create `tests/test_smoke.py` that imports `jobmatchrag` and asserts the package exposes the expected minimal symbol.
- [x] 3.2 Keep the smoke test boundary explicit: no fixtures, no app factories, no workers, and no vertical behavior beyond package import verification.

## Phase 4: Task closure and scope guard

- [x] 4.1 Re-read `openspec/changes/project-tooling-bootstrap/tasks.md` after implementation and mark completed checklist items only for the four bootstrap artifacts above.
- [x] 4.2 Verify the final change leaves CI, `pre-commit`, Docker, Makefile, lockfiles, runtime real, and `AGENTS.md` out of scope before handing off to `sdd-verify`.

## Dependencies

- Phase 1 -> required before all later phases because it defines the verify contract.
- Phase 2 -> depends on Phase 1 and must finish before the smoke harness can target the package.
- Phase 3 -> depends on Phase 2 because the test imports `jobmatchrag`.
- Phase 4 -> depends on all prior phases.

## Recommended Apply Batches

1. **Batch 1:** Phase 1 + Phase 2 (`openspec/config.yaml`, `pyproject.toml`, `src/jobmatchrag/__init__.py`).
2. **Batch 2:** Phase 3 + Phase 4 (`tests/test_smoke.py` plus checklist completion and scope confirmation).
