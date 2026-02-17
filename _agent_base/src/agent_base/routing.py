"""Router parsing and dispatch shared across coding agents."""

import json
import re

import dagger


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
    """Dispatch to the routed function, posting a comment on failure if requested."""
    try:
        if function_name == "upgrade":
            return await agent_ref.upgrade(source=workspace, **params)
        elif function_name == "build":
            return await agent_ref.build(source=workspace, **params)
        elif function_name == "write_tests":
            return await agent_ref.write_tests(source=workspace, **params)
        else:
            return await agent_ref.assist(assignment=body, source=workspace)
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
