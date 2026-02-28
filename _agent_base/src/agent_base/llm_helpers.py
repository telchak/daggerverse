"""LLM builder helpers shared across coding agents."""

from collections.abc import Callable

import dagger
from dagger import dag

from . import constants

MAX_CONTEXT_CHARS = 4000  # ~1000 tokens — keeps total prompt under budget
_TRUNCATION_NOTICE = "\n\n[Truncated.]"
_WORK_DIR = "/work"

# Shared file names — read in order, first match used as shared context
_SHARED_CONTEXT_FILES = ("AGENTS.md", "AGENT.md", "CLAUDE.md")

_SELF_IMPROVE_PROMPT = """

## Self-Improvement Instructions

You have self-improvement enabled. As you work, record useful discoveries in
**two** context files. Use `read_file` to check each file's current contents
first, then use `edit_file` to append new entries at the end. If a file does
not exist yet, use `write_file` to create it.

### Agent-specific file: `{agent_file}`

Record knowledge specific to this agent's domain here:
- Language/framework patterns you discovered (e.g. Python async patterns, Angular signals usage)
- Stack-specific build/test/lint conventions
- Framework version constraints or migration notes
- Tool-specific gotchas (e.g. pytest fixtures, Angular CLI quirks)

### Shared file: `AGENTS.md`

Record general-purpose knowledge about the repository here:
- Project architecture and folder structure
- Cross-cutting conventions (naming, error handling, logging)
- CI/CD and deployment patterns
- Dependency management approach
- Team preferences expressed during this session

### Format rules

- Use markdown headings and bullet points
- Add entries under a `## Learned Context` heading at the bottom of each file
- Keep each entry to 1-3 lines
- Do not duplicate information already present in either file
- Do not record generic language/framework knowledge, temporary state, or anything already documented

Do this as a **final step**, after completing your main task successfully.
"""


async def _read_and_format_section(
    source: dagger.Directory,
    name: str,
) -> str:
    """Read a single context file and return a formatted section."""
    contents = await source.file(name).contents()
    if len(contents) > MAX_CONTEXT_CHARS:
        contents = contents[:MAX_CONTEXT_CHARS] + _TRUNCATION_NOTICE
    return f"## Project Context (from {name})\n\n{contents}"


async def read_context_file(
    source: dagger.Directory,
    context_file_names: tuple[str, ...],
    extra_read_files: tuple[str, ...] = (),
) -> str:
    """Read per-repo context from agent-specific, shared, and extra files.

    Reads up to three sections:
    1. Agent-specific file (context_file_names[0], e.g. MONTY.md)
    2. First matching shared file (AGENTS.md > AGENT.md > CLAUDE.md)
    3. Any extra files that exist (e.g. DAGGER.md for Daggie/Goose)
    """
    entries = await source.entries()
    sections: list[str] = []
    agent_file = context_file_names[0]

    # 1. Agent-specific file (first entry in the tuple)
    if agent_file in entries:
        sections.append(await _read_and_format_section(source, agent_file))

    # 2. Shared file (AGENTS.md > AGENT.md > CLAUDE.md)
    for name in _SHARED_CONTEXT_FILES:
        if name in entries:
            sections.append(await _read_and_format_section(source, name))
            break

    # 3. Extra files (e.g. DAGGER.md for Daggie)
    for name in extra_read_files:
        if name in entries and name != agent_file:
            sections.append(await _read_and_format_section(source, name))

    return "\n\n" + "\n\n".join(sections) if sections else ""


async def commit_context_file(
    workspace: dagger.Directory,
    context_file_names: tuple[str, ...],
    agent_name: str,
) -> dagger.Directory:
    """Create a git commit for context files if they changed."""
    agent_file = context_file_names[0]
    return await (
        dag.container()
        .from_("alpine/git:latest")
        .with_mounted_directory(_WORK_DIR, workspace)
        .with_workdir(_WORK_DIR)
        .with_exec(["git", "config", "user.name", agent_name])
        .with_exec(["git", "config", "user.email", f"{agent_name.lower()}@dagger.io"])
        .with_exec([
            "sh", "-c",
            f'git add -f {agent_file} AGENTS.md 2>/dev/null; '
            f'git diff --cached --quiet || git commit -m "chore({agent_name.lower()}): update context files with learned discoveries"',
        ])
        .directory(_WORK_DIR)
    )


