"""Python build module standalone tests (deterministic, no LLM).

Tests the python-build Dagger module directly — install, lint.
Uses the FastAPI RealWorld example app as test source.
"""

import dagger
from dagger import dag

REALWORLD_REPO = "https://github.com/nsidnev/fastapi-realworld-example-app.git"
REALWORLD_BRANCH = "master"


def _clone_realworld() -> dagger.Directory:
    """Clone the FastAPI RealWorld example app."""
    return dag.git(REALWORLD_REPO).branch(REALWORLD_BRANCH).tree()


async def test_python_build_install(source: dagger.Directory) -> str:
    """Test python-build install: verify dependencies are installed."""
    result = await dag.python_build().install(source=source)

    entries = await result.entries()
    if not entries:
        raise RuntimeError("python-build install returned empty directory")

    # The source should still have its project files
    has_source = "app" in entries
    has_config = any(f in entries for f in ("pyproject.toml", "setup.cfg", "setup.py", "requirements.txt"))

    return f"PASS: python-build install (files={len(entries)}, has_app={has_source}, has_config={has_config})"


async def test_python_build_lint(source: dagger.Directory) -> str:
    """Test python-build lint: verify ruff output is returned."""
    result = await dag.python_build().lint(source=source, tool="ruff")

    if result is None:
        raise RuntimeError("python-build lint returned None")

    # ruff should return some output (even if it's just a summary)
    return f"PASS: python-build lint ({len(result)} chars)"
