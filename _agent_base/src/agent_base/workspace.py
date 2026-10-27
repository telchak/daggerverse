"""Workspace tool implementations shared across coding agents.

The tools act on the workspace the LLM is bound to: Dagger injects it into
every `dagger.Workspace` argument of a tool and hides that argument from the
model. A tool that returns a `dagger.Workspace` replaces the LLM's workspace,
so the next tool call reads the edited files.
"""

import dagger
from dagger import dag


async def read_file_impl(
    ws: dagger.Workspace,
    file_path: str,
    offset: int = 0,
    limit: int = 0,
) -> str:
    """Read a file from the workspace with line numbers."""
    contents = await ws.file(file_path).contents()
    lines = contents.splitlines()

    if offset > 0:
        lines = lines[offset - 1:]
    if limit > 0:
        lines = lines[:limit]

    start = offset if offset > 0 else 1
    numbered = [f"{start + i:4d}  {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered)


async def edit_file_impl(
    ws: dagger.Workspace,
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> dagger.Workspace:
    """Edit a file by replacing a string. Returns the edited workspace."""
    contents = await ws.file(file_path).contents()

    if old_string not in contents:
        msg = f"old_string not found in {file_path}"
        raise ValueError(msg)

    if replace_all:
        new_contents = contents.replace(old_string, new_string)
    else:
        new_contents = contents.replace(old_string, new_string, 1)

    return ws.with_new_file(file_path, new_contents)


def write_file_impl(
    ws: dagger.Workspace,
    file_path: str,
    contents: str,
) -> dagger.Workspace:
    """Create or overwrite a file. Returns the edited workspace."""
    return ws.with_new_file(file_path, contents)


async def glob_impl(
    ws: dagger.Workspace,
    pattern: str,
) -> str:
    """Find files matching a glob pattern."""
    entries = await ws.glob(pattern)
    if not entries:
        return "No files matched the pattern."
    return "\n".join(entries)


async def grep_impl(
    ws: dagger.Workspace,
    pattern: str,
    paths: str = "",
    file_glob: str = "",
    insensitive: bool = False,
    limit: int = 100,
) -> str:
    """Search file contents using grep."""
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
        .with_mounted_directory("/work", ws.directory("."))
        .with_workdir("/work")
        .with_exec(cmd, expect=dagger.ReturnType.ANY)
        .stdout()
    )

    lines = result.strip().splitlines()
    if limit > 0 and len(lines) > limit:
        lines = lines[:limit]
        lines.append(f"... (truncated, {limit} of many matches shown)")

    return "\n".join(lines) if lines else "No matches found."
