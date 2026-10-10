---
type: Workflow
title: "suggest-github-fix (self-healing CI)"
description: "Entry point that analyzes a CI failure and posts inline GitHub suggestion comments on the PR; AI runs only when deterministic checks fail."
tags: [agent, github, workflow, self-healing]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: gh
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/github_tools.py
    title: "agent_base/github_tools.py"
    author: human:telchak
    last_modified: 2026-02-22T02:17:19+01:00
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/4b26a98eedc27da7855b6e486184c956cfed9103
    title: "feat(agents): Add suggest-github-fix for self-healing CI pipelines"
    author: human:telchak
    last_modified: 2026-02-16T00:47:23+01:00
  - id: daggie-system
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, GitHub Actions Integration"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
---

# Flow

1. Called with `github_token`, `pr_number`, `repo`, `commit_sha`, `error_output`.
2. Stores PR state on private fields (`_github_token`, `_pr_repo`, ...), keeps the last 8000
   characters of the error output, and runs a read-only LLM with `suggest_fix_prompt.md`.[^gh]
3. The only write tool is `suggest_github_pr_code_comment(path, line, suggestion, comment)`,
   which posts a ```` ```suggestion ```` review comment on the right side of the diff.

Added 2026-02-15.[^added]

# Intended CI wiring

The deterministic path (`dagger check` or build/test functions) runs first; the agent runs only
`if: failure() && github.event_name == 'pull_request'`, called as an external module with
`-m github.com/telchak/daggerverse/<agent>@<version>`.[^daggie-system] See the
[AI-on-failure decision](/decisions/ai-on-failure-only.md).

[^gh]: agent_base/github_tools.py
[^added]: feat(agents): Add suggest-github-fix for self-healing CI pipelines
[^daggie-system]: Daggie system prompt, GitHub Actions Integration
