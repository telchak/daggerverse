"""Daggie — AI-powered Dagger CI specialist agent."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, agent, dag, field, function, object_type

from agent_base import constants, github_tools, llm_helpers, mcp_stdio, routing, workspace
from agent_base.mcp_stdio import McpServer

_DAGGER_CONFIG_FILE = "DAGGER.md"
_DAGGER_ACTION_FALLBACK_VERSION = "v8.4.1"

# Module manifests: dagger-module.toml since Dagger 1.0, dagger.json before it
_MODULE_MANIFESTS = ("dagger-module.toml", "dagger.json")

# File patterns to read from cloned Dagger modules
_MODULE_SOURCE_GLOBS = [
    *_MODULE_MANIFESTS,
    "*.dang",
    "src/*/__init__.py",
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


def _reference_tree(repo_url: str, branch: str) -> dagger.Directory:
    """A reference repository at the live head of a branch.

    `no_lock` keeps these reads out of the caller's dagger.lock: a reference
    module is read to learn from, not pinned as a dependency.
    """
    return dag.git(repo_url).branch(branch, no_lock=True).tree()


async def _fetch_repo_tags(repo_url: str) -> list[str]:
    """Fetch all Git tags from a remote repository via git ls-remote."""
    try:
        output = await (
            dag.container()
            .from_("alpine/git:latest")
            .with_exec(["git", "ls-remote", "--tags", "--refs", repo_url])
            .stdout()
        )
        # Parse "sha\trefs/tags/tag-name" lines → ["tag-name", ...]
        tags = []
        for line in output.strip().splitlines():
            if "\trefs/tags/" in line:
                tag = line.split("refs/tags/", 1)[1]
                tags.append(tag)
        return sorted(tags)
    except Exception:
        return []


async def _module_dirs(tree: dagger.Directory) -> list[str]:
    """Directories of a repository that hold a module manifest, in path order.

    A 1.0 module commits its vendored SDK and generated clients, so manifests
    under ``sdk/`` and ``clients/`` belong to generated code, not to modules.
    """
    dirs: set[str] = set()
    for manifest in _MODULE_MANIFESTS:
        for path in await tree.glob(f"**/{manifest}"):
            parts = path.split("/")[:-1]
            if "sdk" in parts or "clients" in parts:
                continue
            dirs.add("/".join(parts))
    return sorted(dirs)


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

    Accepts Git URLs of Dagger module repositories at runtime, clones them via
    dag.git(), and auto-discovers all modules within (by finding dagger-module.toml
    or, for Dagger 0.x modules, dagger.json files).
    You can also point to a specific module with the url#branch:path format.

    Pass your project as --source and optionally reference Dagger modules via
    --module-urls for the agent to learn from, or install the module and run
    `dagger agent` to work with Daggie interactively.
    """

    source: Annotated[
        dagger.Directory,
        Doc("Project source directory"),
        DefaultPath("/"),
    ] = field()
    module_urls: Annotated[
        list[str],
        Doc("Git URLs of Dagger module repositories to clone and read for reference. "
            "Points to a repo root to auto-discover all modules (e.g. 'https://github.com/org/modules.git'), "
            "or to a specific module with 'url#branch:path' (e.g. 'https://github.com/org/repo.git#main:my-module')"),
    ] = field(default=list)
    self_improve: Annotated[
        str,
        Doc("Self-improvement mode: 'off' (default), 'write' (update context file), 'commit' (update + git commit)"),
    ] = field(default="off")

    # --- Agent-specific configuration ---

    _CONTEXT_FILES = ("DAGGIE.md", _DAGGER_CONFIG_FILE, "AGENT.md", "CLAUDE.md")
    _CLASS_NAME = "Daggie"
    _ALLOWED_ROUTER_KEYS = {
        "explain": {},
        "debug": {"error_output"},
    }
    # Exposed fields are tools too in Dagger 1.0; hide them from the LLM
    _FIELDS = ["source", "module_urls", "self_improve"]
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

    def _dagger_mcp(self) -> McpServer:
        return McpServer(
            name="dagger",
            container=dag.dagger_mcp().container(),
            command=["python", "main.py"],
            # Queries read the live engine; the server calls it through Dagger-in-Dagger
            live=True,
            dagger_access=True,
        )

    def _mcp_servers(self, task: str = "assist") -> list[McpServer]:
        if not self._TASK_MCP_TOOLS.get(task, False):
            return []
        return [self._dagger_mcp()]

    def _mcp_server(self, name: str) -> McpServer:
        if name != "dagger":
            raise ValueError(f"unknown MCP server {name!r}; the server is 'dagger'")
        return self._dagger_mcp()

    def _load_prompt(self, filename: str) -> dagger.File:
        return dag.current_module().source().file(f"src/daggie/prompts/{filename}")

    def _blocked(self, *extra: str) -> list[str]:
        return [*self._BLOCKED_ENTRYPOINTS, *self._BLOCKED_EXTRA, *self._FIELDS, *extra]

    async def _load_module_sources(self) -> str:
        """Clone and read all referenced Dagger modules.

        When a URL points to a repository root (no path), auto-discovers
        all Dagger modules by finding their manifests in the tree.
        When a URL includes a path, reads only that specific module.

        Also fetches Git tags from each repository so the agent knows
        available versions for module and dependency pinning.
        """
        if not self.module_urls:
            return ""

        sections = []
        for url in self.module_urls:
            try:
                repo_url, branch, path = _parse_module_url(url)
                tree = _reference_tree(repo_url, branch)

                # Fetch available version tags from the repository
                tags = await _fetch_repo_tags(repo_url)
                tags_section = ""
                if tags:
                    tags_section = "\n\n### Available version tags\n```\n" + "\n".join(tags) + "\n```"

                if path:
                    # Explicit path — read that single module
                    module_tree = tree.directory(path)
                    module_docs = await _read_module_tree(module_tree)
                    if module_docs:
                        sections.append(f"## Reference Module: {url} ({path})\n\n{module_docs}{tags_section}")
                else:
                    # No path — auto-discover all modules in the repo
                    module_dirs = await _module_dirs(tree)
                    # Add tags once at the repo level, before individual modules
                    if tags_section:
                        sections.append(f"## Repository: {repo_url}{tags_section}")
                    for module_dir in module_dirs:
                        module_tree = tree.directory(module_dir) if module_dir else tree
                        module_docs = await _read_module_tree(module_tree)
                        if module_docs:
                            label = module_dir or repo_url
                            sections.append(f"## Reference Module: {label}\n\n{module_docs}")
            except Exception as exc:
                sections.append(f"## Reference Module: {url}\n\n*Failed to clone: {exc}*")

        # Fetch latest dagger-for-github action version
        action_tags = await _fetch_repo_tags("https://github.com/dagger/dagger-for-github.git")
        action_version = _DAGGER_ACTION_FALLBACK_VERSION
        if action_tags:
            # Filter to vN.N.N tags (ignore pre-releases, rc, etc.)
            version_tags = [t for t in action_tags if t.startswith("v") and t.count(".") == 2 and all(p.isdigit() for p in t[1:].split("."))]
            if version_tags:
                action_version = version_tags[-1]  # sorted, last = latest
        sections.append(
            f"## GitHub Action: dagger/dagger-for-github\n\n"
            f"Latest stable version tag: **{action_version}**\n"
            f"Use `dagger/dagger-for-github@{action_version}` in all workflow files."
        )

        if not sections:
            return ""

        return "\n\n---\n\n# Pre-loaded Module References\n\n" + "\n\n---\n\n".join(sections)

    async def _build_llm(self, prompt_file, source, task: str = "assist", inputs=None, extra_blocked=()):
        return await llm_helpers.build_llm(
            source, "system_prompt.md", prompt_file, self._load_prompt,
            self._CONTEXT_FILES, self._mcp_servers(task), self._blocked(*extra_blocked),
            inputs=inputs, self_improve=self.self_improve,
            extra_read_files=(_DAGGER_CONFIG_FILE,),
            extra_context=await self._load_module_sources(),
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
            extra_read_files=(_DAGGER_CONFIG_FILE,),
            extra_context=await self._load_module_sources(),
        )

    # --- Agent entrypoints ---

    @function
    async def assist(
        self,
        assignment: Annotated[str, Doc("What you want the agent to do (e.g. 'Create a Dagger pipeline for building and testing a Python project')")] = "",
        assignment_file: Annotated[dagger.File | None, Doc("File containing the assignment instructions (used if --assignment is not set)")] = None,
        source: Annotated[dagger.Directory | None, Doc("Override source directory (uses constructor source if omitted)")] = None,
    ) -> dagger.Directory:
        """Create Dagger pipelines and modules, implement features.

        Reads reference modules, understands your project, and implements
        Dagger CI pipelines. Returns the modified workspace directory.

        Provide instructions via --assignment (takes precedence) or
        --assignment-file for longer/structured prompts.
        """
        if not assignment and assignment_file:
            assignment = await assignment_file.contents()
        if not assignment:
            msg = "Provide either --assignment or --assignment-file"
            raise ValueError(msg)

        llm = await self._build_llm(
            "assist_prompt.md", source or self.source, task="assist",
            inputs={"assignment": assignment},
        )
        return await self._post_process_workspace(llm_helpers.edited_directory(llm))

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
        llm = await self._build_llm(
            "explain_prompt.md", source or self.source, task="explain",
            inputs={"question": question},
            extra_blocked=constants.BLOCKED_DESTRUCTIVE,
        )
        return await llm_helpers.reply(llm)

    @function
    async def debug(
        self,
        error_output: Annotated[str, Doc("Pipeline error output (stderr/stdout from dagger api call)")],
        source: Annotated[dagger.Directory | None, Doc("Source directory with the broken module (optional)")] = None,
    ) -> dagger.Directory:
        """Diagnose and fix Dagger pipeline errors.

        Analyzes error output, reads relevant source files, identifies the
        root cause, and applies fixes. Returns the modified workspace directory.
        """
        llm = await self._build_llm(
            "debug_prompt.md", source or self.source, task="debug",
            inputs={"error_output": github_tools.truncate_error_output(error_output)},
        )
        return await self._post_process_workspace(llm_helpers.edited_directory(llm))

    @function
    async def review(
        self,
        source: Annotated[dagger.Directory | None, Doc("Source directory to review (uses constructor source if omitted)")] = None,
        diff: Annotated[str, Doc("Git diff or PR diff to review (optional)")] = "",
        focus: Annotated[str, Doc("Specific area to focus the review on (optional)")] = "",
    ) -> str:
        """Review Dagger module code for quality, best practices, and correctness.

        Checks function signatures, caching strategies, error handling,
        SDK patterns, and module and workspace configuration. Returns structured feedback.
        """
        llm = await self._build_llm(
            "review_prompt.md", source or self.source, task="review",
            inputs={"diff": diff, "focus": focus},
            extra_blocked=constants.BLOCKED_DESTRUCTIVE,
        )
        return await llm_helpers.reply(llm)

    @function
    @agent
    async def agent(self, base: dagger.LLM, ws: dagger.Workspace) -> dagger.LLM:
        """Daggie for `dagger agent`: Dagger know-how and tools on the session's workspace."""
        return await llm_helpers.build_agent(
            base, ws, self._load_prompt, self._CONTEXT_FILES,
            self._mcp_servers("assist"), self._blocked(),
            extra_read_files=(_DAGGER_CONFIG_FILE,),
        )

    # --- Domain tool ---

    @function
    async def read_module(
        self,
        url: Annotated[str, Doc("Git URL of a Dagger module (e.g. 'https://github.com/org/repo.git#main:path/to/module')")],
    ) -> str:
        """Read a Dagger module from a Git repository.

        Clones the repo, reads the module manifest (dagger-module.toml or
        dagger.json) and main source files, and returns formatted module
        documentation. Use this to learn from existing Dagger modules when
        implementing new ones.
        """
        repo_url, branch, path = _parse_module_url(url)
        tree = _reference_tree(repo_url, branch)
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
        pattern: Annotated[str, Doc("Glob pattern (e.g. 'src/**/*.py', '**/*.go', '**/dagger-module.toml')")],
    ) -> str:
        """Find files in the workspace matching a glob pattern."""
        return await workspace.glob_impl(ws, pattern)

    @function
    async def grep(
        self,
        ws: dagger.Workspace,
        pattern: Annotated[str, Doc("Search pattern (regex supported)")],
        paths: Annotated[str, Doc("Comma-separated paths to search in (optional)")] = "",
        file_glob: Annotated[str, Doc("Glob pattern to filter files (e.g. '*.py')")] = "",
        insensitive: Annotated[bool, Doc("Case-insensitive search")] = False,
        limit: Annotated[int, Doc("Maximum number of matching lines to return")] = 100,
    ) -> str:
        """Search file contents in the workspace using grep."""
        return await workspace.grep_impl(ws, pattern, paths, file_glob, insensitive, limit)

    @function
    async def mcp(
        self,
        server: Annotated[str, Doc("MCP server name, as listed in the system prompt (e.g. 'dagger')")],
        tool: Annotated[str, Doc("Name of the server's tool to call (e.g. 'learn_schema')")],
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

        The sub-agent has read-only access to the workspace.
        Use this for research, analysis, or exploring documentation.
        """
        llm = await llm_helpers.build_task_llm(
            ws, self._load_prompt, self._CONTEXT_FILES,
            self._mcp_servers(task="review"),
            self._blocked("task", *constants.BLOCKED_DESTRUCTIVE),
            description, prompt,
        )
        return await llm_helpers.reply(llm)
