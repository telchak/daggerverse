---
type: AI Agent
title: "Speck (spec-driven development agent)"
description: "AI agent that turns a prompt or GitHub issue into a spec, a technical plan, and a JSON task decomposition assigning agents and models, designed for GitHub Actions matrices."
resource: https://github.com/telchak/daggerverse/tree/main/speck
tags: [agent, llm, spec-driven, planning]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/speck/src/speck/main.py
    title: "speck/src/speck/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: agent-readme
    resource: https://github.com/telchak/daggerverse/blob/main/speck/README.md
    title: "speck/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: prompts
    resource: https://github.com/telchak/daggerverse/tree/main/speck/src/speck/prompts
    title: "speck prompt files"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/speck/dagger-module.toml
    title: "speck/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: added
    resource: https://github.com/telchak/daggerverse/commit/4091f9541d63b4ab4b815c30ab6f0ef7939b9428
    title: "feat(speck): Add Speck agent and enrich Daggie with toolchains/checks knowledge"
    author: human:telchak
    last_modified: 2026-03-21T23:15:19+01:00
  - id: kebab
    resource: https://github.com/telchak/daggerverse/commit/5c6d03d0ab12f4fa66aef955eb2a6d9d130c95c3
    title: "fix(speck): Use kebab-case entrypoints in Speck output for Dagger CLI compatibility"
    author: human:telchak
    last_modified: 2026-03-22T15:07:12+01:00
  - id: json
    resource: https://github.com/telchak/daggerverse/commit/7ec02a5512e913e9230c5bf36cba93600d129873
    title: "fix(speck): Fix malformed json output errors"
    author: human:telchak
    last_modified: 2026-03-22T23:27:34+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Entrypoints

| Function | Output |
|----------|--------|
| `specify(prompt? , issue_id?, repository?, github_token?)` | spec markdown |
| `plan(spec, tech_stack?)` | plan markdown |
| `decompose(prompt/issue, agents, tech_stack, model_family, include_tests, include_review, create_pr)` | JSON |
| `decompose_from_spec(spec, plan, agents, model_family, ...)` | JSON |

Inspired by GitHub's spec-kit.[^agent-readme] The JSON (tasks with agent, entrypoint, model,
dependencies; `execution_plan.phases`, each with `pr_branch` when `create_pr`) is meant for
`fromJson()` + a matrix strategy that dispatches [Monty](/agents/monty.md),
[Angie](/agents/angie.md), [Daggie](/agents/daggie.md)... Entrypoints are emitted in kebab-case
(`write-tests`) so they can be passed straight to `dagger api call`.[^kebab]

# Implementation notes

- Uses [agent-base](/agents/agent-base.md) on the Python SDK runtime;[^manifest] no MCP servers
  (so the `mcp` tool is hidden), no `@agent` function; blocks its own four entrypoints and its
  constructor field `source`. Inputs reach the prompts under `## Input values`.[^main]
- `_extract_and_validate_json` strips markdown fences, surrounding prose and trailing commas,
  then `json.loads` to validate.[^json]
- `_MODEL_FAMILIES` maps complexity `low/medium/high` to model IDs for `claude`, `gemini` and
  `openai`. These IDs go stale as providers ship new models; check them when touching Speck.
- CI forces `GEMINI_MODEL=gemini-2.5-pro` for `speck-*` tests "for better JSON output
  reliability".[^ci]
- `.agent-tests`: `specify plan decompose decompose-with-pipeline decompose-with-pr`.

Added 2026-03-21.[^added] The root README lists Speck since the 1.0 migration.

[^main]: speck/src/speck/main.py
[^agent-readme]: speck/README.md
[^manifest]: speck/dagger-module.toml
[^added]: feat(speck): Add Speck agent and enrich Daggie with toolchains/checks knowledge
[^kebab]: fix(speck): Use kebab-case entrypoints in Speck output for Dagger CLI compatibility
[^json]: fix(speck): Fix malformed json output errors
[^ci]: CI workflow
