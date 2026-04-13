# Exploration: project-tooling-bootstrap

### Current State
JobMatchRAG sigue en estado docs-first: el repo tiene `docs/`, `openspec/specs/` y un foundation pack archivado, pero no tiene `openspec/config.yaml`, `pyproject.toml`, código Python, ni tests ejecutables. La foundation técnica ya cerró Python + FastAPI + Celery como baseline futura, y el archive del change anterior dejó explícito que el próximo paso debía ser un bootstrap mínimo de tooling antes de arrancar `source-ingestion-framework`.

### Affected Areas
- `openspec/config.yaml` — falta hoy y es la pieza que habilita `sdd-verify` con comandos explícitos.
- `openspec/changes/project-tooling-bootstrap/exploration.md` — artefacto de exploración del change.
- `pyproject.toml` — mejor lugar para declarar metadata mínima del proyecto y centralizar config de `pytest`, `ruff` y `mypy`.
- `src/jobmatchrag/` — conviene dejar un package raíz mínimo para que `mypy` y futuros verticales no arranquen desde cero.
- `tests/` — hace falta un harness mínimo real para que `pytest` no sea puramente declarativo.
- `README.md` — solo sería afectado si hiciera falta documentar comandos mínimos; no parece obligatorio en este change.
- `AGENTS.md` — NO es dependencia directa del bootstrap; puede quedar como change posterior mientras no se necesiten reglas de trabajo para ejecutar tooling.

### Approaches
1. **Ultra-small config-only bootstrap** — agregar solo `openspec/config.yaml` y, como mucho, un `pyproject.toml` sin árbol `src/` ni tests reales.
   - Pros: change muy chico, poco riesgo, casi sin discusión estructural.
   - Cons: deja un verify frágil o vacío; `source-ingestion-framework` todavía tendría que crear la base ejecutable real; el bootstrap corre riesgo de ser nominal y no operativo.
   - Effort: Low

2. **Minimal executable Python baseline** — agregar `openspec/config.yaml`, `pyproject.toml`, un package vacío bajo `src/jobmatchrag/`, y un test smoke mínimo bajo `tests/` para validar `pytest`, `ruff` y `mypy` de verdad.
   - Pros: sigue siendo chico pero ya deja un harness real; desacopla tooling de la vertical de ingesta; prepara un punto de arranque limpio para FastAPI/Celery sin imponer todavía arquitectura runtime completa.
   - Cons: introduce una micro-escaffold de código vacío; requiere decidir convenciones mínimas de layout (`src/` + `tests/`) ahora, aunque todavía no exista lógica de negocio.
   - Effort: Low/Medium

3. **Broader developer-platform bootstrap** — además de lo anterior, sumar `AGENTS.md`, `Makefile`, `pre-commit`, CI, lockfiles y más documentación operativa.
   - Pros: deja más terreno listo de una sola vez.
   - Cons: mezcla concerns, agranda innecesariamente el change, fuerza decisiones de workflow todavía prematuras y corre el riesgo de reabrir scope documental cuando el repo aún no tiene runtime real.
   - Effort: Medium/High

### Recommendation
Conviene que este change sea **ultra pequeño en intención, pero NO tan chico que quede hueco**. La mejor opción es la **Minimal executable Python baseline**: meter solo el tooling mínimo que haga reales los futuros `apply`/`verify` (`openspec/config.yaml` + `pyproject.toml` + `src/jobmatchrag/__init__.py` + `tests/test_smoke.py` o equivalente). Eso deja lista una base verificable para `source-ingestion-framework` sin mezclar todavía FastAPI, Celery, adapters, infra, CI ni `AGENTS.md`.

### Risks
- Si el change queda solo en config y sin un test/package mínimo, `source-ingestion-framework` va a volver a mezclar bootstrap con implementación vertical.
- Si se mete tooling extra (CI, pre-commit, Docker, AGENTS, lockfiles, app skeleton amplia), el change pierde foco y reabre decisiones todavía inmaduras.
- `mypy` sobre un repo casi vacío necesita paths y exclusiones explícitas; si se configura sin pensar, puede generar ruido y falsa fricción desde el día uno.

### Ready for Proposal
Yes — el scope ya se puede proponer como bootstrap mínimo ejecutable, explícitamente limitado a baseline Python + verify harness real + OpenSpec config, dejando fuera runtime features y reglas de trabajo no esenciales.
