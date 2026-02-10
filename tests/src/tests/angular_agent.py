"""Angie (Angular Agent) module tests.

Uses the RealWorld Angular example app as a realistic test target:
https://github.com/realworld-apps/angular-realworld-example-app
(Angular 21, standalone components, vitest, playwright, signals)

The develop-github-issue test uses a dedicated test repo:
https://github.com/telchak/angular-dagger-template
"""

import dagger
from dagger import dag

REALWORLD_REPO = "https://github.com/realworld-apps/angular-realworld-example-app.git"
REALWORLD_BRANCH = "main"

TEST_TEMPLATE_REPO = "https://github.com/telchak/angular-dagger-template"
TEST_TEMPLATE_ISSUE_ID = 1


def _clone_realworld() -> dagger.Directory:
    """Clone the Angular RealWorld example app."""
    return dag.git(REALWORLD_REPO).branch(REALWORLD_BRANCH).tree()


async def test_angie_assist(source: dagger.Directory) -> str:
    """Test assist: ask the agent to add a component — returns a Directory."""
    agent = dag.angie(source=source)

    result = await agent.assist(
        assignment=(
            "Analyze this Angular project and describe its architecture. "
            "List the main features, routing structure, and key dependencies. "
            "Then create a file called ARCHITECTURE.md with your findings."
        ),
    )

    # result is a Directory — verify it has files
    entries = await result.entries()
    if not entries:
        raise Exception("assist returned empty directory")

    has_new_file = "ARCHITECTURE.md" in entries
    has_source = "src" in entries

    return f"PASS: assist (files={len(entries)}, new_file={has_new_file}, has_src={has_source})"


async def test_angie_review(source: dagger.Directory) -> str:
    """Test review: review the project for Angular best practices — returns str."""
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
    """Test write-tests: generate tests — returns a Directory with test files."""
    agent = dag.angie(source=source)

    result = await agent.write_tests(
        target="src/app/app.component.ts",
        test_framework="vitest",
    )

    # result is a Directory — verify it still has project files
    entries = await result.entries()
    if not entries:
        raise Exception("write_tests returned empty directory")

    # Check for test files in the workspace
    test_files = await result.glob("**/*.spec.ts")
    has_source = "src" in entries

    return f"PASS: write_tests (files={len(entries)}, spec_files={len(test_files)}, has_src={has_source})"


async def test_angie_build(source: dagger.Directory) -> str:
    """Test build: analyze and fix build — returns a Directory."""
    agent = dag.angie(source=source)

    result = await agent.build()

    # result is a Directory — verify it has project files
    entries = await result.entries()
    if not entries:
        raise Exception("build returned empty directory")

    has_source = "src" in entries
    has_config = "angular.json" in entries

    return f"PASS: build (files={len(entries)}, has_src={has_source}, has_config={has_config})"


async def test_angie_upgrade_dry_run(source: dagger.Directory) -> str:
    """Test upgrade: dry-run upgrade — returns a Directory (unchanged in dry-run)."""
    agent = dag.angie(source=source)

    result = await agent.upgrade(
        target_version="21",
        dry_run=True,
    )

    # result is a Directory — should still have project files
    entries = await result.entries()
    if not entries:
        raise Exception("upgrade dry_run returned empty directory")

    has_source = "src" in entries
    has_package = "package.json" in entries

    return f"PASS: upgrade dry_run (files={len(entries)}, has_src={has_source}, has_package={has_package})"


def _clone_template() -> dagger.Directory:
    """Clone the Angular test template repo."""
    return dag.git(f"{TEST_TEMPLATE_REPO}.git").branch("main").tree()


async def test_angie_develop_github_issue(
    github_token: dagger.Secret,
    issue_id: int = TEST_TEMPLATE_ISSUE_ID,
    repository: str = TEST_TEMPLATE_REPO,
) -> str:
    """Test develop-github-issue: route an issue, implement it, create a PR.

    Uses telchak/angular-dagger-template issue #1 (Add unit tests for AppComponent).
    The router should select write_tests. Verifies a PR URL is returned.
    """
    source = _clone_template()
    agent = dag.angie(source=source)

    pr_url = await agent.develop_github_issue(
        github_token=github_token,
        issue_id=issue_id,
        repository=repository,
        source=source,
    )

    if not pr_url:
        raise Exception("develop_github_issue returned empty result")

    if not pr_url.startswith("https://"):
        raise Exception(f"develop_github_issue returned invalid PR URL: {pr_url}")

    return f"PASS: develop_github_issue (pr_url={pr_url})"
