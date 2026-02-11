"""Examples for using the Monty (Python Agent) Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, Secret, dag, function, object_type


@object_type
class MontyExamples:
    """Usage examples for the Monty Python development agent.

    Demonstrates local development and CI/CD use cases.
    """

    # ========== LOCAL DEVELOPMENT ==========

    @function
    async def assist_local(
        self,
        source: Annotated[dagger.Directory, Doc("Python project source directory")],
        assignment: Annotated[str, Doc("Coding task")] = "Analyze this project and describe its architecture.",
    ) -> dagger.Directory:
        """Example: Use Monty as a local coding assistant.

        Run from your Python project root:
          dagger call -m github.com/certainty-labs/daggerverse/monty \\
            assist --source=. --assignment="Add a FastAPI endpoint with Pydantic validation"

        Export the modified files back:
          dagger call -m ... assist --source=. --assignment="..." export --path=.
        """
        return dag.monty(source=source).assist(assignment=assignment)

    @function
    async def review_local(
        self,
        source: Annotated[dagger.Directory, Doc("Python project source directory")],
        focus: Annotated[str, Doc("Review focus area")] = "",
    ) -> str:
        """Example: Review your Python code locally.

        Run from your Python project root:
          dagger call -m github.com/certainty-labs/daggerverse/monty \\
            review --source=. --focus="type safety and async patterns"
        """
        return await dag.monty(source=source).review(focus=focus)

    @function
    async def upgrade_local(
        self,
        source: Annotated[dagger.Directory, Doc("Python project source directory")],
        target_package: Annotated[str, Doc("Package to upgrade")],
        target_version: Annotated[str, Doc("Target version")] = "latest",
    ) -> dagger.Directory:
        """Example: Preview a dependency upgrade (dry run).

        Run from your Python project root:
          dagger call -m github.com/certainty-labs/daggerverse/monty \\
            upgrade --source=. --target-package=django --target-version=5.0 --dry-run
        """
        return dag.monty(source=source).upgrade(
            target_package=target_package,
            target_version=target_version,
            dry_run=True,
        )

    # ========== GITHUB INTEGRATION ==========

    @function
    async def develop_github_issue(
        self,
        source: Annotated[dagger.Directory, Doc("Python project source directory")],
        github_token: Annotated[Secret, Doc("GitHub token with repo + PR permissions")],
        issue_id: Annotated[int, Doc("GitHub issue number")],
        repository: Annotated[str, Doc("GitHub repository URL")],
    ) -> str:
        """Example: Read a GitHub issue, implement it, and create a PR.

        In GitHub Actions (triggered by labeling an issue):
          dagger call -m github.com/certainty-labs/daggerverse/monty \\
            develop-github-issue \\
            --github-token=env:GITHUB_TOKEN \\
            --issue-id=42 \\
            --repository="https://github.com/owner/repo" \\
            --source=.
        """
        return await dag.monty(source=source).develop_github_issue(
            github_token=github_token,
            issue_id=issue_id,
            repository=repository,
        )

    # ========== CI/CD PIPELINE ==========

    @function
    async def ci_review_pr(
        self,
        source: Annotated[dagger.Directory, Doc("Python project source directory")],
        diff: Annotated[str, Doc("Git diff from the PR")],
    ) -> str:
        """Example: Review a PR diff in CI.

        In GitHub Actions:
          DIFF=$(git diff origin/main...HEAD)
          dagger call -m github.com/certainty-labs/daggerverse/monty \\
            review --source=. --diff="$DIFF" --focus="Python best practices"
        """
        return await dag.monty(source=source).review(
            diff=diff,
            focus="Python best practices, type safety, and performance",
        )

    @function
    async def ci_generate_tests(
        self,
        source: Annotated[dagger.Directory, Doc("Python project source directory")],
        target: Annotated[str, Doc("File or module to test")] = "",
    ) -> dagger.Directory:
        """Example: Generate tests in CI for untested modules.

        In your CI pipeline:
          dagger call -m github.com/certainty-labs/daggerverse/monty \\
            write-tests --source=. --target="src/app/services/"
        """
        return dag.monty(source=source).write_tests(target=target)

    @function
    async def ci_build_and_fix(
        self,
        source: Annotated[dagger.Directory, Doc("Python project source directory")],
        command: Annotated[str, Doc("Build command")] = "python -m build",
    ) -> dagger.Directory:
        """Example: Build the project in CI and get diagnostics on failures.

        In your CI pipeline:
          dagger call -m github.com/certainty-labs/daggerverse/monty \\
            build --source=. --command="python -m build"
        """
        return dag.monty(source=source).build(command=command)
