---
type: Known Issue
title: "Documentation drift"
description: "Places where README.md or CONTRIBUTING.md disagree with the code as of 2026-10-10; check the code before trusting them."
tags: [documentation, known-issue]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide"
    author: human:telchak
    last_modified: 2026-03-05T15:49:35+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
---

Observed on 2026-10-10. Fix the docs or delete an entry here when it is resolved.

| Doc | Says | Reality |
|-----|------|---------|
| README | Modules/AI Agents tables and Architecture tree omit Speck | `speck/` is a released agent (`speck/v0.2.x`) |
| README | "Angie, Monty, and Daggie share `_agent_base`" | Speck uses it too; Goose does not |
| `speck/src/speck/__init__.py` | one-line docstring (text on the opening triple-quote line) | the Python SDK skips text on that line, so the daggerverse description may render empty; other modules start on the next line |
| CONTRIBUTING | Dagger v0.19.11+ | engine is v0.21.10[^ci] |
| CONTRIBUTING | repository structure lists `gcp-orchestrator-agent/`, no agents | renamed Goose on 2026-02-11; five agents exist |
| CONTRIBUTING | "Line count < 300" warning | CI uses 600[^ci] |
| CONTRIBUTING | CI table: `discover`, `validate`, `test`, `release` | `test-modules`, `test-agents`, `test-angie-github-issue` |
| CONTRIBUTING | "modules should not depend on each other (except gcp-auth -> oidc-token)" | true for plain modules; agents depend on several |

[^ci]: CI workflow
