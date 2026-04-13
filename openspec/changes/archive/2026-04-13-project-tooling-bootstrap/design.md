# Design: Project Tooling Bootstrap

## Technical Approach

Materializar un baseline Python mínimo pero ejecutable, alineado con la proposal y el spec: `openspec/config.yaml` define el contrato de verify; `pyproject.toml` concentra metadata y config de `pytest`/`ruff`/`mypy`; `src/jobmatchrag/__init__.py` crea el namespace importable; `tests/test_smoke.py` prueba ese namespace. El objetivo es dejar a `source-ingestion-framework` arrancando sobre tooling real, no sobre bootstrap pendiente.

## Architecture Decisions

| Decision | Options | Choice | Rationale |
|---|---|---|---|
| Packaging layout | Flat root / `src/` layout | `src/jobmatchrag/` | Aísla imports del código fuente, le da target claro a `mypy`, y escala mejor cuando entren verticales. |
| Tooling config | Archivos separados / `pyproject.toml` único | `pyproject.toml` único | Mantiene bootstrap chico, centraliza convenciones y evita dispersar config prematuramente. |
| Verify contract | Comandos implícitos / comandos explícitos en OpenSpec | `openspec/config.yaml` con `pytest`, `ruff`, `mypy` | Hace reutilizable el entrypoint de verificación para cambios siguientes. |
| Smoke scope | Test vacío / import smoke | Test de import y versión/nombre del paquete | Verifica que `pytest` ejecute algo real sin introducir runtime ni fixtures innecesarias. |
| Scope boundary | Incluir platform extras / bootstrap mínimo | Excluir CI, hooks, Docker, Makefile, lockfiles, runtime, `AGENTS.md` | Evita scope creep y mantiene el change enfocado en destrabar la primera vertical. |

## Data Flow

`openspec/config.yaml` -> invoca verify commands -> tooling lee `pyproject.toml` -> `pytest` ejecuta `tests/test_smoke.py` -> test importa `jobmatchrag` desde `src/`.

`source-ingestion-framework` reutiliza el mismo contrato:

`new code in src/` -> mismo `pytest` / `ruff` / `mypy` -> expansión incremental sin redefinir bootstrap.

## File Changes

| File | Action | Description |
|---|---|---|
| `openspec/changes/project-tooling-bootstrap/design.md` | Create | Diseño técnico del bootstrap mínimo. |
| `openspec/config.yaml` | Create | Config SDD con reglas mínimas y comandos verify explícitos. |
| `pyproject.toml` | Create | Metadata del proyecto y config centralizada de `pytest`, `ruff` y `mypy`. |
| `src/jobmatchrag/__init__.py` | Create | Namespace raíz importable, sin runtime FastAPI/Celery. |
| `tests/test_smoke.py` | Create | Smoke test mínimo que valida import del paquete. |

## Interfaces / Contracts

```yaml
# openspec/config.yaml (relevante)
rules:
  verify:
    test_command: "python -m pytest"
    build_command: ""
    coverage_threshold: 0
verify:
  - python -m ruff check .
  - python -m mypy src
  - python -m pytest
```

```python
# src/jobmatchrag/__init__.py
__all__ = ["__version__"]
__version__ = "0.1.0"
```

El smoke test debe importar `jobmatchrag` y afirmar que el paquete expone el símbolo mínimo esperado. No debe crear app factories, workers ni adapters.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Import básico del paquete | `tests/test_smoke.py` verifica import y símbolo mínimo. |
| Integration | Contrato de verify | `openspec/config.yaml` referencia comandos que operan sobre los archivos creados. |
| E2E | None | Fuera de scope en este bootstrap. |

## Migration / Rollout

No migration required. Rollout secuencial: crear config OpenSpec, crear `pyproject.toml`, crear package raíz, crear smoke test. Con eso el repo ya queda listo para que `source-ingestion-framework` solo agregue código vertical y amplíe tests/lint/types sobre la misma base.

## Open Questions

- [ ] Ninguna bloqueante; el change queda listo para `sdd-tasks`.
