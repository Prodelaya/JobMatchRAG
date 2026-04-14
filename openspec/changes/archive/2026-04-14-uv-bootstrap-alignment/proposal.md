# Proposal: UV Bootstrap Alignment

## Intent

Cerrar el gap real de bootstrap local antes de `source-ingestion-framework`: el repo ya verifica con `.venv/bin/python -m ...`, pero todavía no documenta la convención recomendada para crear esa `.venv` usando `uv` sin reabrir el bootstrap completo.

## Scope

### In Scope
- Documentar setup local recomendado con `uv + .venv`.
- Mantener intacto el contrato visible de verify basado en `.venv/bin/python -m ...`.
- Insertar este mini-change en `docs/architecture/vertical-roadmap.md` antes de `source-ingestion-framework`.

### Out of Scope
- `uv sync`, lockfiles, hooks, CI, Docker, runtime y cambios de vertical funcional.
- Migrar verify a `uv run` o redefinir dependencias más allá del extra `dev` existente.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `project-tooling-bootstrap`: ampliar el baseline para que la convención de setup local recomendada quede documentada con `uv venv .venv` y `uv pip install -e .[dev]`, preservando el contrato `.venv`.

## Approach

Aplicar una alineación mínima y práctica: documentar `uv` solo como mecanismo recomendado para crear y poblar `.venv`, sin convertir el repo a un workflow uv-managed. El spec siguiente debería cubrir documentación reproducible y actualización del roadmap, no cambios de runtime ni de verify.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `README.md` | Modified | Setup local recomendado con `uv + .venv` |
| `AGENTS.md` | Modified | Convención local visible sin tocar verify |
| `docs/architecture/vertical-roadmap.md` | Modified | Inserción del mini-change antes de ingesta |
| `openspec/specs/project-tooling-bootstrap/spec.md` | Modified | Delta spec del baseline de bootstrap |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Scope creep hacia workflow uv-managed | Med | Dejar fuera `uv sync`, `uv run`, lockfiles y CI |
| Reabrir bootstrap ya cerrado | Low | Limitar el change a documentación y roadmap |

## Rollback Plan

Revertir los cambios documentales y del roadmap; el repo seguiría funcionando con el contrato `.venv` actual.

## Dependencies

- Exploración `uv-bootstrap-alignment`
- Bootstrap archivado `project-tooling-bootstrap`

## Success Criteria

- [ ] La documentación local recomienda `uv + .venv` sin cambiar el contrato `.venv/bin/python -m ...`.
- [ ] El roadmap muestra este mini-change como habilitador previo a `source-ingestion-framework`.
- [ ] El scope deja explícitamente fuera `uv sync`, lockfiles, hooks, CI, Docker, runtime y cambios funcionales.
