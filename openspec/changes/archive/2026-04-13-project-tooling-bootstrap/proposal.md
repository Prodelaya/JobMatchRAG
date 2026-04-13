# Proposal: Project Tooling Bootstrap

## Intent

Materializar el baseline ya decidido (Python + `pytest` + `ruff` + `mypy`) en un bootstrap ejecutable mínimo. Este change se separa del foundation pack porque aquel cerró decisiones documentales; acá recién se crea el primer harness verificable que desbloquea la primera vertical (`source-ingestion-framework`) sin mezclar runtime real.

## Scope

### In Scope
- Crear `openspec/config.yaml` con comandos mínimos para `verify`.
- Crear `pyproject.toml` con metadata/config centralizada para `pytest`, `ruff` y `mypy`.
- Crear package raíz mínimo en `src/jobmatchrag/` y smoke test mínimo en `tests/`.

### Out of Scope
- CI, `pre-commit`, Docker, Makefile, lockfiles y `AGENTS.md`.
- Runtime real de FastAPI/Celery, adapters de ingesta o lógica vertical.

## Capabilities

### New Capabilities
- `project-tooling-bootstrap`: baseline ejecutable mínima del repo para validación estática y tests smoke antes de la primera vertical.

### Modified Capabilities
- None.

## Approach

Aplicar la opción explorada de **minimal executable Python baseline**: poco scope, pero con package y test reales para que `apply`/`verify` no sean nominales. Esto mantiene separadas las decisiones de plataforma ya archivadas de la infraestructura mínima necesaria para empezar a ejecutar verticales.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/config.yaml` | New | Config SDD con comandos mínimos de verify |
| `pyproject.toml` | New | Metadata y config de tooling Python |
| `src/jobmatchrag/` | New | Package raíz mínimo importable |
| `tests/` | New | Smoke test mínimo del baseline |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Bootstrap demasiado nominal | Med | Exigir package + smoke test reales |
| Scope creep de developer platform | High | Dejar fuera CI, hooks, Docker y runtime |
| `mypy` genere ruido temprano | Med | Configurar targets mínimos sobre `src/` |

## Rollback Plan

Revertir el change completo eliminando archivos de bootstrap si bloquea la vertical. No toca datos, runtime ni specs de negocio.

## Dependencies

- Exploración `openspec/changes/project-tooling-bootstrap/exploration.md`
- Foundation archivada `decision-foundation-pack`

## Success Criteria

- [ ] Existe un baseline ejecutable mínimo con `openspec/config.yaml`, `pyproject.toml`, `src/jobmatchrag/` y `tests/`.
- [ ] El change deja explícito que `source-ingestion-framework` arranca sobre tooling ya materializado, no sobre decisiones documentales.
- [ ] Quedan fuera de scope CI, hooks, Docker, Makefile, lockfiles, runtime real y `AGENTS.md`.
