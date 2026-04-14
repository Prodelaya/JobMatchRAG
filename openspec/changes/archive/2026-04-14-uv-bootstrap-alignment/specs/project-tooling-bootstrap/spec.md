# Delta for project-tooling-bootstrap

## ADDED Requirements

### Requirement: Recommended local uv bootstrap documentation

The system MUST document a recommended local bootstrap flow that creates `.venv` with `uv venv .venv` and installs project dependencies with `uv pip install -e .[dev]`. That guidance SHALL preserve the visible verification contract based on `.venv/bin/python -m ...` and MUST NOT redefine the project as a uv-managed workflow.

#### Scenario: Local setup is documented with uv and .venv

- GIVEN a contributor needs to prepare the repository locally
- WHEN they read the local bootstrap guidance
- THEN the documented steps include `uv venv .venv` and `uv pip install -e .[dev]`
- AND the guidance keeps `.venv` as the expected environment path

#### Scenario: Verify contract remains unchanged

- GIVEN the bootstrap alignment change is reviewed
- WHEN the documented verification entrypoints are checked
- THEN the project still uses `.venv/bin/python -m ruff check .`, `.venv/bin/python -m mypy src`, and `.venv/bin/python -m pytest`
- AND the change does not require `uv run`, `uv sync`, or lockfiles

### Requirement: Roadmap sequencing reflects bootstrap alignment

The system MUST update `docs/architecture/vertical-roadmap.md` to show `uv-bootstrap-alignment` as the recommended mini-change inserted after `project-tooling-bootstrap` and before `source-ingestion-framework`. The roadmap entry SHALL describe it as a documentation/bootstrap alignment change and MUST NOT present it as a functional ingestion vertical.

#### Scenario: Inserted change appears before ingestion framework

- GIVEN a contributor reviews the living roadmap
- WHEN they inspect the ordered list of changes
- THEN `uv-bootstrap-alignment` appears after `project-tooling-bootstrap`
- AND `source-ingestion-framework` remains the next functional vertical after that alignment step

#### Scenario: Scope remains explicitly narrow in sequencing docs

- GIVEN the roadmap explains why the new change exists
- WHEN the contributor reads its purpose
- THEN it is described as aligning local bootstrap documentation to `uv + .venv`
- AND it excludes hooks, CI, Docker, runtime, lockfiles, and other functional scope expansion
