"""Angular module standalone tests (deterministic, no LLM).

Tests the angular Dagger module directly — build, install, lint.
Uses a minimal Angular app fixture with a committed package-lock.json, so
installs are reproducible and don't depend on what the npm registry resolves.
"""

import dagger
from dagger import dag

FIXTURE_PATH = "src/tests/fixtures/angular-app"


def _fixture_source() -> dagger.Directory:
    """Return the minimal Angular app fixture bundled with the tests module."""
    return dag.current_module().source().directory(FIXTURE_PATH)


async def test_angular_build(source: dagger.Directory) -> str:
    """Test angular build: run ng build and verify dist/ has files including index.html."""
    dist = await dag.angular().build(source=source)

    entries = await dist.entries()
    if not entries:
        raise RuntimeError("angular build returned empty dist directory")

    # Recursively find index.html in dist output
    html_files = await dist.glob("**/index.html")
    if not html_files:
        raise RuntimeError(f"angular build dist has no index.html. Entries: {entries}")

    return f"PASS: angular build (dist entries={len(entries)}, has_index_html=True)"


async def test_angular_install(source: dagger.Directory) -> str:
    """Test angular install: verify node_modules is created."""
    result = await dag.angular().install(source=source)

    entries = await result.entries()
    has_node_modules = any(e.rstrip("/") == "node_modules" for e in entries)
    if not has_node_modules:
        raise RuntimeError(f"angular install did not create node_modules. Entries: {entries}")

    return "PASS: angular install (node_modules present)"


async def test_angular_check_build(source: dagger.Directory) -> str:
    """Test the check-build check on a workspace made from the fixture.

    `dagger check` injects the workspace; a module calling another passes one
    explicitly, as here. Reading `pass` runs the check.
    """
    check = dag.angular().check_build(ws=source.as_workspace())
    if not await check.pass_():
        raise RuntimeError(f"angular check-build failed: {await check.error().message()}")
    return "PASS: angular check-build (workspace from the fixture)"
