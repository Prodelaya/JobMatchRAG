from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
ROADMAP = (ROOT / "docs/architecture/vertical-roadmap.md").read_text(encoding="utf-8")
OPENSPEC_CONFIG = (ROOT / "openspec/config.yaml").read_text(encoding="utf-8")


def test_bootstrap_docs_publish_recommended_uv_plus_dotvenv_flow() -> None:
    assert "uv venv .venv" in README
    assert "uv pip install -e .[dev]" in README
    assert "uv venv .venv" in AGENTS
    assert "uv pip install -e .[dev]" in AGENTS
    assert "prepare the local `.venv`" in README
    assert ".venv/bin/python -m ..." in README
    assert "Recommended local bootstrap" in AGENTS


def test_verify_contract_and_roadmap_scope_stay_aligned() -> None:
    for command in (
        ".venv/bin/python -m ruff check .",
        ".venv/bin/python -m mypy src",
        ".venv/bin/python -m pytest",
    ):
        assert command in AGENTS
        assert command in OPENSPEC_CONFIG

    for excluded_item in (
        "uv sync",
        "uv run",
        "lockfiles",
        "hooks",
        "CI",
        "Docker",
        "runtime",
        "functional scope",
    ):
        assert excluded_item in README
        assert excluded_item in AGENTS

    uv_index = ROADMAP.index("`uv-bootstrap-alignment`")
    source_index = ROADMAP.index("`source-ingestion-framework`")
    assert uv_index < source_index
    assert "Mini-change de alineación documental del bootstrap local con `uv + .venv`" in ROADMAP
    assert "no agrega tooling nuevo ni capacidad funcional de ingesta" in ROADMAP
