"""GitHub integration implementations shared across coding agents."""

from collections.abc import Awaitable, Callable

import dagger
from dagger import dag

from . import llm_helpers, routing

MAX_SUGGESTIONS = 5
_MAX_ERROR_CHARS = 8000


def truncate_error_output(error_output: str) -> str:
    """Keep the tail of a long error output, where the failure usually is."""
    if len(error_output) > _MAX_ERROR_CHARS:
        return "...(truncated)\n" + error_output[-_MAX_ERROR_CHARS:]
    return error_output


def parse_suggestions(reply: str) -> tuple[str, list[dict]]:
    """Read the `{"summary": ..., "suggestions": [...]}` reply of a suggest-fix LLM.

    Returns the summary and at most MAX_SUGGESTIONS well-formed suggestions,
    each with `path`, `line`, `suggestion` and `comment`. A reply without a
    JSON object is returned whole as the summary.
    """
    data = routing.extract_json_object(reply)
    if data is None:
        return reply.strip(), []

    suggestions = []
    for item in data.get("suggestions") or []:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        suggestion = item.get("suggestion")
        try:
            line = int(item.get("line"))
        except (TypeError, ValueError):
            continue
        if not isinstance(path, str) or not path or not isinstance(suggestion, str):
            continue
        suggestions.append({
            "path": path,
            "line": line,
            "suggestion": suggestion,
            "comment": str(item.get("comment") or ""),
        })
    return str(data.get("summary") or "").strip(), suggestions[:MAX_SUGGESTIONS]


def suggestion_body(suggestion: str, comment: str = "") -> str:
    """Body of a GitHub "suggested change" review comment."""
    body = f"{comment}\n\n" if comment else ""
    return body + f"```suggestion\n{suggestion}\n```"


async def suggest_github_fix_impl(
    build_suggest_fix_llm_fn: Callable[[dagger.Directory, dict[str, str]], Awaitable[dagger.LLM]],
    github_token: dagger.Secret,
    pr_number: int,
    repo: str,
    commit_sha: str,
    error_output: str,
    workspace: dagger.Directory,
) -> str:
    """Analyze a CI failure and post inline code suggestions on a GitHub PR.

    The LLM reads the workspace and replies with its suggestions as JSON; this
    function posts them. A tool cannot post them itself: in Dagger 1.0 the
    tools of an LLM run on the object as the agent was called, which does not
    carry the GitHub token passed to this entrypoint.
    """
    inputs = {
        "error_output": truncate_error_output(error_output),
        "pr_number": str(pr_number),
        "repo": repo,
        "commit_sha": commit_sha,
    }
    llm = await build_suggest_fix_llm_fn(workspace, inputs)
    summary, suggestions = parse_suggestions(await llm_helpers.reply(llm))

    gh = dag.github_issue(token=github_token)
    posted = []
    for item in suggestions:
        await gh.write_pull_request_code_comment(
            repo=repo,
            issue_id=pr_number,
            commit=commit_sha,
            body=suggestion_body(item["suggestion"], item["comment"]),
            path=item["path"],
            side="RIGHT",
            line=item["line"],
        )
        posted.append(f"- Posted suggestion on {item['path']}:{item['line']}")

    if not posted:
        return summary or "No suggestions posted."
    return "\n".join(filter(None, [summary, *posted]))


async def develop_github_issue_impl(
    load_prompt_fn: Callable,
    execute_routed_fn: Callable,
    allowed_keys: dict[str, set[str]],
    github_token: dagger.Secret,
    issue_id: int,
    repository: str,
    workspace: dagger.Directory,
    base: str,
    suggest_on_failure: bool,
) -> str:
    """Read a GitHub issue, route to best agent function, create a PR."""
    gh = dag.github_issue(token=github_token)

    # Read the issue
    issue = gh.read(repository, issue_id)
    title = await issue.title()
    body = await issue.body()
    url = await issue.url()

    # Classify the issue to pick the best agent function
    router_prompt = await load_prompt_fn("router_prompt.md").contents()
    router = (
        dag.llm()
        .with_system_prompt(router_prompt)
        .with_prompt(f"## GitHub Issue: {title}\n\n{body}")
    )
    function_name, params = routing.parse_router_reply(await llm_helpers.reply(router))

    # Filter params to expected keys per function to prevent TypeErrors
    allowed = allowed_keys.get(function_name, set())
    params = {k: v for k, v in params.items() if k in allowed}

    result = await execute_routed_fn(
        function_name, params, body, workspace,
        gh, repository, issue_id, suggest_on_failure,
    )

    # Create a PR from the modified workspace
    pr = gh.create_pull_request(
        repo=repository,
        title=title,
        body=f"{body}\n\nCloses {url}",
        source=result,
        base=base,
    )
    try:
        pr_url = await pr.url()
    except dagger.ExecError as exc:
        error_msg = str(exc)
        if "nothing to commit" in error_msg:
            await gh.write_comment(
                repo=repository,
                issue_id=issue_id,
                body=(
                    f"**Agent completed but made no code changes.**\n\n"
                    f"**Function**: `{function_name}`\n\n"
                    f"The agent analyzed the issue but did not modify any files. "
                    f"This may be an intermittent LLM issue — please retry."
                ),
            )
            raise RuntimeError(
                f"Agent function '{function_name}' produced no file changes for issue #{issue_id}. "
                f"The workspace was unmodified."
            ) from exc
        raise

    # Comment on the issue with the PR link
    await gh.write_comment(
        repo=repository,
        issue_id=issue_id,
        body=f"I've implemented this issue and opened a pull request: {pr_url}",
    )

    return pr_url
