"""Speck — AI-powered spec-driven development agent.

Implements a spec-driven development pipeline inspired by spec-kit:
1. Specify: Generate requirements from a prompt or GitHub issue
2. Plan: Create a technical implementation plan
3. Decompose: Break the plan into structured, agent-assignable tasks (JSON)

The structured JSON output is designed for consumption by GitHub Actions
workflows to dynamically dispatch sub-agents (Monty, Angie, Daggie, etc.).
"""

import json
import re
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, field, function, object_type

from agent_base import constants, llm_helpers, workspace
from agent_base.mcp_stdio import McpServer

# Model family mappings: complexity tier → model ID
_MODEL_FAMILIES: dict[str, dict[str, str]] = {
    "claude": {
        "low": "claude-haiku-4-5",
        "medium": "claude-sonnet-4-6",
        "high": "claude-opus-4-6",
    },
    "gemini": {
        "low": "gemini-3.1-flash-lite-preview",
        "medium": "gemini-3-flash-preview",
        "high": "gemini-3.1-pro-preview",
    },
    "openai": {
        "low": "gpt-4o-mini",
        "medium": "gpt-4o",
        "high": "o3",
    },
}


def _extract_and_validate_json(raw: str) -> str:
    """Extract and validate JSON from LLM output.

    Handles common LLM output issues:
    - Markdown fences wrapping the JSON
    - Trailing commas before ] or }
    - Text before/after the JSON object
    Returns the cleaned, valid JSON string.
    """
    text = raw.strip()

    # Strip markdown fences if present
    match = re.search(r"```(?:json)?[ \t]*\n(.*?)\n```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Extract the JSON object if surrounded by prose
    if not text.startswith("{"):
        obj_match = re.search(r"\{.*\}", text, re.DOTALL)
        if obj_match:
            text = obj_match.group(0)

    # Fix trailing commas (e.g., ",]" or ",}")
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Validate
    json.loads(text)
    return text


def _format_model_table(family: dict[str, str]) -> str:
    """Format a model family dict as a readable table for the LLM prompt."""
    lines = ["| Complexity | Model ID |", "|-----------|----------|"]
    for tier, model_id in family.items():
        lines.append(f"| {tier} | `{model_id}` |")
    return "\n".join(lines)


@object_type
class Speck:
    """AI-powered spec-driven development agent.

    Takes a prompt or GitHub issue and produces structured task
    decompositions with agent and model assignments. The output is
    a JSON object designed for GitHub Actions matrix consumption.

    Pass your project as --source and provide an agent registry via
    --agents to enable intelligent agent assignment.
    """

    source: Annotated[
        dagger.Directory,
        Doc("Project source directory"),
        DefaultPath("/"),
    ] = field()

    # --- Agent-specific configuration ---

    _CONTEXT_FILES = ("SPECK.md", "AGENT.md", "CLAUDE.md")
    _CLASS_NAME = "Speck"

    def _mcp_servers(self) -> list[McpServer]:
        return []

    def _load_prompt(self, filename: str) -> dagger.File:
        return dag.current_module().source().file(f"src/speck/prompts/{filename}")

    # Speck's own entrypoints to block on all LLMs (prevent recursion).
    # Unlike coding agents, Speck doesn't have assist/review/build/etc.,
    # so we only block functions that actually exist on this class.
    _BLOCKED_ENTRYPOINTS = ["specify", "plan", "decompose", "decompose_from_spec"]
    # Exposed fields are tools too in Dagger 1.0; hide them from the LLM
    _FIELDS = ["source"]

    def _blocked(self, *extra: str) -> list[str]:
        return [*self._BLOCKED_ENTRYPOINTS, *self._FIELDS, *extra]

    async def _build_llm(self, prompt_file, inputs):
        return await llm_helpers.build_llm(
            self.source, "system_prompt.md", prompt_file, self._load_prompt,
            self._CONTEXT_FILES, self._mcp_servers(), self._blocked(),
            inputs=inputs,
        )

    # --- Agent entrypoints ---

    @function
    async def specify(
        self,
        prompt: Annotated[str, Doc("Natural language description of what to build")] = "",
        issue_id: Annotated[int, Doc("GitHub issue number (alternative to prompt)")] = 0,
        repository: Annotated[str, Doc("GitHub repository URL (required if using issue_id)")] = "",
        github_token: Annotated[dagger.Secret | None, Doc("GitHub token (required if using issue_id)")] = None,
    ) -> str:
        """Generate a feature specification from a prompt or GitHub issue.

        Produces a structured specification with user stories, acceptance
        criteria, functional requirements, and success criteria. Returns
        the specification as markdown text.
        """
        assignment = await self._resolve_input(prompt, issue_id, repository, github_token)

        work = await self._build_llm("specify_prompt.md", {"feature_description": assignment})
        return await llm_helpers.reply(work)

    @function
    async def plan(
        self,
        spec: Annotated[str, Doc("Feature specification (output of specify)")],
        tech_stack: Annotated[str, Doc("Tech stack hints (e.g. 'Python, FastAPI, PostgreSQL')")] = "",
    ) -> str:
        """Generate a technical implementation plan from a specification.

        Takes a feature specification and produces a technical plan with
        architecture decisions, project structure, dependencies, and
        complexity analysis. Returns the plan as markdown text.
        """
        work = await self._build_llm("plan_prompt.md", {"spec": spec, "tech_stack": tech_stack})
        return await llm_helpers.reply(work)

    @function
    async def decompose(
        self,
        prompt: Annotated[str, Doc("What to build (runs full pipeline: specify -> plan -> decompose)")] = "",
        issue_id: Annotated[int, Doc("GitHub issue number (alternative to prompt)")] = 0,
        repository: Annotated[str, Doc("GitHub repository URL (required if using issue_id)")] = "",
        github_token: Annotated[dagger.Secret | None, Doc("GitHub token (required if using issue_id)")] = None,
        agents: Annotated[str, Doc("JSON array of available agents with name, source, specialization, capabilities")] = "[]",
        tech_stack: Annotated[str, Doc("Tech stack hints (e.g. 'Python, FastAPI, PostgreSQL')")] = "",
        model_family: Annotated[str, Doc("Model family for suggestions: 'claude' (default), 'gemini', or 'openai'")] = "claude",
        include_tests: Annotated[bool, Doc("Generate test tasks (write_tests) after implementation tasks")] = False,
        include_review: Annotated[bool, Doc("Generate review tasks (review) at the end of each phase")] = False,
        create_pr: Annotated[bool, Doc("Add PR branch names to phases for automated PR creation (one PR per phase)")] = False,
    ) -> str:
        """Run the full spec-driven development pipeline.

        Executes specify -> plan -> decompose in sequence and returns
        a structured JSON object with tasks, agent assignments, model
        suggestions, and an execution plan. Designed for GitHub Actions
        matrix consumption.

        When create_pr is enabled, each phase in the execution plan gets
        a pr_branch field. The GitHub Actions workflow should matrix by
        phase, chain tasks sequentially (impl -> test -> review), and
        create one PR per phase with the accumulated changes.
        """
        assignment = await self._resolve_input(prompt, issue_id, repository, github_token)
        if model_family not in _MODEL_FAMILIES:
            raise ValueError(f"model_family must be one of {list(_MODEL_FAMILIES)}, got '{model_family}'")
        model_table = _MODEL_FAMILIES[model_family]

        work = await self._build_llm("decompose_prompt.md", {
            "feature_description": assignment,
            "agents_registry": agents,
            "model_family": model_family,
            "model_table": _format_model_table(model_table),
            "include_tests": "true" if include_tests else "false",
            "include_review": "true" if include_review else "false",
            "create_pr": "true" if create_pr else "false",
            "tech_stack": tech_stack,
        })
        raw = await llm_helpers.reply(work)
        return _extract_and_validate_json(raw)

    @function
    async def decompose_from_spec(
        self,
        spec: Annotated[str, Doc("Feature specification markdown")],
        plan: Annotated[str, Doc("Technical implementation plan markdown")],
        agents: Annotated[str, Doc("JSON array of available agents")] = "[]",
        model_family: Annotated[str, Doc("Model family for suggestions: 'claude' (default), 'gemini', or 'openai'")] = "claude",
        include_tests: Annotated[bool, Doc("Generate test tasks (write_tests) after implementation tasks")] = False,
        include_review: Annotated[bool, Doc("Generate review tasks (review) at the end of each phase")] = False,
        create_pr: Annotated[bool, Doc("Add PR branch names to phases for automated PR creation (one PR per phase)")] = False,
    ) -> str:
        """Decompose a pre-existing spec and plan into structured tasks.

        Use this when you already have a specification and plan (e.g.
        from manual spec-kit usage) and want to generate the structured
        JSON task list with agent assignments.
        """
        if model_family not in _MODEL_FAMILIES:
            raise ValueError(f"model_family must be one of {list(_MODEL_FAMILIES)}, got '{model_family}'")
        model_table = _MODEL_FAMILIES[model_family]

        work = await self._build_llm("decompose_from_spec_prompt.md", {
            "spec": spec,
            "plan": plan,
            "agents_registry": agents,
            "model_family": model_family,
            "model_table": _format_model_table(model_table),
            "include_tests": "true" if include_tests else "false",
            "include_review": "true" if include_review else "false",
            "create_pr": "true" if create_pr else "false",
        })
        raw = await llm_helpers.reply(work)
        return _extract_and_validate_json(raw)

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
        """Edit a file by replacing a string. The old_string must match exactly."""
        return await workspace.edit_file_impl(ws, file_path, old_string, new_string, replace_all)

    @function
    def write_file(
        self,
        ws: dagger.Workspace,
        file_path: Annotated[str, Doc("Path to the file relative to the workspace root")],
        contents: Annotated[str, Doc("The full file contents to write")],
    ) -> dagger.Workspace:
        """Create or overwrite a file in the workspace."""
        return workspace.write_file_impl(ws, file_path, contents)

    @function
    async def glob(
        self,
        ws: dagger.Workspace,
        pattern: Annotated[str, Doc("Glob pattern (e.g. 'src/**/*.py', '**/*.toml')")],
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

    # --- Task sub-agent ---

    @function
    async def task(
        self,
        ws: dagger.Workspace,
        description: Annotated[str, Doc("Short description of the sub-task")],
        prompt: Annotated[str, Doc("Detailed prompt for the sub-agent")],
    ) -> str:
        """Launch a sub-agent for research or focused analysis.

        The sub-agent has read-only access to the workspace.
        Use this for exploring the codebase to inform specification and planning.
        """
        llm = await llm_helpers.build_task_llm(
            ws, self._load_prompt, self._CONTEXT_FILES,
            self._mcp_servers(),
            self._blocked("task", *constants.BLOCKED_DESTRUCTIVE),
            description, prompt,
        )
        return await llm_helpers.reply(llm)

    # --- Internal helpers ---

    async def _resolve_input(
        self,
        prompt: str,
        issue_id: int,
        repository: str,
        github_token: dagger.Secret | None,
    ) -> str:
        """Resolve input from either a prompt string or a GitHub issue."""
        if prompt:
            return prompt

        if issue_id and repository and github_token:
            issue = dag.github_issue(
                token=github_token,
            ).read(repo=repository, issue_id=issue_id)
            title = await issue.title()
            body = await issue.body()
            return f"# {title}\n\n{body}"

        msg = "Either 'prompt' or 'issue_id' + 'repository' + 'github_token' must be provided"
        raise ValueError(msg)
