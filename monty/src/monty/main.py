"""Monty — AI-powered Python development agent with MCP integration."""

import json
import re
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, field, function, object_type

# Entrypoints blocked on all LLMs to prevent recursion
_BLOCKED_ENTRYPOINTS = [
    "assist", "review", "write_tests", "build",
    "upgrade", "develop_github_issue", "suggest_github_fix",
]

# Destructive tools blocked on the read-only sub-agent
_BLOCKED_DESTRUCTIVE = ["edit_file", "write_file", "suggest_github_pr_code_comment"]


@object_type
class Monty:
    """AI-powered Python development agent.

    Uses the python-lft MCP server for linting, formatting, and testing,
    and the pypi-query MCP server for dependency intelligence and security
    auditing. Provides workspace tools for reading, editing, and searching
    files.

    Pass your Python project as --source and use the agent entrypoints
    (assist, review, write-tests, build, upgrade) to work with your code.
    """

    source: Annotated[
        dagger.Directory,
        Doc("Python project source directory"),
        DefaultPath("/"),
    ] = field()
    python_version: Annotated[
        str,
        Doc("Python version for the MCP server containers"),
    ] = field(default="3.13")

    # Private fields set during suggest_github_fix execution
    _github_token: dagger.Secret | None = field(default=None, init=False)
    _pr_repo: str = field(default="", init=False)
    _pr_number: int = field(default=0, init=False)
    _pr_commit_sha: str = field(default="", init=False)

    # --- Python MCP integration ---

    def _python_lft_mcp_service(self) -> dagger.Service:
        """Create the python-lft MCP server (lint, format, test) as a Dagger Service."""
        return (
            dag.container()
            .from_(f"python:{self.python_version}-slim")
            .with_exec(["apt-get", "update", "-qq"])
            .with_exec(["apt-get", "install", "-y", "-qq", "git"])
            .with_exec(["pip", "install", "--no-cache-dir", "python-lft-mcp[tools] @ git+https://github.com/Agent-Hellboy/python-lft-mcp.git"])
            .with_default_args(["python", "-m", "python_lft"])
            .as_service()
        )

    def _pypi_mcp_service(self) -> dagger.Service:
        """Create the pypi-query MCP server (package intelligence) as a Dagger Service."""
        return (
            dag.container()
            .from_(f"python:{self.python_version}-slim")
            .with_exec(["pip", "install", "--no-cache-dir", "pypi-query-mcp-server"])
            .with_default_args(["pypi-query-mcp-server"])
            .as_service()
        )

    # --- Prompt helpers ---

    def _load_prompt(self, filename: str) -> dagger.File:
        """Load a prompt file from the module source."""
        return dag.current_module().source().file(
            f"src/monty/prompts/{filename}"
        )

    _MAX_CONTEXT_CHARS = 4000  # ~1000 tokens — keeps total prompt under budget

    async def _read_context_file(self, source: dagger.Directory | None = None) -> str:
        """Read per-repo context from MONTY.md, AGENT.md, or CLAUDE.md."""
        target = source or self.source
        entries = await target.entries()
        for name in ("MONTY.md", "AGENT.md", "CLAUDE.md"):
            if name in entries:
                contents = await target.file(name).contents()
                if len(contents) > self._MAX_CONTEXT_CHARS:
                    contents = contents[:self._MAX_CONTEXT_CHARS] + "\n\n[Context file truncated to fit token budget.]"
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
            .with_mcp_server("python-lft", self._python_lft_mcp_service())
            .with_mcp_server("pypi", self._pypi_mcp_service())
            .with_system_prompt(system_prompt + context_md)
        )

        for fn in _BLOCKED_ENTRYPOINTS:
            llm = llm.with_blocked_function("Monty", fn)

        return llm.with_prompt_file(self._load_prompt(prompt_file))

    async def _build_suggest_fix_llm(
        self,
        env: dagger.Env,
        source: dagger.Directory | None = None,
    ) -> dagger.LLM:
        """Build an LLM for suggest-github-fix (no MCP servers, workspace + suggestion tool)."""
        context_md = await self._read_context_file(source)
        system_prompt = await self._load_prompt("system_prompt.md").contents()

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(system_prompt + context_md)
        )

        for fn in _BLOCKED_ENTRYPOINTS + ["task"] + _BLOCKED_DESTRUCTIVE:
            if fn != "suggest_github_pr_code_comment":
                llm = llm.with_blocked_function("Monty", fn)

        return llm.with_prompt_file(self._load_prompt("suggest_fix_prompt.md"))

    # --- Agent entrypoints ---

    @function
    async def assist(
        self,
        assignment: Annotated[str, Doc("What you want the agent to do (e.g. 'Add a FastAPI endpoint with Pydantic validation')")],
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
    ) -> dagger.Directory:
        """General Python coding assistant.

        Reads code, answers questions, implements features, refactors,
        and uses Python MCP tools for linting, formatting, and package info.
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
        """Review Python code for best practices, performance, security, and type safety.

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
        target: Annotated[str, Doc("Specific file or module to write tests for (optional)")] = "",
        test_framework: Annotated[str, Doc("Test framework preference: 'pytest', 'unittest' (optional)")] = "",
    ) -> dagger.Directory:
        """Generate unit, integration, or e2e tests for Python modules and packages.

        Follows Python testing patterns and uses the project's existing test setup.
        Returns the workspace directory with generated test files.
        """
        workspace = source or self.source

        env = dag.env().with_workspace(workspace)

        if target:
            env = env.with_string_input("target", target, "Specific file or module to write tests for")
        if test_framework:
            env = env.with_string_input("test_framework", test_framework, "Test framework preference")

        work = await self._build_llm(env, "write_tests_prompt.md", workspace)
        return work.env().workspace()

    @function
    async def build(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory (uses constructor source if omitted)")] = None,
        command: Annotated[str, Doc("Build command to run (e.g. 'pip install -e .[dev]', 'python -m build')")] = "",
    ) -> dagger.Directory:
        """Build, lint, or type-check a Python project.

        Diagnoses build errors and suggests fixes using Python MCP tools.
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
        target_package: Annotated[str, Doc("Package to upgrade (e.g. 'django', 'fastapi', 'all')")],
        target_version: Annotated[str, Doc("Target version (e.g. '5.0', '0.115.0', 'latest')")] = "latest",
        source: Annotated[dagger.Directory | None, Doc("Source directory (uses constructor source if omitted)")] = None,
        dry_run: Annotated[bool, Doc("Analyze and report changes without modifying files")] = False,
    ) -> dagger.Directory:
        """Upgrade Python dependencies to a target version.

        Detects the current version, researches breaking changes and
        migration steps between versions, analyzes the codebase for impacted
        code, and applies the necessary modifications.
        Returns the workspace directory with upgrade changes applied.
        """
        workspace = source or self.source

        env = (
            dag.env()
            .with_workspace(workspace)
            .with_string_input("target_package", target_package, "Package to upgrade")
            .with_string_input("target_version", target_version, "Target version to upgrade to")
        )

        if dry_run:
            env = env.with_string_input("dry_run", "true", "Only analyze and report, do not modify files")

        work = await self._build_llm(env, "upgrade_prompt.md", workspace)
        return work.env().workspace()

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
        workspace = source or self.source

        # Store PR state for the suggestion tool
        self._github_token = github_token
        self._pr_repo = repo
        self._pr_number = pr_number
        self._pr_commit_sha = commit_sha

        # Truncate error output (keep tail — most relevant)
        max_error_chars = 8000
        if len(error_output) > max_error_chars:
            error_output = "...(truncated)\n" + error_output[-max_error_chars:]

        env = (
            dag.env()
            .with_string_input("error_output", error_output, "The CI error output to analyze")
            .with_string_input("pr_number", str(pr_number), "The pull request number")
            .with_string_input("repo", repo, "The GitHub repository URL")
            .with_string_input("commit_sha", commit_sha, "The HEAD commit SHA of the PR")
            .with_string_output("result", "Summary of suggestions posted")
        )

        if source:
            self.source = source
        if workspace:
            env = env.with_workspace(workspace)

        work = await self._build_suggest_fix_llm(env, workspace)
        return await work.env().output("result").as_string()

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

        function_name = (await router.env().output("function_name").as_string()).strip().lower()
        params_json = await router.env().output("params_json").as_string()

        # Parse JSON with fallback for malformed LLM output (code fences, trailing text)
        try:
            params = json.loads(params_json)
        except (json.JSONDecodeError, TypeError):
            match = re.search(r"\{[^}]*\}", params_json or "")
            if match:
                try:
                    params = json.loads(match.group())
                except json.JSONDecodeError:
                    params = {}
                    function_name = "assist"
            else:
                params = {}
                function_name = "assist"

        # Filter params to expected keys per function to prevent TypeErrors
        _allowed_keys = {
            "upgrade": {"target_package", "target_version"},
            "build": {"command"},
            "write_tests": {"target", "test_framework"},
        }
        allowed = _allowed_keys.get(function_name, set())
        params = {k: v for k, v in params.items() if k in allowed}

        try:
            # Call the chosen function with extracted parameters
            if function_name == "upgrade":
                result = await self.upgrade(source=workspace, **params)
            elif function_name == "build":
                result = await self.build(source=workspace, **params)
            elif function_name == "write_tests":
                result = await self.write_tests(source=workspace, **params)
            else:
                result = await self.assist(assignment=body, source=workspace)
        except Exception as exc:
            if suggest_github_fix_on_failure:
                await gh.write_comment(
                    repo=repository,
                    issue_id=issue_id,
                    body=(
                        f"**Agent encountered an error:**\n\n"
                        f"**Function**: `{function_name}`\n"
                        f"**Error**:\n```\n{str(exc)[:3000]}\n```\n\n"
                        f"Run `suggest-github-fix` on the PR for inline code suggestions."
                    ),
                )
            raise

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

    # --- GitHub suggestion tool (exposed to LLM via with_current_module) ---

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
        if not self._github_token or not self._pr_repo:
            raise ValueError("suggest_github_pr_code_comment can only be used during suggest_github_fix")

        body = ""
        if comment:
            body += f"{comment}\n\n"
        body += f"```suggestion\n{suggestion}\n```"

        gh = dag.github_issue(token=self._github_token)
        await gh.write_pull_request_code_comment(
            repo=self._pr_repo,
            issue_id=self._pr_number,
            commit=self._pr_commit_sha,
            body=body,
            path=path,
            side="RIGHT",
            line=line,
        )
        return f"Posted suggestion on {path}:{line}"

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
        pattern: Annotated[str, Doc("Glob pattern (e.g. 'src/**/*.py', '**/*.toml')")],
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
        file_glob: Annotated[str, Doc("Glob pattern to filter files (e.g. '*.py')")] = "",
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

        The sub-agent has read-only access to the workspace and Python MCP tools.
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
            .with_mcp_server("python-lft", self._python_lft_mcp_service())
            .with_mcp_server("pypi", self._pypi_mcp_service())
            .with_system_prompt(task_system + context_md)
        )

        # Block entrypoints (prevent recursion) and destructive tools (read-only sub-agent)
        for fn in _BLOCKED_ENTRYPOINTS + ["task"] + _BLOCKED_DESTRUCTIVE:
            llm = llm.with_blocked_function("Monty", fn)

        llm = llm.with_prompt(f"## Task: {description}\n\n{prompt}")

        return await llm.env().output("result").as_string()
