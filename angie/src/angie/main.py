"""Angie — AI-powered Angular development agent with MCP integration."""

import json
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, field, function, object_type


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

    # --- Angular MCP integration ---

    def _angular_mcp_service(self) -> dagger.Service:
        """Create the Angular CLI MCP server as a Dagger Service."""
        return (
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
        )

    # --- Prompt helpers ---

    def _load_prompt(self, filename: str) -> dagger.File:
        """Load a prompt file from the module source."""
        return dag.current_module().source().file(
            f"src/angie/prompts/{filename}"
        )

    async def _read_context_file(self, source: dagger.Directory | None = None) -> str:
        """Read per-repo context from ANGIE.md, AGENT.md, or CLAUDE.md."""
        target = source or self.source
        entries = await target.entries()
        for name in ("ANGIE.md", "AGENT.md", "CLAUDE.md"):
            if name in entries:
                contents = await target.file(name).contents()
                return f"\n\n## Project Context (from {name})\n\n{contents}"
        return ""

    async def _build_llm(
        self,
        env: dagger.Env,
        prompt_file: str,
        source: dagger.Directory | None = None,
    ) -> dagger.LLM:
        """Build an LLM with the environment, workspace tools, MCP, and prompts."""
        context_md = await self._read_context_file(source)
        system_prompt = await self._load_prompt("system_prompt.md").contents()

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_mcp_server("angular", self._angular_mcp_service())
            .with_system_prompt(system_prompt + context_md)
        )

        return (
            llm
            .with_blocked_function("Angie", "assist")
            .with_blocked_function("Angie", "review")
            .with_blocked_function("Angie", "write_tests")
            .with_blocked_function("Angie", "build")
            .with_blocked_function("Angie", "upgrade")
            .with_blocked_function("Angie", "develop_github_issue")
            .with_prompt_file(self._load_prompt(prompt_file))
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
        workspace = source or self.source

        env = (
            dag.env()
            .with_workspace(workspace)
            .with_string_input("assignment", assignment, "The coding task to accomplish")
        )

        work = await self._build_llm(env, "assist_prompt.md", workspace)
        return work.env().workspace()

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
        workspace = source or self.source

        env = (
            dag.env()
            .with_workspace(workspace)
            .with_string_output("result", "The code review result")
        )

        if diff:
            env = env.with_string_input("diff", diff, "Git diff or PR diff to review")
        if focus:
            env = env.with_string_input("focus", focus, "Specific area to focus the review on")

        work = await self._build_llm(env, "review_prompt.md", workspace)
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
        workspace = source or self.source

        env = dag.env().with_workspace(workspace)

        if target:
            env = env.with_string_input("target", target, "Specific file or component to write tests for")
        if test_framework:
            env = env.with_string_input("test_framework", test_framework, "Test framework preference")

        work = await self._build_llm(env, "write_tests_prompt.md", workspace)
        return work.env().workspace()

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
        workspace = source or self.source

        env = dag.env().with_workspace(workspace)

        if command:
            env = env.with_string_input("command", command, "Build command to run")

        work = await self._build_llm(env, "build_prompt.md", workspace)
        return work.env().workspace()

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
        workspace = source or self.source

        env = (
            dag.env()
            .with_workspace(workspace)
            .with_string_input("target_version", target_version, "Target Angular version to upgrade to")
        )

        if dry_run:
            env = env.with_string_input("dry_run", "true", "Only analyze and report, do not modify files")

        work = await self._build_llm(env, "upgrade_prompt.md", workspace)
        return work.env().workspace()

    # --- GitHub integration ---

    @function
    async def develop_github_issue(
        self,
        github_token: Annotated[dagger.Secret, Doc("GitHub token with repo and pull-request permissions")],
        issue_id: Annotated[int, Doc("GitHub issue number")],
        repository: Annotated[str, Doc("GitHub repository URL (e.g. 'https://github.com/owner/repo')")],
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
        base: Annotated[str, Doc("Base branch for the pull request")] = "main",
    ) -> str:
        """Read a GitHub issue, route it to the best agent, and create a Pull Request.

        A router LLM reads the issue and selects the optimal function — assist,
        upgrade, build, or write-tests — then calls it with extracted parameters.
        Comments on the issue with a summary and a link to the PR.
        Returns the PR URL.
        """
        workspace = source or self.source
        gh = dag.github_issue(token=github_token)

        # Read the issue
        issue = gh.read(repository, issue_id)
        title = await issue.title()
        body = await issue.body()
        url = await issue.url()

        # Classify the issue to pick the best agent function
        router_prompt = await self._load_prompt("router_prompt.md").contents()

        router_env = (
            dag.env()
            .with_string_input("issue_title", title, "The GitHub issue title")
            .with_string_input("issue_body", body, "The GitHub issue body")
            .with_string_output("function_name", "The function to call: assist, upgrade, build, or write_tests")
            .with_string_output("params_json", "JSON object with function parameters")
        )

        router = (
            dag.llm()
            .with_env(router_env)
            .with_system_prompt(router_prompt)
            .with_prompt(f"## GitHub Issue: {title}\n\n{body}")
        )

        function_name = await router.env().output("function_name").as_string()
        params_json = await router.env().output("params_json").as_string()
        params = json.loads(params_json)

        # Call the chosen function with extracted parameters
        if function_name == "upgrade":
            result = await self.upgrade(source=workspace, **params)
        elif function_name == "build":
            result = await self.build(source=workspace, **params)
        elif function_name == "write_tests":
            result = await self.write_tests(source=workspace, **params)
        else:
            result = await self.assist(assignment=body, source=workspace)

        # Create a PR from the modified workspace
        pr = gh.create_pull_request(
            repo=repository,
            title=title,
            body=f"{body}\n\nCloses {url}",
            source=result,
            base=base,
        )
        pr_url = await pr.url()

        # Comment on the issue with the PR link
        await gh.write_comment(
            repo=repository,
            issue_id=issue_id,
            body=f"I've implemented this issue and opened a pull request: {pr_url}",
        )

        return pr_url

    # --- Workspace tools (exposed to LLM via with_current_module) ---

    @function
    async def read_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        offset: Annotated[int, Doc("Line number to start reading from (1-based)")] = 0,
        limit: Annotated[int, Doc("Maximum number of lines to read")] = 0,
    ) -> str:
        """Read a file from the workspace with line numbers."""
        contents = await self.source.file(file_path).contents()
        lines = contents.splitlines()

        if offset > 0:
            lines = lines[offset - 1:]
        if limit > 0:
            lines = lines[:limit]

        start = offset if offset > 0 else 1
        numbered = [f"{start + i:4d}  {line}" for i, line in enumerate(lines)]
        return "\n".join(numbered)

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
        before = self.source
        contents = await before.file(file_path).contents()

        if old_string not in contents:
            msg = f"old_string not found in {file_path}"
            raise ValueError(msg)

        if replace_all:
            new_contents = contents.replace(old_string, new_string)
        else:
            new_contents = contents.replace(old_string, new_string, 1)

        after = before.with_new_file(file_path, new_contents)
        self.source = after
        return after.changes(before)

    @function
    async def write_file(
        self,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        contents: Annotated[str, Doc("The full file contents to write")],
    ) -> dagger.Changeset:
        """Create or overwrite a file in the workspace.

        Returns a changeset showing the diff.
        """
        before = self.source
        after = before.with_new_file(file_path, contents)
        self.source = after
        return after.changes(before)

    @function
    async def glob(
        self,
        pattern: Annotated[str, Doc("Glob pattern (e.g. 'src/**/*.ts', '**/*.component.ts')")],
    ) -> str:
        """Find files in the workspace matching a glob pattern."""
        entries = await self.source.glob(pattern)
        if not entries:
            return "No files matched the pattern."
        return "\n".join(entries)

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
        cmd = ["grep", "-rn"]
        if insensitive:
            cmd.append("-i")

        if file_glob:
            cmd.extend(["--include", file_glob])

        cmd.append(pattern)

        if paths:
            cmd.extend(paths.split(","))
        else:
            cmd.append(".")

        result = await (
            dag.container()
            .from_("alpine:latest")
            .with_mounted_directory("/work", self.source)
            .with_workdir("/work")
            .with_exec(cmd, expect=dagger.ExecExpect.ANY)
            .stdout()
        )

        lines = result.strip().splitlines()
        if limit > 0 and len(lines) > limit:
            lines = lines[:limit]
            lines.append(f"... (truncated, {limit} of many matches shown)")

        return "\n".join(lines) if lines else "No matches found."

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
        task_system = await self._load_prompt("task_system_prompt.md").contents()
        context_md = await self._read_context_file()

        env = (
            dag.env()
            .with_workspace(self.source)
            .with_string_input("task_description", description, "The sub-task description")
            .with_string_input("task_prompt", prompt, "Detailed instructions for the sub-task")
            .with_string_output("result", "The sub-task result")
        )

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_mcp_server("angular", self._angular_mcp_service())
            .with_system_prompt(task_system + context_md)
            .with_blocked_function("Angie", "assist")
            .with_blocked_function("Angie", "review")
            .with_blocked_function("Angie", "write_tests")
            .with_blocked_function("Angie", "build")
            .with_blocked_function("Angie", "upgrade")
            .with_blocked_function("Angie", "develop_github_issue")
            .with_blocked_function("Angie", "task")
            .with_prompt(f"## Task: {description}\n\n{prompt}")
        )

        return await llm.env().output("result").as_string()
