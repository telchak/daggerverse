---
type: Workflow
title: "suggest-github-fix (self-healing CI)"
description: "Entry point that analyzes a CI failure, gets fix suggestions from a read-only LLM as JSON, and posts them as inline GitHub suggestion comments on the PR; AI runs only when deterministic checks fail."
tags: [agent, github, workflow, self-healing]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: gh
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/github_tools.py
    title: "agent_base/github_tools.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/4b26a98eedc27da7855b6e486184c956cfed9103
    title: "feat(agents): Add suggest-github-fix for self-healing CI pipelines"
    author: human:telchak
    last_modified: 2026-02-16T00:47:23+01:00
  - id: daggie-system
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, GitHub Actions Integration"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Flow

1. Called with `github_token`, `pr_number`, `repo`, `commit_sha`, `error_output` and the PR's
   source.
2. Keeps the last 8000 characters of the error output and runs a read-only LLM (no MCP, no
   destructive tools) with `suggest_fix_prompt.md`; the inputs are appended to the prompt.[^gh]
3. The model replies with JSON `{"summary": ..., "suggestions": [{path, line, suggestion, comment}]}`.
   `parse_suggestions` keeps at most 5 well-formed entries, and the code posts each as a
   ```` ```suggestion ```` review comment on the right side of the diff with
   `github-issue.write_pull_request_code_comment`.[^gh]
4. Returns the summary and the list of posted suggestions.

Until the 1.0 port the LLM posted comments itself through a `suggest_github_pr_code_comment`
tool. In 1.0 an LLM's tools run on the agent object as it was constructed, which does not carry
the token passed to the entrypoint, so the posting moved to the code. Added 2026-02-15.[^added]

# Intended CI wiring

The deterministic path (`dagger check` or build/test functions) runs first; the agent runs only
`if: failure() && github.event_name == 'pull_request'`, called as an external module with
`--allow-llm=all -m github.com/telchak/daggerverse/<agent>@<version>`.[^daggie-system] See the
[AI-on-failure decision](/decisions/ai-on-failure-only.md).

[^gh]: agent_base/github_tools.py
[^added]: feat(agents): Add suggest-github-fix for self-healing CI pipelines
[^daggie-system]: Daggie system prompt, GitHub Actions Integration
