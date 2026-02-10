"""Examples for using the Angie (Angular Agent) Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


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
    ) -> str:
        """Example: Use Angie as a local coding assistant.

        Run from your Angular project root:
          dagger call -m github.com/certainty-labs/daggerverse/angie \
            assist --source=. --assignment="Add a search component with debounce"
        """
        return await dag.angie(source=source).assist(assignment=assignment)

    @function
    async def review_local(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        focus: Annotated[str, Doc("Review focus area")] = "",
    ) -> str:
        """Example: Review your Angular code locally.

        Run from your Angular project root:
          dagger call -m github.com/certainty-labs/daggerverse/angie \
            review --source=. --focus="performance and change detection"
        """
        return await dag.angie(source=source).review(focus=focus)

    @function
    async def upgrade_local(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        target_version: Annotated[str, Doc("Target Angular version")],
    ) -> str:
        """Example: Preview an Angular version upgrade (dry run).

        Run from your Angular project root:
          dagger call -m github.com/certainty-labs/daggerverse/angie \
            upgrade --source=. --target-version=19 --dry-run
        """
        return await dag.angie(source=source).upgrade(
            target_version=target_version,
            dry_run=True,
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
          dagger call -m github.com/certainty-labs/daggerverse/angie \
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
    ) -> str:
        """Example: Generate tests in CI for untested components.

        In your CI pipeline:
          dagger call -m github.com/certainty-labs/daggerverse/angie \
            write-tests --source=. --target="src/app/features/auth/"
        """
        return await dag.angie(source=source).write_tests(target=target)

    @function
    async def ci_build_and_fix(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        command: Annotated[str, Doc("Build command")] = "ng build --configuration production",
    ) -> str:
        """Example: Build the project in CI and get diagnostics on failures.

        In your CI pipeline:
          dagger call -m github.com/certainty-labs/daggerverse/angie \
            build --source=. --command="ng build --configuration production"
        """
        return await dag.angie(source=source).build(command=command)

    @function
    async def ci_upgrade_check(
        self,
        source: Annotated[dagger.Directory, Doc("Angular project source directory")],
        target_version: Annotated[str, Doc("Target Angular version")],
    ) -> str:
        """Example: Run upgrade compatibility check in CI (dry run).

        Schedule as a periodic CI job to check upgrade readiness:
          dagger call -m github.com/certainty-labs/daggerverse/angie \
            upgrade --source=. --target-version=20 --dry-run
        """
        return await dag.angie(source=source).upgrade(
            target_version=target_version,
            dry_run=True,
        )
