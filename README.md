# JobMatchRAG
JobMatchRAG es un sistema personal de inteligencia de empleo diseñado para detectar, consolidar, rankear y mostrar públicamente ofertas de trabajo alineadas con el perfil profesional y los criterios reales de Pablo Laya.

## Recommended local bootstrap

Use this minimal bootstrap flow to prepare the local `.venv`:

1. `uv venv .venv`
2. `uv pip install -e .[dev]`

This recommended local bootstrap preserves the existing `.venv/bin/python -m ...` verification contract.
It does not adopt `uv sync`, `uv run`, lockfiles, hooks, CI, Docker, runtime, or functional scope changes.
