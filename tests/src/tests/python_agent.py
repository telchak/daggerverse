"""Monty (Python Agent) module tests.

Uses the FastAPI RealWorld example app as a realistic test target:
https://github.com/nsidnev/fastapi-realworld-example-app
(FastAPI, Pydantic, async, PostgreSQL, clean architecture)
"""

import dagger
from dagger import dag

REALWORLD_REPO = "https://github.com/nsidnev/fastapi-realworld-example-app.git"
REALWORLD_BRANCH = "master"


def _clone_realworld() -> dagger.Directory:
    """Clone the FastAPI RealWorld example app."""
    return dag.git(REALWORLD_REPO).branch(REALWORLD_BRANCH).tree()


async def test_monty_assist(source: dagger.Directory) -> str:
    """Test assist: ask the agent to analyze the project — returns a Directory."""
    agent = dag.monty(source=source)

    result = await agent.assist(
        assignment=(
            "Analyze this Python project and describe its architecture. "
            "List the main features, routing structure, and key dependencies. "
            "Then create a file called ARCHITECTURE.md with your findings."
        ),
    )

    # result is a Directory — verify it has files
    entries = await result.entries()
    if not entries:
        raise Exception("assist returned empty directory")

    has_new_file = "ARCHITECTURE.md" in entries
    has_source = "app" in entries

    return f"PASS: assist (files={len(entries)}, new_file={has_new_file}, has_app={has_source})"


async def test_monty_review(source: dagger.Directory) -> str:
    """Test review: review the project for Python best practices — returns str."""
    agent = dag.monty(source=source)

    result = await agent.review(
        focus="type safety, async patterns, and Python best practices",
    )

    if not result:
        raise Exception("review returned empty result")

    # A real review should contain structured feedback
    result_lower = result.lower()
    has_structure = any(
        keyword in result_lower
        for keyword in ("issue", "suggestion", "summary", "positive", "recommend")
    )

    return f"PASS: review ({len(result)} chars, structured={has_structure})"


async def test_monty_write_tests(source: dagger.Directory) -> str:
    """Test write-tests: generate tests — returns a Directory with test files."""
    agent = dag.monty(source=source)

    result = await agent.write_tests(
        target="app/main.py",
        test_framework="pytest",
    )

    # result is a Directory — verify it still has project files
    entries = await result.entries()
    if not entries:
        raise Exception("write_tests returned empty directory")

    # Check for test files in the workspace
    test_files = await result.glob("**/test_*.py")
    has_source = "app" in entries

    return f"PASS: write_tests (files={len(entries)}, test_files={len(test_files)}, has_app={has_source})"


async def test_monty_build(source: dagger.Directory) -> str:
    """Test build: analyze and fix build — returns a Directory."""
    agent = dag.monty(source=source)

    result = await agent.build()

    # result is a Directory — verify it has project files
    entries = await result.entries()
    if not entries:
        raise Exception("build returned empty directory")

    has_source = "app" in entries
    has_config = any(f in entries for f in ("pyproject.toml", "setup.cfg", "setup.py"))

    return f"PASS: build (files={len(entries)}, has_app={has_source}, has_config={has_config})"


async def test_monty_upgrade_dry_run(source: dagger.Directory) -> str:
    """Test upgrade: dry-run upgrade — returns a Directory (unchanged in dry-run)."""
    agent = dag.monty(source=source)

    result = await agent.upgrade(
        target_package="pydantic",
        target_version="latest",
        dry_run=True,
    )

    # result is a Directory — should still have project files
    entries = await result.entries()
    if not entries:
        raise Exception("upgrade dry_run returned empty directory")

    has_source = "app" in entries
    has_requirements = any(
        f in entries for f in ("requirements.txt", "pyproject.toml", "setup.cfg")
    )

    return f"PASS: upgrade dry_run (files={len(entries)}, has_app={has_source}, has_requirements={has_requirements})"
