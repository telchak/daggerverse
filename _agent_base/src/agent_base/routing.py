"""Router parsing and dispatch shared across coding agents."""

import json
import re

import dagger
from dagger import dag


def parse_router_response(params_json: str | None) -> tuple[dict, str | None]:
    """Parse JSON from router LLM output with fallback for malformed responses.

    Returns (params_dict, fallback_function_name). fallback_function_name is
    "assist" if parsing failed entirely, None if parsing succeeded.
    """
    try:
        return json.loads(params_json), None
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{[^}]*\}", params_json or "")
        if match:
            try:
                return json.loads(match.group()), None
            except json.JSONDecodeError:
                return {}, "assist"
        return {}, "assist"


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
        # produce text instead of calling write_file on the first attempt.
        if workspace and not await _workspace_has_changes(workspace, result):
            result = await _call_function(agent_ref, function_name, params, body, workspace)

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
