import jobmatchrag


def test_package_exposes_minimal_version_symbol() -> None:
    assert jobmatchrag.__version__ == "0.1.0"
