"""Angie — AI-powered Angular development agent with MCP integration."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, agent, dag, field, function, object_type

from agent_base import constants, github_tools, llm_helpers, mcp_stdio, routing, workspace
from agent_base.mcp_stdio import McpServer


@object_type
class Angie:
    """AI-powered Angular development agent.

    Uses the Angular CLI MCP server for docs, best practices, build, test,
    and modernize capabilities. Provides workspace tools for reading, editing,
    and searching files.

    Pass your Angular project as --source and use the agent entrypoints
    (assist, review, write-tests, build, upgrade) to work with your code, or
    install the module and run `dagger agent` to work with Angie interactively.
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
    self_improve: Annotated[
        str,
        Doc("Self-improvement mode: 'off' (default), 'write' (update context file), 'commit' (update + git commit)"),
    ] = field(default="off")

    # --- Agent-specific configuration ---

    _CONTEXT_FILES = ("ANGIE.md", "AGENT.md", "CLAUDE.md")
    _CLASS_NAME = "Angie"
    _ALLOWED_ROUTER_KEYS = {
        "upgrade": {"target_version", "dry_run"},
        "build": {"command"},
        "write_tests": {"target", "test_framework"},
    }
    # Exposed fields are tools too in Dagger 1.0; hide them from the LLM
    _FIELDS = ["source", "node_version", "self_improve"]
    # Build/test tools blocked during write_tests to prevent the LLM
    # from running tests instead of writing them (can hang on missing infra)
    _BLOCKED_BUILD_TOOLS = [
        "angular_build", "angular_test", "angular_lint", "angular_install",
    ]

    # Experimental MCP tools needed per task — only load what's relevant.
    # None means no MCP server at all (workspace tools are sufficient).
    _TASK_MCP_TOOLS = {
        "assist": ["build", "test", "modernize"],
        "review": None,         # workspace tools only — MCP can't see files and confuses the LLM
        "write_tests": None,    # workspace tools only — just needs to read code and write test files
        "build": ["build"],
        "upgrade": ["modernize"],
        "suggest_fix": None,
    }

    def _angular_mcp(self, experimental_tools: list[str]) -> McpServer:
        command = ["ng", "mcp"]
        for tool in experimental_tools:
            command.extend(["--experimental-tool", tool])
        return McpServer(
            name="angular",
            container=(
                dag.container()
                .from_(f"node:{self.node_version}")
                .with_mounted_cache("/root/.npm", dag.cache_volume("node-npm"))
                .with_exec(["npm", "install", "-g", "@angular/cli"])
            ),
            command=command,
        )

    def _mcp_servers(self, task: str = "assist") -> list[McpServer]:
        experimental_tools = self._TASK_MCP_TOOLS.get(task, [])
        if experimental_tools is None:
            return []
        return [self._angular_mcp(experimental_tools)]

    def _mcp_server(self, name: str) -> McpServer:
        if name != "angular":
            raise ValueError(f"unknown MCP server {name!r}; the server is 'angular'")
        return self._angular_mcp(self._TASK_MCP_TOOLS["assist"])

    def _load_prompt(self, filename: str) -> dagger.File:
        return dag.current_module().source().file(f"src/angie/prompts/{filename}")

    def _blocked(self, *extra: str) -> list[str]:
        return [*constants.BLOCKED_ENTRYPOINTS, *self._FIELDS, *extra]

    async def _build_llm(self, prompt_file, source, task: str = "assist", inputs=None, extra_blocked=()):
        return await llm_helpers.build_llm(
            source, "system_prompt.md", prompt_file, self._load_prompt,
            self._CONTEXT_FILES, self._mcp_servers(task), self._blocked(*extra_blocked),
            inputs=inputs, self_improve=self.self_improve,
            retry_note=getattr(self, "_retry_note", ""),
        )

    async def _post_process_workspace(self, workspace: dagger.Directory) -> dagger.Directory:
        if self.self_improve == "commit":
            return await llm_helpers.commit_context_file(
                workspace, self._CONTEXT_FILES, self._CLASS_NAME,
            )
        return workspace

    async def _build_suggest_fix_llm(self, source, inputs):
        return await llm_helpers.build_suggest_fix_llm(
            source, self._load_prompt, self._CONTEXT_FILES,
            self._blocked("task", *constants.BLOCKED_DESTRUCTIVE), inputs,
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
        llm = await self._build_llm(
            "assist_prompt.md", source or self.source, task="assist",
            inputs={"assignment": assignment},
        )
        return await self._post_process_workspace(llm_helpers.edited_directory(llm))

    @function
    async def review(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory to review (uses constructor source if omitted)")] = None,
        assignment: Annotated[str, Doc("What to review — task description from a CI orchestrator (optional)")] = "",
        diff: Annotated[str, Doc("Git diff or PR diff to review (optional)")] = "",
        focus: Annotated[str, Doc("Specific area to focus the review on (optional)")] = "",
    ) -> str:
        """Review Angular code for best practices, performance, accessibility, and type safety.

        Provides structured feedback with issues, suggestions, and a summary.
        Returns the review as text (no files modified).
        """
        llm = await self._build_llm(
            "review_prompt.md", source or self.source, task="review",
            inputs={"assignment": assignment, "diff": diff, "focus": focus},
            extra_blocked=constants.BLOCKED_DESTRUCTIVE,
        )
        return await llm_helpers.reply(llm)

    @function
    async def write_tests(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory (uses constructor source if omitted)")] = None,
        assignment: Annotated[str, Doc("What to test — task description from a CI orchestrator (optional)")] = "",
        target: Annotated[str, Doc("Specific file or component to write tests for (optional)")] = "",
        test_framework: Annotated[str, Doc("Test framework preference: 'jest', 'karma', 'vitest' (optional)")] = "",
    ) -> dagger.Directory:
        """Generate unit, integration, or e2e tests for Angular components and services.

        Follows Angular testing patterns and uses the project's existing test setup.
        Returns the workspace directory with generated test files.
        """
        llm = await self._build_llm(
            "write_tests_prompt.md", source or self.source, task="write_tests",
            inputs={"assignment": assignment, "target": target, "test_framework": test_framework},
            extra_blocked=self._BLOCKED_BUILD_TOOLS,
        )
        return await self._post_process_workspace(llm_helpers.edited_directory(llm))

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
        llm = await self._build_llm(
            "build_prompt.md", source or self.source, task="build",
            inputs={"command": command},
        )
        return await self._post_process_workspace(llm_helpers.edited_directory(llm))

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
        inputs = {"target_version": target_version}
        if dry_run:
            inputs["dry_run"] = "true — only analyze and report, do not modify files"
        llm = await self._build_llm("upgrade_prompt.md", source or self.source, task="upgrade", inputs=inputs)
        return await self._post_process_workspace(llm_helpers.edited_directory(llm))

    @function
    @agent
    async def agent(self, base: dagger.LLM, ws: dagger.Workspace) -> dagger.LLM:
        """Angie for `dagger agent`: Angular tools and guidance on the session's workspace."""
        return await llm_helpers.build_agent(
            base, ws, self._load_prompt, self._CONTEXT_FILES,
            self._mcp_servers("assist"), self._blocked(),
        )

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
        return await github_tools.suggest_github_fix_impl(
            self._build_suggest_fix_llm, github_token, pr_number, repo,
            commit_sha, error_output, source or self.source,
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

    # --- Angular build tools ---

    @function
    async def angular_build(
        self,
        ws: dagger.Workspace,
        configuration: Annotated[str, Doc("Build configuration (e.g. 'production', 'development')")] = "production",
        output_path: Annotated[str, Doc("Custom output path (auto-detected from angular.json if empty)")] = "",
    ) -> dagger.Directory:
        """Build the Angular project in the workspace using ng build.

        Returns the dist directory with compiled output.
        """
        return await dag.angular().build(
            source=ws.directory("."),
            configuration=configuration,
            output_path=output_path,
            node_version=self.node_version,
        )

    @function
    async def angular_lint(
        self,
        ws: dagger.Workspace,
        fix: Annotated[bool, Doc("Automatically fix lint errors")] = False,
    ) -> str:
        """Lint the Angular project in the workspace using ng lint.

        Returns the lint output.
        """
        return await dag.angular().lint(
            source=ws.directory("."),
            fix=fix,
            node_version=self.node_version,
        )

    @function
    async def angular_test(self, ws: dagger.Workspace) -> str:
        """Run the tests of the Angular project in the workspace using ng test.

        Returns the test output.
        """
        return await dag.angular().test(
            source=ws.directory("."),
            node_version=self.node_version,
        )

    @function
    async def angular_install(self, ws: dagger.Workspace) -> dagger.Directory:
        """Install the dependencies of the Angular project in the workspace.

        Returns the source directory with node_modules installed.
        """
        return dag.angular().install(
            source=ws.directory("."),
            node_version=self.node_version,
        )

    # --- Workspace tools ---

    @function
    async def read_file(
        self,
        ws: dagger.Workspace,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        offset: Annotated[int, Doc("Line number to start reading from (1-based)")] = 0,
        limit: Annotated[int, Doc("Maximum number of lines to read")] = 0,
    ) -> str:
        """Read a file from the workspace with line numbers."""
        return await workspace.read_file_impl(ws, file_path, offset, limit)

    @function
    async def edit_file(
        self,
        ws: dagger.Workspace,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        old_string: Annotated[str, Doc("The exact string to find and replace")],
        new_string: Annotated[str, Doc("The replacement string")],
        replace_all: Annotated[bool, Doc("Replace all occurrences (default: first only)")] = False,
    ) -> dagger.Workspace:
        """Edit a file by replacing a string. The old_string must match exactly.

        Returns the edited workspace.
        """
        return await workspace.edit_file_impl(ws, file_path, old_string, new_string, replace_all)

    @function
    def write_file(
        self,
        ws: dagger.Workspace,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        contents: Annotated[str, Doc("The full file contents to write")],
    ) -> dagger.Workspace:
        """Create or overwrite a file in the workspace.

        Returns the edited workspace.
        """
        return workspace.write_file_impl(ws, file_path, contents)

    @function
    async def glob(
        self,
        ws: dagger.Workspace,
        pattern: Annotated[str, Doc("Glob pattern (e.g. 'src/**/*.ts', '**/*.component.ts')")],
    ) -> str:
        """Find files in the workspace matching a glob pattern."""
        return await workspace.glob_impl(ws, pattern)

    @function
    async def grep(
        self,
        ws: dagger.Workspace,
        pattern: Annotated[str, Doc("Search pattern (regex supported)")],
        paths: Annotated[str, Doc("Comma-separated paths to search in (optional)")] = "",
        file_glob: Annotated[str, Doc("Glob pattern to filter files (e.g. '*.ts')")] = "",
        insensitive: Annotated[bool, Doc("Case-insensitive search")] = False,
        limit: Annotated[int, Doc("Maximum number of matching lines to return")] = 100,
    ) -> str:
        """Search file contents in the workspace using grep."""
        return await workspace.grep_impl(ws, pattern, paths, file_glob, insensitive, limit)

    @function
    async def mcp(
        self,
        server: Annotated[str, Doc("MCP server name, as listed in the system prompt (e.g. 'angular')")],
        tool: Annotated[str, Doc("Name of the server's tool to call")],
        arguments: Annotated[str, Doc("The tool's arguments, as a JSON object")] = "{}",
    ) -> str:
        """Call a tool of one of the MCP servers listed in the system prompt."""
        return await mcp_stdio.call(self._mcp_server(server), tool, arguments)

    # --- Task sub-agent ---

    @function
    async def task(
        self,
        ws: dagger.Workspace,
        description: Annotated[str, Doc("Short description of the sub-task")],
        prompt: Annotated[str, Doc("Detailed prompt for the sub-agent")],
    ) -> str:
        """Launch a sub-agent for research or focused work.

        The sub-agent has read-only access to the workspace and Angular MCP tools.
        Use this for research, analysis, or exploring documentation.
        """
        llm = await llm_helpers.build_task_llm(
            ws, self._load_prompt, self._CONTEXT_FILES,
            self._mcp_servers(task="review"),
            self._blocked("task", *constants.BLOCKED_DESTRUCTIVE, *self._BLOCKED_BUILD_TOOLS),
            description, prompt,
        )
        return await llm_helpers.reply(llm)
