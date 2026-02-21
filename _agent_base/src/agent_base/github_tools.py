"""GitHub integration implementations shared across coding agents."""

from collections.abc import Callable

import dagger
from dagger import dag


async def suggest_github_fix_impl(
    build_suggest_fix_llm_fn: Callable,
    github_token: dagger.Secret,
    pr_number: int,
    repo: str,
    commit_sha: str,
    error_output: str,
    agent_ref,
    workspace: dagger.Directory,
) -> str:
    """Analyze a CI failure and post inline code suggestions on a GitHub PR."""
    # Store PR state on the agent for the suggestion tool
    agent_ref._github_token = github_token
    agent_ref._pr_repo = repo
    agent_ref._pr_number = pr_number
    agent_ref._pr_commit_sha = commit_sha

    # Truncate error output (keep tail — most relevant)
    max_error_chars = 8000
    if len(error_output) > max_error_chars:
        error_output = "...(truncated)\n" + error_output[-max_error_chars:]

    env = (
        dag.env()
        .with_string_input("error_output", error_output, "The CI error output to analyze")
        .with_string_input("pr_number", str(pr_number), "The pull request number")
        .with_string_input("repo", repo, "The GitHub repository URL")
        .with_string_input("commit_sha", commit_sha, "The HEAD commit SHA of the PR")
        .with_string_output("result", "Summary of suggestions posted")
    )

    if workspace:
        env = env.with_workspace(workspace)

    work = await build_suggest_fix_llm_fn(env, workspace)
    return await work.env().output("result").as_string()


async def suggest_github_pr_code_comment_impl(
    github_token: dagger.Secret | None,
    pr_repo: str,
    pr_number: int,
    pr_commit_sha: str,
    path: str,
    line: int,
    suggestion: str,
    comment: str = "",
) -> str:
    """Post an inline code suggestion on a GitHub pull request."""
    if not github_token or not pr_repo:
        raise ValueError("suggest_github_pr_code_comment can only be used during suggest_github_fix")

    body = ""
    if comment:
        body += f"{comment}\n\n"
    body += f"```suggestion\n{suggestion}\n```"

    gh = dag.github_issue(token=github_token)
    await gh.write_pull_request_code_comment(
        repo=pr_repo,
        issue_id=pr_number,
        commit=pr_commit_sha,
        body=body,
        path=path,
        side="RIGHT",
        line=line,
    )
    return f"Posted suggestion on {path}:{line}"


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

    router_env = (
        dag.env()
        .with_string_input("issue_title", title, "The GitHub issue title")
        .with_string_input("issue_body", body, "The GitHub issue body")
        .with_string_output("function_name", "The function to call: assist, upgrade, build, or write_tests")
        .with_string_output("params_json", "JSON object with function parameters")
    )

    router = (
        dag.llm()
        .with_env(router_env)
        .with_system_prompt(router_prompt)
        .with_prompt(f"## GitHub Issue: {title}\n\n{body}")
    )

    function_name = (await router.env().output("function_name").as_string()).strip().lower()
    params_json = await router.env().output("params_json").as_string()

    from .routing import parse_router_response
    params, fallback = parse_router_response(params_json)
    if fallback:
        function_name = fallback

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
