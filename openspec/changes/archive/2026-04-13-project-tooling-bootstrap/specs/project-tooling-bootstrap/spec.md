# Project Tooling Bootstrap Specification

## Purpose
Definir el bootstrap mínimo y verificable del repo para que futuras verticales arranquen sobre tooling ejecutable, no sobre decisiones solo documentales.

## Requirements

### Requirement: OpenSpec verify contract
The system MUST provide `openspec/config.yaml` as the SDD project config. It SHALL define executable verify commands for tests, lint, and type-checking so later changes can reuse the same verification contract.

#### Scenario: Verify commands are discoverable
- GIVEN a contributor reviews the repository baseline
- WHEN opening `openspec/config.yaml`
- THEN the file lists explicit verify commands for `pytest`, `ruff`, and `mypy`

#### Scenario: Verify contract supports future verticals
- GIVEN a later change such as `source-ingestion-framework`
- WHEN it needs a baseline verification entrypoint
- THEN it can reuse the configured verify commands without first inventing project tooling

### Requirement: Python baseline declaration
The system MUST provide a root `pyproject.toml` that declares the Python project baseline. It SHALL centralize the minimal configuration needed for `pytest`, `ruff`, and `mypy`, and SHOULD scope static analysis to the bootstrap package so early noise stays controlled.

#### Scenario: Tooling configuration is centralized
- GIVEN the repository bootstrap is present
- WHEN a contributor inspects Python tooling configuration
- THEN `pyproject.toml` is the single baseline source for project metadata and `pytest`/`ruff`/`mypy` settings

#### Scenario: Type-checking remains targeted
- GIVEN the repository has only bootstrap code
- WHEN `mypy` runs from the configured verify command
- THEN it evaluates the intended bootstrap sources without requiring vertical runtime modules

### Requirement: Importable root package scaffold
The system MUST provide a minimal importable package under `src/jobmatchrag/`. It MUST represent only the project root namespace for future work and MUST NOT imply real FastAPI, Celery, or ingestion runtime behavior.

#### Scenario: Root namespace exists
- GIVEN the bootstrap files are created
- WHEN Python imports `jobmatchrag`
- THEN the import succeeds from the root package scaffold

#### Scenario: Runtime scope stays excluded
- GIVEN the bootstrap change is reviewed
- WHEN inspecting `src/jobmatchrag/`
- THEN only minimal package scaffolding is present and no real FastAPI/Celery runtime or vertical logic is required

### Requirement: Minimal smoke verification harness
The system MUST provide at least one smoke test under `tests/` that validates the baseline package can be exercised by `pytest`. This harness SHALL be minimal but executable, so verification is real rather than nominal.

#### Scenario: Smoke test validates baseline
- GIVEN the bootstrap is installed in the workspace
- WHEN `pytest` runs through the configured verify command
- THEN at least one smoke test executes against the root package successfully

#### Scenario: Bootstrap boundaries stay explicit
- GIVEN the change scope is reviewed
- WHEN checking the bootstrap artifacts
- THEN CI, `pre-commit`, Docker, Makefile, lockfiles, `AGENTS.md`, and real FastAPI/Celery runtime remain out of scope for this baseline
