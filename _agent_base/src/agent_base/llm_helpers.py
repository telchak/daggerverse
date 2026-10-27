"""LLM builder helpers shared across coding agents.

Dagger 1.0 has no `Env`: an LLM is bound to a workspace (`LLM.with_workspace`)
and acts through the methods of the objects bound to it
(`LLM.with_tools(dag.current_node(), except_=...)`). Values an agent used to
pass as Env inputs are written into the prompt, results come from the final
reply or from the edited workspace, and nothing runs until `LLM.loop()`.
"""

from collections.abc import Callable, Iterable

import dagger
from dagger import dag

from . import mcp_stdio
from .mcp_stdio import McpServer

MAX_CONTEXT_CHARS = 4000  # ~1000 tokens — keeps total prompt under budget
_TRUNCATION_NOTICE = "\n\n[Truncated.]"
_WORK_DIR = "/work"

# Shared file names — read in order, first match used as shared context
_SHARED_CONTEXT_FILES = ("AGENTS.md", "AGENT.md", "CLAUDE.md")

_SELF_IMPROVE_PROMPT = """

## Self-Improvement Instructions

You have self-improvement enabled. As you work, record useful discoveries in
**two** context files. Use `readFile` to check each file's current contents
first, then use `editFile` to append new entries at the end. If a file does
not exist yet, use `writeFile` to create it.

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


def tool_name(name: str) -> str:
    """The GraphQL name of a Python function: the name its tool has.

    `LLM.with_tools(except_=...)` compares these names as they are and ignores
    names it does not know, so a snake_case name would hide nothing.
    """
    head, *rest = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest)


def tool_exclusions(names: Iterable[str]) -> list[str]:
    """GraphQL names to pass to `LLM.with_tools(except_=...)`."""
    return sorted({tool_name(name) for name in names})


def format_inputs(inputs: dict[str, str] | None) -> str:
    """Render the task inputs into the prompt, skipping empty values.

    Prompts describe their inputs under "## Inputs"; the values follow them,
    under "## Input values".
    """
    present = [(name, value) for name, value in (inputs or {}).items() if value]
    if not present:
        return ""
    sections = [f"### {name}\n\n{value}" for name, value in present]
    return "\n\n## Input values\n\n" + "\n\n".join(sections)


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
    source: dagger.Directory,
    system_prompt_file: str,
    prompt_file: str,
    load_prompt_fn: Callable[[str], dagger.File],
    context_file_names: tuple[str, ...],
    mcp_servers: list[McpServer],
    blocked: Iterable[str],
    inputs: dict[str, str] | None = None,
    self_improve: str = "off",
    extra_read_files: tuple[str, ...] = (),
    extra_context: str = "",
    retry_note: str = "",
) -> dagger.LLM:
    """Build an LLM that works on `source`, with this agent's tools, MCP servers and prompts.

    Call it from an agent function: it binds the object that received the call.
    """
    context_md = await read_context_file(source, context_file_names, extra_read_files)
    system_prompt = await load_prompt_fn(system_prompt_file).contents()

    if self_improve != "off":
        system_prompt += _SELF_IMPROVE_PROMPT.format(agent_file=context_file_names[0])

    llm = (
        dag.llm()
        .with_workspace(source.as_workspace())
        .with_tools(dag.current_node(), except_=tool_exclusions([*blocked, *mcp_stdio.blocked_tools(mcp_servers)]))
    )
    llm, mcp_context = await mcp_stdio.attach(llm, mcp_servers)
    llm = llm.with_system_prompt(system_prompt + context_md + extra_context + mcp_context)

    prompt = await load_prompt_fn(prompt_file).contents()
    if retry_note:
        prompt += f"\n\n{retry_note}"
    return llm.with_prompt(prompt + format_inputs(inputs))


async def build_suggest_fix_llm(
    source: dagger.Directory,
    load_prompt_fn: Callable[[str], dagger.File],
    context_file_names: tuple[str, ...],
    blocked: Iterable[str],
    inputs: dict[str, str],
    extra_read_files: tuple[str, ...] = (),
    extra_context: str = "",
) -> dagger.LLM:
    """Build a read-only LLM for suggest-github-fix (no MCP; suggestions come back in the reply)."""
    return await build_llm(
        source, "system_prompt.md", "suggest_fix_prompt.md", load_prompt_fn,
        context_file_names, [], blocked, inputs=inputs,
        extra_read_files=extra_read_files, extra_context=extra_context,
    )


async def build_task_llm(
    ws: dagger.Workspace,
    load_prompt_fn: Callable[[str], dagger.File],
    context_file_names: tuple[str, ...],
    mcp_servers: list[McpServer],
    blocked: Iterable[str],
    description: str,
    prompt: str,
) -> dagger.LLM:
    """Build an LLM for the task sub-agent: the caller's workspace, read-only tools and MCP."""
    task_system = await load_prompt_fn("task_system_prompt.md").contents()
    context_md = await read_context_file(ws.directory("."), context_file_names)

    llm = (
        dag.llm()
        .with_workspace(ws)
        .with_tools(dag.current_node(), except_=tool_exclusions([*blocked, *mcp_stdio.blocked_tools(mcp_servers)]))
    )
    llm, mcp_context = await mcp_stdio.attach(llm, mcp_servers)
    llm = llm.with_system_prompt(task_system + context_md + mcp_context)
    return llm.with_prompt(f"## Task: {description}\n\n{prompt}")


async def build_agent(
    base: dagger.LLM,
    ws: dagger.Workspace,
    load_prompt_fn: Callable[[str], dagger.File],
    context_file_names: tuple[str, ...],
    mcp_servers: list[McpServer],
    blocked: Iterable[str],
    extra_read_files: tuple[str, ...] = (),
) -> dagger.LLM:
    """Fold this agent's tools, MCP servers and system prompt onto a base LLM (for `@agent`).

    `dagger agent` passes a base LLM bound to the user's workspace, so the
    tools edit that workspace and the session's Changes panel shows the edits.
    """
    context_md = await read_context_file(ws.directory("."), context_file_names, extra_read_files)
    system_prompt = await load_prompt_fn("system_prompt.md").contents()
    llm = base.with_tools(
        dag.current_node(), except_=tool_exclusions([*blocked, *mcp_stdio.blocked_tools(mcp_servers)]),
    )
    llm, mcp_context = await mcp_stdio.attach(llm, mcp_servers)
    return llm.with_system_prompt(system_prompt + context_md + mcp_context)


async def reply(llm: dagger.LLM) -> str:
    """Run the agent loop and return the model's final reply."""
    return await llm.loop().last_reply()


def edited_directory(llm: dagger.LLM) -> dagger.Directory:
    """Run the agent loop and return the workspace it edited, as a directory."""
    return llm.loop().workspace().directory("/")
