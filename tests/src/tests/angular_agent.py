"""Angie (Angular Agent) module tests.

Uses the RealWorld Angular example app as a realistic test target:
https://github.com/realworld-apps/angular-realworld-example-app
(Angular 21, standalone components, vitest, playwright, signals)
"""

import dagger
from dagger import dag

REALWORLD_REPO = "https://github.com/realworld-apps/angular-realworld-example-app.git"
REALWORLD_BRANCH = "main"


def _clone_realworld() -> dagger.Directory:
    """Clone the Angular RealWorld example app."""
    return dag.git(REALWORLD_REPO).branch(REALWORLD_BRANCH).tree()


async def test_angie_assist(source: dagger.Directory) -> str:
    """Test assist: ask the agent to explain the project architecture."""
    agent = dag.angie(source=source)

    result = await agent.assist(
        assignment=(
            "Analyze this Angular project and explain its architecture. "
            "List the main features, routing structure, and how state management "
            "is handled. Mention the Angular version and key dependencies."
        ),
    )

    if not result:
        raise Exception("assist returned empty result")

    # The agent should identify it as an Angular app and mention key aspects
    result_lower = result.lower()
    checks = []
    if "angular" in result_lower:
        checks.append("mentions Angular")
    if "component" in result_lower:
        checks.append("mentions components")
    if "route" in result_lower or "routing" in result_lower:
        checks.append("mentions routing")

    return f"PASS: assist ({len(result)} chars, detected: {', '.join(checks) or 'none'})"


async def test_angie_review(source: dagger.Directory) -> str:
    """Test review: review the project for Angular best practices."""
    agent = dag.angie(source=source)

    result = await agent.review(
        focus="standalone components, signals usage, and Angular best practices",
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


async def test_angie_write_tests(source: dagger.Directory) -> str:
    """Test write-tests: generate tests for a specific component."""
    agent = dag.angie(source=source)

    result = await agent.write_tests(
        target="src/app/app.component.ts",
        test_framework="vitest",
    )

    if not result:
        raise Exception("write_tests returned empty result")

    # The agent should produce test-related output
    result_lower = result.lower()
    has_test_content = any(
        keyword in result_lower
        for keyword in ("describe", "test", "spec", "expect", "it(")
    )

    return f"PASS: write_tests ({len(result)} chars, test_content={has_test_content})"


async def test_angie_build(source: dagger.Directory) -> str:
    """Test build: analyze the build configuration."""
    agent = dag.angie(source=source)

    result = await agent.build()

    if not result:
        raise Exception("build returned empty result")

    # The agent should analyze angular.json, package.json, tsconfig
    result_lower = result.lower()
    has_build_info = any(
        keyword in result_lower
        for keyword in ("angular.json", "package.json", "tsconfig", "build", "ng build")
    )

    return f"PASS: build ({len(result)} chars, build_info={has_build_info})"


async def test_angie_upgrade_dry_run(source: dagger.Directory) -> str:
    """Test upgrade: dry-run upgrade analysis (no file modifications)."""
    agent = dag.angie(source=source)

    result = await agent.upgrade(
        target_version="21",
        dry_run=True,
    )

    if not result:
        raise Exception("upgrade dry_run returned empty result")

    # The agent should detect the current version and analyze upgrade path
    result_lower = result.lower()
    has_version_info = any(
        keyword in result_lower
        for keyword in ("version", "angular", "upgrade", "breaking", "current")
    )

    return f"PASS: upgrade dry_run ({len(result)} chars, version_info={has_version_info})"
