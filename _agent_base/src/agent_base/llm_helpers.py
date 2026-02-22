"""LLM builder helpers shared across coding agents."""

from collections.abc import Callable

import dagger
from dagger import dag

from . import constants

MAX_CONTEXT_CHARS = 4000  # ~1000 tokens — keeps total prompt under budget


async def read_context_file(
    source: dagger.Directory,
    context_file_names: tuple[str, ...],
) -> str:
    """Read per-repo context from the first matching file in the priority list."""
    entries = await source.entries()
    for name in context_file_names:
        if name in entries:
            contents = await source.file(name).contents()
            if len(contents) > MAX_CONTEXT_CHARS:
                contents = contents[:MAX_CONTEXT_CHARS] + "\n\n[Context file truncated to fit token budget.]"
            return f"\n\n## Project Context (from {name})\n\n{contents}"
    return ""


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
) -> dagger.LLM:
    """Build an LLM with environment, workspace tools, MCP servers, and prompts."""
    context_md = await read_context_file(source, context_file_names)
    system_prompt = await load_prompt_fn(system_prompt_file).contents()

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
