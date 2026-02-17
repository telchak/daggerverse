"""Angie — AI-powered Angular development agent with MCP integration."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, field, function, object_type

from agent_base import constants, github_tools, llm_helpers, routing, workspace


@object_type
class Angie:
    """AI-powered Angular development agent.

    Uses the Angular CLI MCP server for docs, best practices, build, test,
    and modernize capabilities. Provides workspace tools for reading, editing,
    and searching files.

    Pass your Angular project as --source and use the agent entrypoints
    (assist, review, write-tests, build, upgrade) to work with your code.
    """

    source: Annotated[
        dagger.Directory,
        Doc("Angular project source directory"),
        DefaultPath("/"),
    ] = field()
    node_version: Annotated[
        str,
        Doc("Node.js version for the Angular CLI MCP server container"),
    ] = field(default="22")

    # Private fields set during suggest_github_fix execution
    _github_token: dagger.Secret | None = field(default=None, init=False)
    _pr_repo: str = field(default="", init=False)
    _pr_number: int = field(default=0, init=False)
    _pr_commit_sha: str = field(default="", init=False)

    # --- Agent-specific configuration ---

    _CONTEXT_FILES = ("ANGIE.md", "AGENT.md", "CLAUDE.md")
    _CLASS_NAME = "Angie"
    _ALLOWED_ROUTER_KEYS = {
        "upgrade": {"target_version", "dry_run"},
        "build": {"command"},
        "write_tests": {"target", "test_framework"},
    }

    def _mcp_servers(self) -> dict[str, dagger.Service]:
        return {
            "angular": (
                dag.container()
                .from_(f"node:{self.node_version}")
                .with_default_args([
                    "npx", "-y", "@angular/cli", "mcp",
                    "--experimental-tool", "build",
                    "--experimental-tool", "test",
                    "--experimental-tool", "e2e",
                    "--experimental-tool", "modernize",
                ])
                .as_service()
            ),
        }

    def _load_prompt(self, filename: str) -> dagger.File:
        return dag.current_module().source().file(f"src/angie/prompts/{filename}")

    async def _build_llm(self, env, prompt_file, source=None):
        return await llm_helpers.build_llm(
            env, "system_prompt.md", prompt_file, self._load_prompt,
            self._CONTEXT_FILES, self._mcp_servers(), self._CLASS_NAME,
            constants.BLOCKED_ENTRYPOINTS, source or self.source,
        )

    async def _build_suggest_fix_llm(self, env, source=None):
        return await llm_helpers.build_suggest_fix_llm(
            env, self._load_prompt, self._CONTEXT_FILES, self._CLASS_NAME,
            constants.BLOCKED_ENTRYPOINTS, constants.BLOCKED_DESTRUCTIVE,
            source or self.source,
        )

    # --- Agent entrypoints ---

    @function
    async def assist(
        self,
        assignment: Annotated[str, Doc("What you want the agent to do (e.g. 'Add a login component with reactive forms')")],
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
    ) -> dagger.Directory:
        """General Angular coding assistant.

        Reads code, answers questions, implements features, refactors,
        and uses Angular CLI MCP tools for docs and best practices.
        Returns the modified workspace directory.
        """
        ws = source or self.source
        env = (
            dag.env()
            .with_workspace(ws)
            .with_string_input("assignment", assignment, "The coding task to accomplish")
        )
        return (await self._build_llm(env, "assist_prompt.md", ws)).env().workspace()

    @function
    async def review(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory to review (uses constructor source if omitted)")] = None,
        diff: Annotated[str, Doc("Git diff or PR diff to review (optional)")] = "",
        focus: Annotated[str, Doc("Specific area to focus the review on (optional)")] = "",
    ) -> str:
        """Review Angular code for best practices, performance, accessibility, and type safety.

        Provides structured feedback with issues, suggestions, and a summary.
        Returns the review as text (no files modified).
        """
        ws = source or self.source
        env = (
            dag.env()
            .with_workspace(ws)
            .with_string_output("result", "The code review result")
        )
        if diff:
            env = env.with_string_input("diff", diff, "Git diff or PR diff to review")
        if focus:
            env = env.with_string_input("focus", focus, "Specific area to focus the review on")
        work = await self._build_llm(env, "review_prompt.md", ws)
        return await work.env().output("result").as_string()

    @function
    async def write_tests(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory (uses constructor source if omitted)")] = None,
        target: Annotated[str, Doc("Specific file or component to write tests for (optional)")] = "",
        test_framework: Annotated[str, Doc("Test framework preference: 'jest', 'karma', 'vitest' (optional)")] = "",
    ) -> dagger.Directory:
        """Generate unit, integration, or e2e tests for Angular components and services.

        Follows Angular testing patterns and uses the project's existing test setup.
        Returns the workspace directory with generated test files.
        """
        ws = source or self.source
        env = dag.env().with_workspace(ws)
        if target:
            env = env.with_string_input("target", target, "Specific file or component to write tests for")
        if test_framework:
            env = env.with_string_input("test_framework", test_framework, "Test framework preference")
        return (await self._build_llm(env, "write_tests_prompt.md", ws)).env().workspace()

    @function
    async def build(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory (uses constructor source if omitted)")] = None,
        command: Annotated[str, Doc("Build command to run (e.g. 'ng build --configuration production')")] = "",
    ) -> dagger.Directory:
        """Build, compile, or lint an Angular project.

        Diagnoses build errors and suggests fixes using Angular CLI MCP tools.
        Returns the workspace directory with any fixes applied.
        """
        ws = source or self.source
        env = dag.env().with_workspace(ws)
        if command:
            env = env.with_string_input("command", command, "Build command to run")
        return (await self._build_llm(env, "build_prompt.md", ws)).env().workspace()

    @function
    async def upgrade(
        self,
        target_version: Annotated[str, Doc("Target Angular version (e.g. '19', '18.2', '20.0.0')")],
        source: Annotated[dagger.Directory | None, Doc("Source directory (uses constructor source if omitted)")] = None,
        dry_run: Annotated[bool, Doc("Analyze and report changes without modifying files")] = False,
    ) -> dagger.Directory:
        """Upgrade an Angular project to a target version.

        Detects the current Angular version, researches breaking changes and
        migration steps between versions, analyzes the codebase for impacted
        code, and applies the necessary modifications.
        Returns the workspace directory with upgrade changes applied.
        """
        ws = source or self.source
        env = (
            dag.env()
            .with_workspace(ws)
            .with_string_input("target_version", target_version, "Target Angular version to upgrade to")
        )
        if dry_run:
            env = env.with_string_input("dry_run", "true", "Only analyze and report, do not modify files")
        return (await self._build_llm(env, "upgrade_prompt.md", ws)).env().workspace()

    # --- GitHub integration ---

    @function
    async def suggest_github_fix(
        self,
        github_token: Annotated[dagger.Secret, Doc("GitHub token with repo permissions")],
        pr_number: Annotated[int, Doc("Pull request number")],
        repo: Annotated[str, Doc("GitHub repository URL (e.g. 'https://github.com/owner/repo')")],
        commit_sha: Annotated[str, Doc("HEAD commit SHA of the PR branch")],
        error_output: Annotated[str, Doc("CI error output (stderr/stdout)")],
        source: Annotated[dagger.Directory | None, Doc("Source directory of the PR branch")] = None,
    ) -> str:
        """Analyze a CI failure and post inline code suggestions on a GitHub PR.

        Reads the error output, explores source files, and posts GitHub
        "suggested changes" that developers can apply with one click.
        """
        ws = source or self.source
        if source:
            self.source = source
        return await github_tools.suggest_github_fix_impl(
            self._build_suggest_fix_llm, github_token, pr_number, repo,
            commit_sha, error_output, self, ws,
        )

    @function
    async def suggest_github_pr_code_comment(
        self,
        path: Annotated[str, Doc("File path relative to repo root")],
        line: Annotated[int, Doc("Line number to suggest a change on")],
        suggestion: Annotated[str, Doc("Replacement code (no ```suggestion fences, just the raw code)")],
        comment: Annotated[str, Doc("Explanation of the fix")] = "",
    ) -> str:
        """Post an inline code suggestion on a GitHub pull request.

        The suggestion will appear as a GitHub "suggested change" that
        developers can apply with one click.
        """
        return await github_tools.suggest_github_pr_code_comment_impl(
            self._github_token, self._pr_repo, self._pr_number,
            self._pr_commit_sha, path, line, suggestion, comment,
        )

    @function
    async def develop_github_issue(
        self,
        github_token: Annotated[dagger.Secret, Doc("GitHub token with repo and pull-request permissions")],
        issue_id: Annotated[int, Doc("GitHub issue number")],
        repository: Annotated[str, Doc("GitHub repository URL (e.g. 'https://github.com/owner/repo')")],
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
        base: Annotated[str, Doc("Base branch for the pull request")] = "main",
        suggest_github_fix_on_failure: Annotated[bool, Doc("Post a diagnostic comment on the issue if the agent fails")] = False,
    ) -> str:
        """Read a GitHub issue, route it to the best agent, and create a Pull Request.

        A router LLM reads the issue and selects the optimal function — assist,
        upgrade, build, or write-tests — then calls it with extracted parameters.
        Comments on the issue with a summary and a link to the PR.
        Returns the PR URL.
        """
        return await github_tools.develop_github_issue_impl(
            self._load_prompt, self._execute_routed_function,
            self._ALLOWED_ROUTER_KEYS, github_token, issue_id, repository,
            source or self.source, base, suggest_github_fix_on_failure,
        )

    async def _execute_routed_function(self, function_name, params, body, workspace, gh, repository, issue_id, suggest_on_failure):
        return await routing.execute_routed_function(
            self, function_name, params, body, workspace,
            gh, repository, issue_id, suggest_on_failure,
        )

    # --- Workspace tools ---

    @function
    async def read_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        offset: Annotated[int, Doc("Line number to start reading from (1-based)")] = 0,
        limit: Annotated[int, Doc("Maximum number of lines to read")] = 0,
    ) -> str:
        """Read a file from the workspace with line numbers."""
        return await workspace.read_file_impl(self.source, file_path, offset, limit)

    @function
    async def edit_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        old_string: Annotated[str, Doc("The exact string to find and replace")],
        new_string: Annotated[str, Doc("The replacement string")],
        replace_all: Annotated[bool, Doc("Replace all occurrences (default: first only)")] = False,
    ) -> dagger.Changeset:
        """Edit a file by replacing a string. The old_string must match exactly.

        Returns a changeset showing the diff.
        """
        self.source, changeset = await workspace.edit_file_impl(
            self.source, file_path, old_string, new_string, replace_all,
        )
        return changeset

    @function
    async def write_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        contents: Annotated[str, Doc("The full file contents to write")],
    ) -> dagger.Changeset:
        """Create or overwrite a file in the workspace.

        Returns a changeset showing the diff.
        """
        self.source, changeset = workspace.write_file_impl(
            self.source, file_path, contents,
        )
        return changeset

    @function
    async def glob(
        self,
        pattern: Annotated[str, Doc("Glob pattern (e.g. 'src/**/*.ts', '**/*.component.ts')")],
    ) -> str:
        """Find files in the workspace matching a glob pattern."""
        return await workspace.glob_impl(self.source, pattern)

    @function
    async def grep(
        self,
        pattern: Annotated[str, Doc("Search pattern (regex supported)")],
        paths: Annotated[str, Doc("Comma-separated paths to search in (optional)")] = "",
        file_glob: Annotated[str, Doc("Glob pattern to filter files (e.g. '*.ts')")] = "",
        insensitive: Annotated[bool, Doc("Case-insensitive search")] = False,
        limit: Annotated[int, Doc("Maximum number of matching lines to return")] = 100,
    ) -> str:
        """Search file contents in the workspace using grep."""
        return await workspace.grep_impl(self.source, pattern, paths, file_glob, insensitive, limit)

    # --- Task sub-agent ---

    @function
    async def task(
        self,
        description: Annotated[str, Doc("Short description of the sub-task")],
        prompt: Annotated[str, Doc("Detailed prompt for the sub-agent")],
    ) -> str:
        """Launch a sub-agent for research or focused work.

        The sub-agent has read-only access to the workspace and Angular MCP tools.
        Use this for research, analysis, or exploring documentation.
        """
        llm = await llm_helpers.build_task_llm(
            self.source, self._load_prompt, self._CONTEXT_FILES,
            self._mcp_servers(), self._CLASS_NAME,
            constants.BLOCKED_ENTRYPOINTS, constants.BLOCKED_DESTRUCTIVE,
            description, prompt,
        )
        return await llm.env().output("result").as_string()
