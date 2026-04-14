# Design: UV Bootstrap Alignment

## Technical Approach

Materializar la alineación como un ajuste documental mínimo sobre el baseline de `project-tooling-bootstrap`: explicitar en `README.md` el bootstrap local con `uv venv .venv` + `uv pip install -e .[dev]`, reflejar la misma convención en `AGENTS.md` sin tocar el contrato de verify, y actualizar `docs/architecture/vertical-roadmap.md` para insertar este mini-change antes de `source-ingestion-framework`.

## Architecture Decisions

| Decision | Options | Choice | Rationale |
|---|---|---|---|
| Adoptar `uv` en este change | 1) seguir sin guía formal 2) `uv + .venv` mínimo 3) `uv` workflow completo (`sync/run`) | Opción 2 | Cierra el gap real de bootstrap sin reabrir foundations ni arrastrar lockfile, CI, Docker o redefinición operativa. |
| Mantener contrato de verify | 1) migrar a `uv run` 2) conservar `.venv/bin/python -m ...` | Opción 2 | `AGENTS.md` y `openspec/config.yaml` ya publican ese contrato; cambiarlo mezclaría tooling con una decisión mayor fuera de scope. |
| Tocar archivos de tooling | 1) modificar `pyproject.toml` / `openspec/config.yaml` 2) dejar tooling intacto y actualizar solo documentación viva | Opción 2 | `pyproject.toml` ya expone `dev`; `openspec/config.yaml` ya define verify. No hay evidencia de un gap técnico que justifique cambios estructurales. |

## Data Flow

Flujo documental, no de runtime:

    Contributor
        │
        ├── reads README.md ────────┐
        ├── reads AGENTS.md ────────┼──→ creates `.venv` with `uv`
        └── reads roadmap ──────────┘
                                      │
                                      └── runs existing `.venv/bin/python -m ...` verify commands

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `openspec/changes/uv-bootstrap-alignment/design.md` | Create | Documentar el approach técnico de este mini-change. |
| `README.md` | Modify | Agregar bootstrap local reproducible con `uv + .venv`; dejar claro que es setup recomendado, no workflow uv-managed. |
| `AGENTS.md` | Modify | Hacer visible la convención de bootstrap local con `uv` preservando el verify contract existente. |
| `docs/architecture/vertical-roadmap.md` | Modify | Insertar `uv-bootstrap-alignment` después de `project-tooling-bootstrap`, marcarlo como mini-change de alineación documental y mover `source-ingestion-framework` a la posición siguiente. |
| `pyproject.toml` | No change | Reusar el extra `dev` ya existente. |
| `openspec/config.yaml` | No change | Mantener intactos los comandos de verify basados en `.venv`. |

## Interfaces / Contracts

No se agregan interfaces de código ni contratos runtime. El único contrato afectado es documental:

- **Bootstrap recomendado:** `uv venv .venv` y `uv pip install -e .[dev]`.
- **Contrato preservado:** `.venv/bin/python -m ruff check .`, `.venv/bin/python -m mypy src`, `.venv/bin/python -m pytest`.
- **Exclusiones explícitas:** `uv sync`, `uv run`, lockfiles, hooks, CI, Docker, runtime y cambios funcionales.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Docs consistency | README y AGENTS exponen la misma convención `uv + .venv` | Revisión de contenido contra spec y proposal. |
| Contract safety | Verify contract sigue igual | Confirmar que `AGENTS.md` y `openspec/config.yaml` mantienen `.venv/bin/python -m ...`. |
| Roadmap integrity | Secuencia actualizada correctamente | Revisar que `uv-bootstrap-alignment` quede antes de `source-ingestion-framework` y con propósito no funcional. |

## Migration / Rollout

No migration required. Es una alineación documental del bootstrap local existente.

## Open Questions

- [ ] None.
