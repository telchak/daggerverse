"""Examples for using the Angie (Angular Agent) Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, Secret, dag, function, object_type


@object_type
class AngieExamples:
    """Usage examples for the Angie Angular development agent.

    Demonstrates local development and CI/CD use cases.
    """

    # ========== LOCAL DEVELOPMENT ==========

    @function
    async def assist_local(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        assignment: Annotated[str, Doc("Coding task")] = "Analyze this project and describe its architecture.",
    ) -> dagger.Directory:
        """Example: Use Angie as a local coding assistant.

        Run from your Angular project root:
          dagger call -m github.com/telchak/daggerverse/angie \\
            assist --source=. --assignment="Add a search component with debounce"

        Export the modified files back:
          dagger call -m ... assist --source=. --assignment="..." export --path=.
        """
        return dag.angie(source=source).assist(assignment=assignment)

    @function
    async def review_local(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        focus: Annotated[str, Doc("Review focus area")] = "",
    ) -> str:
        """Example: Review your Angular code locally.

        Run from your Angular project root:
          dagger call -m github.com/telchak/daggerverse/angie \\
            review --source=. --focus="performance and change detection"
        """
        return await dag.angie(source=source).review(focus=focus)

    @function
    async def upgrade_local(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        target_version: Annotated[str, Doc("Target Angular version")],
    ) -> dagger.Directory:
        """Example: Preview an Angular version upgrade (dry run).

        Run from your Angular project root:
          dagger call -m github.com/telchak/daggerverse/angie \\
            upgrade --source=. --target-version=19 --dry-run
        """
        return dag.angie(source=source).upgrade(
            target_version=target_version,
            dry_run=True,
        )

    # ========== GITHUB INTEGRATION ==========

    @function
    async def develop_github_issue(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        github_token: Annotated[Secret, Doc("GitHub token with repo + PR permissions")],
        issue_id: Annotated[int, Doc("GitHub issue number")],
        repository: Annotated[str, Doc("GitHub repository URL")],
    ) -> str:
        """Example: Read a GitHub issue, implement it, and create a PR.

        In GitHub Actions (triggered by labeling an issue):
          dagger call -m github.com/telchak/daggerverse/angie \\
            develop-github-issue \\
            --github-token=env:GITHUB_TOKEN \\
            --issue-id=42 \\
            --repository="https://github.com/owner/repo" \\
            --source=.
        """
        return await dag.angie(source=source).develop_github_issue(
            github_token=github_token,
            issue_id=issue_id,
            repository=repository,
        )

    # ========== CI/CD PIPELINE ==========

    @function
    async def ci_review_pr(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        diff: Annotated[str, Doc("Git diff from the PR")],
    ) -> str:
        """Example: Review a PR diff in CI.

        In GitHub Actions:
          DIFF=$(git diff origin/main...HEAD)
          dagger call -m github.com/telchak/daggerverse/angie \\
            review --source=. --diff="$DIFF" --focus="Angular best practices"
        """
        return await dag.angie(source=source).review(
            diff=diff,
            focus="Angular best practices, type safety, and performance",
        )

    @function
    async def ci_generate_tests(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        target: Annotated[str, Doc("File or component to test")] = "",
    ) -> dagger.Directory:
        """Example: Generate tests in CI for untested components.

        In your CI pipeline:
          dagger call -m github.com/telchak/daggerverse/angie \\
            write-tests --source=. --target="src/app/features/auth/"
        """
        return dag.angie(source=source).write_tests(target=target)

    @function
    async def ci_build_and_fix(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        command: Annotated[str, Doc("Build command")] = "ng build --configuration production",
    ) -> dagger.Directory:
        """Example: Build the project in CI and get diagnostics on failures.

        In your CI pipeline:
          dagger call -m github.com/telchak/daggerverse/angie \\
            build --source=. --command="ng build --configuration production"
        """
        return dag.angie(source=source).build(command=command)

    @function
    async def ci_upgrade_check(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        target_version: Annotated[str, Doc("Target Angular version")],
    ) -> dagger.Directory:
        """Example: Run upgrade compatibility check in CI (dry run).

        Schedule as a periodic CI job to check upgrade readiness:
          dagger call -m github.com/telchak/daggerverse/angie \\
            upgrade --source=. --target-version=20 --dry-run
        """
        return dag.angie(source=source).upgrade(
            target_version=target_version,
            dry_run=True,
        )