async def build_llm(
    env: dagger.Env,
    system_prompt_file: str,
    prompt_file: str,
    load_prompt_fn: Callable[[str], dagger.File],
    context_file_names: tuple[str, ...],
    mcp_servers: dict[str, dagger.Service],
    class_name: str,
    blocked_entrypoints: list[str],
    source: dagger.Directory,
    extra_blocked: list[str] | None = None,
    self_improve: str = "off",
) -> dagger.LLM:
    """Build an LLM with environment, workspace tools, MCP servers, and prompts."""
    context_md = await read_context_file(source, context_file_names)
    system_prompt = await load_prompt_fn(system_prompt_file).contents()

    if self_improve != "off":
        agent_file = context_file_names[0]
        system_prompt += _SELF_IMPROVE_PROMPT.format(agent_file=agent_file)

    llm = (
        dag.llm()
        .with_env(env.with_current_module())
        .with_system_prompt(system_prompt + context_md)
    )

    for name, service in mcp_servers.items():
        llm = llm.with_mcp_server(name, service)

    for fn in blocked_entrypoints + (extra_blocked or []):
        llm = llm.with_blocked_function(class_name, fn)

    return llm.with_prompt_file(load_prompt_fn(prompt_file))


async def build_suggest_fix_llm(
    env: dagger.Env,
    load_prompt_fn: Callable[[str], dagger.File],
    context_file_names: tuple[str, ...],
    class_name: str,
    blocked_entrypoints: list[str],
    blocked_destructive: list[str],
    source: dagger.Directory,
) -> dagger.LLM:
    """Build an LLM for suggest-github-fix (no MCP, workspace + suggestion tool)."""
    context_md = await read_context_file(source, context_file_names)
    system_prompt = await load_prompt_fn("system_prompt.md").contents()

    llm = (
        dag.llm()
        .with_env(env.with_current_module())
        .with_system_prompt(system_prompt + context_md)
    )

    for fn in blocked_entrypoints + ["task"] + blocked_destructive:
        if fn != "suggest_github_pr_code_comment":
            llm = llm.with_blocked_function(class_name, fn)

    return llm.with_prompt_file(load_prompt_fn("suggest_fix_prompt.md"))


async def build_task_llm(
    source: dagger.Directory,
    load_prompt_fn: Callable[[str], dagger.File],
    context_file_names: tuple[str, ...],
    mcp_servers: dict[str, dagger.Service],
    class_name: str,
    blocked_entrypoints: list[str],
    blocked_destructive: list[str],
    description: str,
    prompt: str,
) -> dagger.LLM:
    """Build an LLM for the task sub-agent (read-only workspace + MCP)."""
    task_system = await load_prompt_fn("task_system_prompt.md").contents()
    context_md = await read_context_file(source, context_file_names)

    env = (
        dag.env()
        .with_workspace(source)
        .with_string_input("task_description", description, "The sub-task description")
        .with_string_input("task_prompt", prompt, "Detailed instructions for the sub-task")
        .with_string_output("result", "The sub-task result")
    )

    llm = (
        dag.llm()
        .with_env(env.with_current_module())
        .with_system_prompt(task_system + context_md)
    )

    for name, service in mcp_servers.items():
        llm = llm.with_mcp_server(name, service)

    for fn in blocked_entrypoints + ["task"] + blocked_destructive:
        llm = llm.with_blocked_function(class_name, fn)

    return llm.with_prompt(f"## Task: {description}\n\n{prompt}")


async def get_result_or_last_reply(work: dagger.LLM, output_name: str = "result") -> str:
    """Get a string output from the LLM, falling back to last_reply.

    Some LLMs (notably Gemini) sometimes produce text output without
    calling the output binding tool.  This helper tries the binding first,
    then falls back to the LLM's last reply so the work isn't lost.
    """
    try:
        value = await work.env().output(output_name).as_string()
        if value and value.strip():
            return value
    except Exception:
        pass
    # Fallback: the LLM generated text but didn't bind it
    return await work.last_reply()
