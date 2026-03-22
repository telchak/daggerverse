"""Angular module standalone tests (deterministic, no LLM).

Tests the angular Dagger module directly — build, install, lint.
Uses the RealWorld Angular example app as test source.
"""

import dagger
from dagger import dag

REALWORLD_REPO = "https://github.com/realworld-apps/angular-realworld-example-app.git"
# Pinned to avoid upstream dependency breakage (core@21.2.4 vs animations@21.1.1)
REALWORLD_COMMIT = "cc15bad5d28534d027fc833c558d520f110e2720"


def _clone_realworld() -> dagger.Directory:
    """Clone the Angular RealWorld example app at a pinned commit."""
    return dag.git(REALWORLD_REPO).commit(REALWORLD_COMMIT).tree()


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
