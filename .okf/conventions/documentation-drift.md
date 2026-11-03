---
type: Known Issue
title: "Documentation drift"
description: "Places where README.md, module READMEs or examples disagree with the code as of 2026-10-24; check the code before trusting them."
tags: [documentation, known-issue]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: one-workflow
    resource: https://github.com/telchak/daggerverse/commit/183ab8e60066d822711d12cc2fba0a7b231e6bc6
    title: "refactor: replace 3 workflows with single ci.yml"
    author: human:telchak
    last_modified: 2025-12-31T18:25:34+01:00
  - id: mcp-examples
    resource: https://github.com/telchak/daggerverse/tree/main/dagger-mcp/examples
    title: "dagger-mcp examples"
    author: human:telchak
  - id: angular-test
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/angular_agent.py
    title: "tests/src/tests/angular_agent.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

Observed on 2026-10-24, after the Dagger 1.0 migration. Fix the docs or delete an entry here
when it is resolved.

| Doc | Says | Reality |
|-----|------|---------|
| README, Validation Pipeline table | "Function docstrings" and "Emojis in code" warnings | CI has not checked either since three workflows became `ci.yml`[^one-workflow] [^ci] |
| `dagger-mcp/examples` (Go, Python, TypeScript) | `with_mcp_server(..., dag.dagger_mcp().server())` then `last_reply()` | they are 0.x-view modules (`dagger.json`, `engineVersion` v0.19.11); on v1.0.0-beta.21 an LLM with `with_mcp_server` hangs on its second step, see [known issues](/dagger/known-issues-1-0-beta.md)[^mcp-examples] |
| Agent tests (`angular_agent.py` and siblings) | report `has_src` / `has_app` from `"src" in entries` | `Directory.entries()` lists directories with a trailing slash (`src/`), so the flag is always False; the tests still pass[^angular-test] |

Resolved by the 1.0 migration (2026-10-24): CONTRIBUTING's Dagger version, repository structure,
line limit, CI table and dependency rule; the README's Speck omissions and its "Angie, Monty, and
Daggie share `_agent_base`" (all five agents do now)[^readme]; Speck's one-line package docstring;
the gcp-cloud-run README's flat `deploy-service` / `get-service-url` calls.

[^readme]: Repository README
[^ci]: CI workflow
[^one-workflow]: refactor: replace 3 workflows with single ci.yml
[^mcp-examples]: dagger-mcp examples
[^angular-test]: tests/src/tests/angular_agent.py
