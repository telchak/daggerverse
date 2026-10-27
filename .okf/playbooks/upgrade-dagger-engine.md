---
type: Playbook
title: "Upgrade the Dagger engine version"
description: "How a Dagger version bump flows on Dagger 1.0: Renovate's grouped PR, the self-hosted runner label, regenerated code, the few hand edits and the full CI."
tags: [playbook, dagger, dependencies]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: renovate
    resource: https://github.com/telchak/daggerverse/blob/main/renovate.json
    title: "renovate.json"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: claude
    resource: https://github.com/telchak/daggerverse/blob/main/CLAUDE.md
    title: "CLAUDE.md, Working rules"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: lock
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.lock
    title: "dagger.lock"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Development Setup"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: bump
    resource: https://github.com/telchak/daggerverse/commit/015480db9479042a02f04661235d11c726658645
    title: "chore(deps): update dependency dagger/dagger to v0.21.10"
    author: process:renovate
    last_modified: 2026-10-01T11:09:06+00:00
---

Usually Renovate opens one grouped "dagger engine" PR, as for the last 0.x bump to
v0.21.10.[^bump] One bump changes, together:

| What | Done by |
|------|---------|
| `DAGGER_VERSION` in `ci.yml` | Renovate[^renovate] |
| every `runs-on: dagger-v<ver>` label | Renovate |
| the root README badge (`label=Dagger&message=v<ver>`) | Renovate |
| the dagger-for-github snippets (`version: "<ver>"`) in the READMEs and Daggie's system prompt | Renovate |
| CONTRIBUTING's quoted version and the inline example in Daggie's prompt | by hand, on the same PR |
| the generated `sdk/`, `clients/`, entrypoints, `uv.lock` and the agents' `engineVersion` | `dagger generate -y` with the new CLI, pushed onto the PR[^claude] |

The CLI starts an engine of its own version, so CLI and engine always match, on the self-hosted
runners too.[^contributing] Plain modules have no `engineVersion`, and the 48 `examples/`
modules keep their own `dagger.json` (Renovate ignores them).

Checklist:

1. Make sure the ARC runner scale set with the new `dagger-v<ver>` label exists, or every Dagger
   job queues forever.[^ci] See [self-hosted runners](/decisions/self-hosted-dagger-runners.md).
2. Read what changed in between ([breaking changes](/dagger/breaking-changes.md)); 1.0 betas are
   Git tags without GitHub releases.
3. Install the new CLI, run `dagger generate -y`, and push the result onto the Renovate PR; until
   then CI's `check` job fails. To also move the Python SDK (`github.com/dagger/python-sdk`,
   pinned at v1.2.0 in `dagger.lock`), run `dagger lock update` first and commit
   `dagger.lock`.[^lock]
4. Run `dagger check`, then let the full CI run, agent tests included: they catch LLM/API
   behaviour changes that module tests do not.
5. On a Windows host `dagger check` always reports the generated files as stale (file modes, not
   content): check that `dagger generate --no-apply` shows no line changes and rely on the CI
   `check` job; see [known issues](/dagger/known-issues-1-0-beta.md).
6. Update this bundle's [Dagger platform](/dagger/platform.md) concept.

[^renovate]: renovate.json
[^ci]: CI workflow
[^claude]: CLAUDE.md, Working rules
[^lock]: dagger.lock
[^contributing]: Contributing guide, Development Setup
[^bump]: chore(deps): update dependency dagger/dagger to v0.21.10
