"""Examples for using the Daggie (Dagger CI Agent) Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, Secret, dag, function, object_type


@object_type
class DaggieExamples:
    """Usage examples for the Daggie Dagger CI specialist agent.

    Demonstrates local development and CI/CD use cases.
    """

    # ========== LOCAL DEVELOPMENT ==========

    @function
    async def assist_local(
        self,
        source: Annotated[dagger.Directory, Doc("Project source directory")],
        assignment: Annotated[str, Doc("Coding task")] = "Analyze this project and create a Dagger module for building it.",
    ) -> dagger.Directory:
        """Example: Use Daggie as a local coding assistant.

        Run from your project root:
          dagger call -m github.com/telchak/daggerverse/daggie \\
            assist --source=. --assignment="Create a Dagger pipeline for building and testing"
        """
        return dag.daggie(source=source).assist(assignment=assignment)

    @function
    async def assist_with_references(
        self,
        source: Annotated[dagger.Directory, Doc("Project source directory")],
    ) -> dagger.Directory:
        """Example: Use Daggie with reference modules to learn patterns.

        The agent clones and reads the reference modules before implementing:
          dagger call -m github.com/telchak/daggerverse/daggie \\
            --module-urls="https://github.com/telchak/daggerverse.git#main:daggerverse/python-build" \\
            assist --source=. --assignment="Create a similar module for this project"
        """
        return dag.daggie(
            source=source,
            module_urls=[
                "https://github.com/telchak/daggerverse.git#main:daggerverse/python-build",
            ],
        ).assist(
            assignment="Create a Dagger module for this project following the patterns from the reference module.",
        )

    @function
    async def explain_concept(
        self,
        question: Annotated[str, Doc("What to explain")] = "What is a Dagger module and how does dagger.json configure it?",
    ) -> str:
        """Example: Ask Daggie to explain a Dagger concept.

        Run:
          dagger call -m github.com/telchak/daggerverse/daggie \\
            explain --question="How does caching work in Dagger?"
        """
        return await dag.daggie().explain(question=question)

    @function
    async def debug_pipeline(
        self,
        source: Annotated[dagger.Directory, Doc("Project source with the broken module")],
        error_output: Annotated[str, Doc("Pipeline error output")],
    ) -> dagger.Directory:
        """Example: Debug a Dagger pipeline error.

        Run:
          dagger call -m github.com/telchak/daggerverse/daggie \\
            debug --source=. --error-output="$(dagger call build 2>&1)"
        """
        return dag.daggie(source=source).debug(error_output=error_output)

    @function
    async def review_local(
        self,
        source: Annotated[dagger.Directory, Doc("Project source directory")],
        focus: Annotated[str, Doc("Review focus area")] = "",
    ) -> str:
        """Example: Review Dagger module code.

        Run:
          dagger call -m github.com/telchak/daggerverse/daggie \\
            review --source=. --focus="caching and container optimization"
        """
        return await dag.daggie(source=source).review(focus=focus)

    # ========== GITHUB INTEGRATION ==========

    @function
    async def develop_github_issue(
        self,
        source: Annotated[dagger.Directory, Doc("Project source directory")],
        github_token: Annotated[Secret, Doc("GitHub token with repo + PR permissions")],
        issue_id: Annotated[int, Doc("GitHub issue number")],
        repository: Annotated[str, Doc("GitHub repository URL")],
    ) -> str:
        """Example: Read a GitHub issue, implement it, and create a PR.

        In GitHub Actions (triggered by labeling an issue):
          dagger call -m github.com/telchak/daggerverse/daggie \\
            develop-github-issue \\
            --github-token=env:GITHUB_TOKEN \\
            --issue-id=42 \\
            --repository="https://github.com/owner/repo" \\
            --source=.
        """
        return await dag.daggie(source=source).develop_github_issue(
            github_token=github_token,
            issue_id=issue_id,
            repository=repository,
        )

    # ========== CI/CD PIPELINE ==========

    @function
    async def ci_review_pr(
        self,
        source: Annotated[dagger.Directory, Doc("Project source directory")],
        diff: Annotated[str, Doc("Git diff from the PR")],
    ) -> str:
        """Example: Review a PR diff in CI.

        In GitHub Actions:
          DIFF=$(git diff origin/main...HEAD)
          dagger call -m github.com/telchak/daggerverse/daggie \\
            review --source=. --diff="$DIFF" --focus="Dagger best practices"
        """
        return await dag.daggie(source=source).review(
            diff=diff,
            focus="Dagger best practices, caching, and pipeline correctness",
        )

    @function
    async def ci_suggest_fix(
        self,
        source: Annotated[dagger.Directory, Doc("Project source directory")],
        github_token: Annotated[Secret, Doc("GitHub token")],
        pr_number: Annotated[int, Doc("Pull request number")],
        repo: Annotated[str, Doc("GitHub repository URL")],
        commit_sha: Annotated[str, Doc("HEAD commit SHA")],
        error_output: Annotated[str, Doc("CI error output")],
    ) -> str:
        """Example: Post inline fix suggestions on a PR after CI failure.

        In GitHub Actions (on build failure):
          dagger call -m github.com/telchak/daggerverse/daggie \\
            suggest-github-fix \\
            --github-token=env:GITHUB_TOKEN \\
            --pr-number=123 \\
            --repo="https://github.com/owner/repo" \\
            --commit-sha=abc123 \\
            --error-output="$(cat build-output.log)" \\
            --source=.
        """
        return await dag.daggie(source=source).suggest_github_fix(
            github_token=github_token,
            pr_number=pr_number,
            repo=repo,
            commit_sha=commit_sha,
            error_output=error_output,
        )
