# Exploration: uv-bootstrap-alignment

### Current State
JobMatchRAG ya tiene un bootstrap Python mínimo y ejecutable: `openspec/config.yaml` y `AGENTS.md` reutilizan comandos `.venv/bin/python -m ...`, `pyproject.toml` ya declara el extra `dev`, y `.gitignore` ya excluye `.venv/`. No hay `uv.lock`, CI, Docker, hooks ni runtime real, y `README.md` todavía no documenta el bootstrap local. El verify report archivado de `project-tooling-bootstrap` dejó como follow-up explícito documentar cómo reproducir el entorno local.

### Affected Areas
- `AGENTS.md` — ya expone el contrato operativo local con `.venv/bin/python -m ...`; podría sumar el paso de bootstrap con `uv` sin tocar el verify contract.
- `README.md` — mejor lugar para documentar el setup local mínimo (`uv venv` + instalación editable con extras dev).
- `docs/architecture/vertical-roadmap.md` — si este mini-change se abre ahora, debe reflejar la inserción antes de `source-ingestion-framework`.
- `pyproject.toml` — solo se tocaría si se cambiara la convención de dependencias; con el `dev` extra actual NO parece necesario.
- `openspec/config.yaml` — NO debería cambiarse si el contrato verify sigue siendo `.venv/bin/python -m ...`.
- `docs/operations/*.md`, `docs/architecture/system-overview.md`, `docs/architecture/ingestion-and-sources.md` — NO deberían tocarse: este change no altera runtime, operación, arquitectura ni governance de ingesta.

### Approaches
1. **Postergar y seguir con `.venv` documentado informalmente** — no abrir change nuevo y dejar `source-ingestion-framework` como siguiente.
   - Pros: cero trabajo inmediato; no toca nada del bootstrap cerrado.
   - Cons: se arrastra una convención incompleta justo antes de empezar una vertical mayor; el follow-up del verify report sigue vivo; `source-ingestion-framework` corre riesgo de mezclar framework de ingesta con setup local.
   - Effort: Low

2. **Mini-change de alineación mínima a `uv + .venv`** — mantener `.venv` como contrato visible, documentar `uv venv .venv` y `uv pip install -e .[dev]`, y actualizar el roadmap si se inserta el change antes de ingesta.
   - Pros: cierra el gap real de bootstrap sin reabrir foundations; reutiliza el `pyproject.toml` actual; evita meter lockfile, CI, Docker, hooks o runtime; deja `source-ingestion-framework` arrancando con setup local claro.
   - Cons: usa la interfaz pip-compatible de `uv`, que la documentación de `uv` no presenta como la convención ideal para proyectos uv-managed; queda como alineación práctica, no como adopción completa de workflow uv.
   - Effort: Low

3. **Adopción completa de workflow uv-managed** — pasar a `uv sync --extra dev` / `uv run ...` y normalizar el proyecto alrededor de `uv` como gestor principal.
   - Pros: queda más alineado con la recomendación actual de `uv` para proyectos; prepara un flujo más reproducible a futuro.
   - Cons: abre preguntas extra sobre `uv.lock`, comandos de verify, posible uso de `uv run`, y expectativas futuras en CI/Docker; eso ya mezcla bootstrap con decisiones más amplias que hoy NO bloquean ingesta.
   - Effort: Medium

### Recommendation
Sí conviene abrir **ahora** un mini-change `uv-bootstrap-alignment`, pero SOLO si se mantiene extremadamente acotado. La mejor opción es la **alineación mínima a `uv + .venv`**: documentar `uv venv .venv` (o `uv venv`, que por defecto crea `.venv`) y luego `uv pip install -e .[dev]`, manteniendo intacto el contrato de verify basado en `.venv/bin/python -m ...`. No recomiendo `uv sync --extra dev` en este change porque empuja al repo hacia el workflow uv-managed y probablemente arrastre lockfile y redefinición de comandos, cosa que hoy no hace falta para destrabar `source-ingestion-framework`.

### Risks
- Si el change intenta migrar también el verify contract a `uv run` o `uv sync`, se mezcla con una decisión de workflow más grande que la necesidad real actual.
- Si se introduce `uv.lock`, CI, hooks, Docker o cambios de runtime, el mini-change pierde foco y reabre el bootstrap cerrado.
- Si no se actualiza `docs/architecture/vertical-roadmap.md` al insertar este change antes de ingesta, la documentación viva queda desalineada con la secuencia real.

### Ready for Proposal
Yes — proponerlo como change pequeño de documentación/convención local. Alcance mínimo: `README.md`, `AGENTS.md` y `docs/architecture/vertical-roadmap.md`; `pyproject.toml` solo si discovery adicional demostrara que el extra `dev` actual no alcanza, cosa que hoy no aparece.
