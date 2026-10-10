---
type: Playbook
title: "Upgrade the Dagger engine version"
description: "How a Dagger engine bump flows through Renovate, the self-hosted runner label, dagger.json files and CI."
tags: [playbook, dagger, dependencies]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: renovate
    resource: https://github.com/telchak/daggerverse/blob/main/renovate.json
    title: "renovate.json"
    author: human:telchak
    last_modified: 2026-04-14T15:45:03+02:00
  - id: bump
    resource: https://github.com/telchak/daggerverse/commit/015480db9479042a02f04661235d11c726658645
    title: "chore(deps): update dependency dagger/dagger to v0.21.10"
    author: process:renovate
    last_modified: 2026-10-01T11:09:06+00:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
---

Usually Renovate opens one grouped "dagger engine" PR.[^renovate] It must change, consistently:

- `engineVersion` in every `dagger.json` (17 modules + `tests/`, examples are ignored),
- `DAGGER_VERSION` in `ci.yml`,
- every `runs-on: dagger-v<ver>` label,
- the README badge.[^bump]

Checklist:

1. Make sure a self-hosted runner with the new `dagger-v<ver>` label exists, or every job queues
   forever.[^ci] See [self-hosted runners](/decisions/self-hosted-dagger-runners.md).
2. Read the release notes for the versions skipped ([breaking changes](/dagger/breaking-changes.md)).
3. Let the full CI run: agent tests catch LLM/API behaviour changes that module tests do not.
4. If `dagger develop` regenerates `sdk/` differently (Python SDK changes), check `uv.lock` still
   matches; `uv_build` stays pinned by the template.
5. Update CONTRIBUTING's quoted version and this bundle's [Dagger platform](/dagger/platform.md)
   concept.

[^renovate]: renovate.json
[^bump]: chore(deps): update dependency dagger/dagger to v0.21.10
[^ci]: CI workflow
