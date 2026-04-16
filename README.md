# JobMatchRAG

JobMatchRAG es un sistema personal de inteligencia de empleo para Pablo Laya. Su objetivo en V1 es capturar ofertas, filtrar incompatibilidades duras, consolidar duplicados, calcular un score explicable y exponer el resultado públicamente como un artefacto vivo de portfolio.

## Estado actual

- foundation documental: cerrada
- bootstrap de tooling Python: cerrado
- alineación del bootstrap local con `uv + .venv`: cerrada
- siguiente vertical recomendado: abrir `infojobs-search-mapping`

## Fuente de verdad

El repositorio usa documentación viva como fuente de verdad. Los puntos de entrada más relevantes son:

- `docs/PRD-JobMatchRAG.md` — framing del producto y alcance de V1
- `docs/architecture/system-overview.md` — forma del sistema, boundaries y pipeline
- `docs/architecture/vertical-roadmap.md` — orden recomendado de changes y siguiente vertical
- `AGENTS.md` — reglas de trabajo del proyecto y expectativas de mantenimiento de la documentación viva

## Bootstrap local recomendado

Usá este flujo mínimo de bootstrap para prepare the local `.venv` y dejar alineado el entorno recomendado:

1. `uv venv .venv`
2. `uv pip install -e .[dev]`

Este bootstrap local recomendado preserva el contrato existente de verificación `.venv/bin/python -m ...`.
No adopta `uv sync`, `uv run`, lockfiles, hooks, CI, Docker, runtime ni cambios de alcance functional scope.

## Verificación local

- `.venv/bin/python -m ruff check .`
- `.venv/bin/python -m mypy src`
- `.venv/bin/python -m pytest`
