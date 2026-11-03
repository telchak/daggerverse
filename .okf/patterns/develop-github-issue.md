---
type: Workflow
title: "develop-github-issue (issue to PR)"
description: "Entry point that reads a GitHub issue, routes it with a classification LLM to the best agent function, runs it, and opens a pull request."
tags: [agent, github, workflow]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: gh
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/github_tools.py
    title: "agent_base/github_tools.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: routing
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/routing.py
    title: "agent_base/routing.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: classify
    resource: https://github.com/telchak/daggerverse/commit/a315613a5f65cdade7c1c9b54c5ef830ecacd83b
    title: "fix(angie): use classification LLM for issue routing instead of agent pattern"
    author: human:telchak
    last_modified: 2026-02-10T21:20:15+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, test-angie-github-issue job"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Flow

1. Read the issue with `dag.github_issue(token).read(repo, id)` (`kpenfound/dag/github-issue`).
2. A **router LLM** (`router_prompt.md`, no tools) replies with JSON
   `{"function_name": ..., "params": {...}}`. It is a single classification call, not an agent
   loop (changed 2026-02-10).[^classify]
3. `parse_router_reply` accepts a bare, fenced or embedded JSON object; a malformed reply falls
   back to `assist`. Params are filtered by `_ALLOWED_ROUTER_KEYS` per function to avoid
   `TypeError`s.[^routing]
4. `execute_routed_function` runs `upgrade` / `build` / `write_tests` / `assist` and retries once,
   with a retry note, if the workspace digest did not change. On error with
   `suggest_github_fix_on_failure`, it comments the error on the issue.
5. `create_pull_request(repo, title, body + "Closes <url>", source=result, base)`, then comments
   the PR URL on the issue; "nothing to commit" becomes an issue comment and an error.[^gh]

# Tested end to end

The `test-angie-github-issue` CI job runs it against a real repository with
`ANGIE_TEST_GITHUB_TOKEN` (`dagger api call -m ./tests angie-develop-github-issue`), then closes
the PR and deletes its branch with `gh pr close --delete-branch`.[^ci]

[^gh]: agent_base/github_tools.py
[^routing]: agent_base/routing.py
[^classify]: fix(angie): use classification LLM for issue routing instead of agent pattern
[^ci]: CI workflow, test-angie-github-issue job
