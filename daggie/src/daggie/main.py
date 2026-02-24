"""Daggie — AI-powered Dagger CI specialist agent."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, field, function, object_type

from agent_base import constants, github_tools, llm_helpers, routing, workspace

# File patterns to read from cloned Dagger modules
_MODULE_SOURCE_GLOBS = [
    "dagger.json",
    "src/**/main.py",
    "src/**/main.ts",
    "main.go",
    "src/**/main.go",
    "dagger/src/**/*.ts",
]


def _parse_module_url(url: str) -> tuple[str, str, str]:
    """Parse a Dagger module Git URL into (repo_url, branch, path).

    Supports "url#branch:path", "url#branch", and plain "url" formats.
    """
    if "#" in url:
        repo_url, ref_part = url.split("#", 1)
        if ":" in ref_part:
            branch, path = ref_part.split(":", 1)
        else:
            branch = ref_part
            path = ""
    else:
        repo_url = url
        branch = "main"
        path = ""
    return repo_url, branch, path


async def _read_module_tree(tree: dagger.Directory) -> str:
    """Read key files from a cloned Dagger module and return formatted docs."""
    sections = []

    for pattern in _MODULE_SOURCE_GLOBS:
        matches = await tree.glob(pattern)
        for path in matches:
            try:
                contents = await tree.file(path).contents()
                # Truncate very large files
                if len(contents) > 6000:
                    contents = contents[:6000] + "\n... (truncated)"
                sections.append(f"### {path}\n```\n{contents}\n```")
            except Exception:
                continue

    return "\n\n".join(sections)


@object_type
class Daggie:
    """AI-powered Dagger CI specialist agent.

    Specializes in creating, explaining, and debugging Dagger CI modules
    and pipelines across all SDKs (Python, TypeScript, Go, Java).

    Accepts Git URLs of Dagger modules at runtime, clones them via dag.git(),
    reads their source code, and uses that knowledge to propose implementations.

    Pass your project as --source and optionally reference Dagger modules via
    --module-urls for the agent to learn from.
    """

    source: Annotated[
        dagger.Directory,
        Doc("Project source directory"),
        DefaultPath("/"),
    ] = field()
    module_urls: Annotated[
        list[str],
        Doc("Git URLs of Dagger modules to clone and read for reference (e.g. 'https://github.com/org/repo.git#main:path/to/module')"),
    ] = field(default=list)

    # Private fields set during suggest_github_fix execution
    _github_token: dagger.Secret | None = field(default=None, init=False)
    _pr_repo: str = field(default="", init=False)
    _pr_number: int = field(default=0, init=False)
    _pr_commit_sha: str = field(default="", init=False)

    # --- Agent-specific configuration ---

    _CONTEXT_FILES = ("DAGGIE.md", "DAGGER.md", "AGENT.md", "CLAUDE.md")
    _CLASS_NAME = "Daggie"
    _ALLOWED_ROUTER_KEYS = {
        "explain": {},
        "debug": {"error_output"},
    }
    # Agent-specific entrypoints to block (in addition to shared BLOCKED_ENTRYPOINTS)
    # NOTE: Only block functions that exist on Daggie. Blocking non-existent
    # functions (write_tests, build, upgrade) makes the LLM aware of them and
    # causes hallucinated calls. Override shared list with Daggie-specific one.
    _BLOCKED_EXTRA = ["explain", "debug", "read_module"]
    _BLOCKED_ENTRYPOINTS = [
        "assist", "review", "develop_github_issue", "suggest_github_fix",
    ]

    # Per-task MCP configuration — schema introspection helps for creation/explanation/debugging
    _TASK_MCP_TOOLS = {
        "assist": True,
        "explain": True,
        "debug": True,
        "review": False,
    }

    def _mcp_servers(self, task: str = "assist") -> dict[str, dagger.Service]:
        if not self._TASK_MCP_TOOLS.get(task, False):
            return {}
        return {"dagger": dag.dagger_mcp().server()}

    def _load_prompt(self, filename: str) -> dagger.File:
        return dag.current_module().source().file(f"src/daggie/prompts/{filename}")

    async def _load_module_sources(self) -> str:
        """Clone and read all referenced Dagger modules."""
        if not self.module_urls:
            return ""

        sections = []
        for url in self.module_urls:
            try:
                repo_url, branch, path = _parse_module_url(url)
                tree = dag.git(repo_url).branch(branch).tree()
                if path:
                    tree = tree.directory(path)

                module_docs = await _read_module_tree(tree)
                if module_docs:
                    sections.append(f"## Reference Module: {url}\n\n{module_docs}")
            except Exception as exc:
                sections.append(f"## Reference Module: {url}\n\n*Failed to clone: {exc}*")

        if not sections:
            return ""

        return "\n\n---\n\n# Pre-loaded Module References\n\n" + "\n\n---\n\n".join(sections)

    async def _build_llm(self, env, prompt_file, source=None, task: str = "assist", extra_blocked=None):
        # Load module sources and inject as context
        module_context = await self._load_module_sources()
        context_md = await llm_helpers.read_context_file(
            source or self.source, self._CONTEXT_FILES,
        )
        system_prompt = await self._load_prompt("system_prompt.md").contents()
        full_system = system_prompt + context_md + module_context

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(full_system)
        )

        for name, service in self._mcp_servers(task).items():
            llm = llm.with_mcp_server(name, service)

        for fn in self._BLOCKED_ENTRYPOINTS + self._BLOCKED_EXTRA + (extra_blocked or []):
            llm = llm.with_blocked_function(self._CLASS_NAME, fn)

        return llm.with_prompt_file(self._load_prompt(prompt_file))

    async def _build_suggest_fix_llm(self, env, source=None):
        module_context = await self._load_module_sources()
        context_md = await llm_helpers.read_context_file(
            source or self.source, self._CONTEXT_FILES,
        )
        system_prompt = await self._load_prompt("system_prompt.md").contents()
        full_system = system_prompt + context_md + module_context

        llm = (
            dag.llm()
            .with_env(env.with_current_module())
            .with_system_prompt(full_system)
        )

        for fn in self._BLOCKED_ENTRYPOINTS + self._BLOCKED_EXTRA + ["task"] + constants.BLOCKED_DESTRUCTIVE:
            if fn != "suggest_github_pr_code_comment":
                llm = llm.with_blocked_function(self._CLASS_NAME, fn)

        return llm.with_prompt_file(self._load_prompt("suggest_fix_prompt.md"))

    # --- Agent entrypoints ---

    @function
    async def assist(
        self,
        assignment: Annotated[str, Doc("What you want the agent to do (e.g. 'Create a Dagger pipeline for building and testing a Python project')")],
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
    ) -> dagger.Directory:
        """Create Dagger pipelines and modules, implement features.

        Reads reference modules, understands your project, and implements
        Dagger CI pipelines. Returns the modified workspace directory.
        """
        ws = source or self.source
        env = (
            dag.env()
            .with_workspace(ws)
            .with_string_input("assignment", assignment, "The coding task to accomplish")
        )
        return (await self._build_llm(env, "assist_prompt.md", ws, task="assist")).env().workspace()

    @function
    async def explain(
        self,
        question: Annotated[str, Doc("What you want explained (e.g. 'How does caching work in Dagger?')")],
        source: Annotated[dagger.Directory | None, Doc("Source directory to reference (optional)")] = None,
    ) -> str:
        """Explain Dagger modules, CLI commands, pipeline patterns, and concepts.

        Reads reference modules and source code to provide clear explanations
        with code examples. Returns the explanation as text.
        """
        ws = source or self.source
        env = (
            dag.env()
            .with_workspace(ws)
            .with_string_input("question", question, "The question to answer")
            .with_string_output("result", "The explanation")
        )
        work = await self._build_llm(env, "explain_prompt.md", ws, task="explain")
        return await llm_helpers.get_result_or_last_reply(work)

    @function
    async def debug(
        self,
        error_output: Annotated[str, Doc("Pipeline error output (stderr/stdout from dagger call)")],
        source: Annotated[dagger.Directory | None, Doc("Source directory with the broken module (optional)")] = None,
    ) -> dagger.Directory:
        """Diagnose and fix Dagger pipeline errors.

        Analyzes error output, reads relevant source files, identifies the
        root cause, and applies fixes. Returns the modified workspace directory.
        """
        ws = source or self.source
        # Truncate error output (keep tail — most relevant)
        max_error_chars = 8000
        if len(error_output) > max_error_chars:
            error_output = "...(truncated)\n" + error_output[-max_error_chars:]

        env = (
            dag.env()
            .with_workspace(ws)
            .with_string_input("error_output", error_output, "The pipeline error output to diagnose")
        )
        return (await self._build_llm(env, "debug_prompt.md", ws, task="debug")).env().workspace()

    @function
    async def review(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory to review (uses constructor source if omitted)")] = None,
        diff: Annotated[str, Doc("Git diff or PR diff to review (optional)")] = "",
        focus: Annotated[str, Doc("Specific area to focus the review on (optional)")] = "",
    ) -> str:
        """Review Dagger module code for quality, best practices, and correctness.

        Checks function signatures, caching strategies, error handling,
        SDK patterns, and dagger.json configuration. Returns structured feedback.
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
        work = await self._build_llm(env, "review_prompt.md", ws, task="review")
        return await llm_helpers.get_result_or_last_reply(work)

    # --- Domain tool ---

    @function
    async def read_module(
        self,
        url: Annotated[str, Doc("Git URL of a Dagger module (e.g. 'https://github.com/org/repo.git#main:path/to/module')")],
    ) -> str:
        """Read a Dagger module from a Git repository.

        Clones the repo, reads dagger.json and main source files,
        and returns formatted module documentation. Use this to learn
        from existing Dagger modules when implementing new ones.
        """
        repo_url, branch, path = _parse_module_url(url)
        tree = dag.git(repo_url).branch(branch).tree()
        if path:
            tree = tree.directory(path)

        module_docs = await _read_module_tree(tree)
        if not module_docs:
            return f"No Dagger module files found at {url}"

        return f"# Module: {url}\n\n{module_docs}"

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
        explain, or debug — then calls it with extracted parameters.
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
        pattern: Annotated[str, Doc("Glob pattern (e.g. 'src/**/*.py', '**/*.go', '**/dagger.json')")],
    ) -> str:
        """Find files in the workspace matching a glob pattern."""
        return await workspace.glob_impl(self.source, pattern)

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
        return await workspace.grep_impl(self.source, pattern, paths, file_glob, insensitive, limit)

    # --- Task sub-agent ---

    @function
    async def task(
        self,
        description: Annotated[str, Doc("Short description of the sub-task")],
        prompt: Annotated[str, Doc("Detailed prompt for the sub-agent")],
    ) -> str:
        """Launch a sub-agent for research or focused work.

        The sub-agent has read-only access to the workspace.
        Use this for research, analysis, or exploring documentation.
        """
        llm = await llm_helpers.build_task_llm(
            self.source, self._load_prompt, self._CONTEXT_FILES,
            self._mcp_servers(task="review"), self._CLASS_NAME,
            self._BLOCKED_ENTRYPOINTS + self._BLOCKED_EXTRA,
            constants.BLOCKED_DESTRUCTIVE,
            description, prompt,
        )
        return await llm_helpers.get_result_or_last_reply(llm)
