"""Router parsing and dispatch shared across coding agents."""

import json
import re

import dagger

# Appended to the task prompt when the first attempt changed no file. A retry
# must differ from the first attempt: Dagger caches an identical LLM chain and
# would hand back the same, unchanged workspace.
RETRY_NOTE = (
    "## Previous attempt\n\n"
    "A previous attempt at this task finished without changing any file. "
    "Make the changes in the workspace with `editFile` or `writeFile`; "
    "describing them in your reply is not enough."
)

_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json_object(text: str | None) -> dict | None:
    """Parse the JSON object an LLM was asked to reply with.

    Accepts a bare object, one inside a ``` fence, or one surrounded by prose.
    Returns None when no object can be parsed.
    """
    if not text:
        return None
    candidates = [text.strip(), *_FENCED_JSON.findall(text)]
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start:end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def parse_router_reply(reply: str | None, default: str = "assist") -> tuple[str, dict]:
    """Read the router's `{"function_name": ..., "params": {...}}` reply.

    Falls back to (`default`, {}) when the reply holds no usable object.
    """
    data = extract_json_object(reply)
    if data is None:
        return default, {}
    function_name = str(data.get("function_name") or "").strip().lower() or default
    params = data.get("params")
    return function_name, params if isinstance(params, dict) else {}


async def _workspace_has_changes(original: dagger.Directory, result: dagger.Directory) -> bool:
    """Check if the result workspace differs from the original by comparing directory digests."""
    original_id = await original.digest()
    result_id = await result.digest()
    return original_id != result_id


async def _call_function(agent_ref, function_name: str, params: dict, body: str, workspace) -> dagger.Directory:
    """Call a single agent function by name."""
    if function_name == "upgrade":
        return await agent_ref.upgrade(source=workspace, **params)
    elif function_name == "build":
        return await agent_ref.build(source=workspace, **params)
    elif function_name == "write_tests":
        return await agent_ref.write_tests(source=workspace, **params)
    else:
        return await agent_ref.assist(assignment=body, source=workspace)


async def execute_routed_function(
    agent_ref,
    function_name: str,
    params: dict,
    body: str,
    workspace: dagger.Directory | None,
    gh,
    repository: str,
    issue_id: int,
    suggest_on_failure: bool,
) -> dagger.Directory:
    """Dispatch to the routed function, retrying once if no files were modified."""
    try:
        result = await _call_function(agent_ref, function_name, params, body, workspace)

        # If the workspace wasn't modified, retry once — LLMs sometimes
        # produce text instead of calling writeFile on the first attempt.
        # The agent's _build_llm appends this note to the task prompt.
        if workspace and not await _workspace_has_changes(workspace, result):
            agent_ref._retry_note = RETRY_NOTE
            try:
                result = await _call_function(agent_ref, function_name, params, body, workspace)
            finally:
                agent_ref._retry_note = ""

        return result
    except Exception as exc:
        if suggest_on_failure:
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
