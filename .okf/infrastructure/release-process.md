---
type: Process
title: "Release process (per-module semver tags)"
description: "On every push to main, each module changed since its last tag gets a new <module>/vX.Y.Z tag computed by the repo's own semver module."
tags: [release, versioning, ci]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, release job"
    author: human:telchak
    last_modified: 2026-10-10T13:32:33+00:00
  - id: publishing
    resource: https://github.com/telchak/daggerverse/commit/d44547db1c67ff39bcb75b79a025b688226311ab
    title: "fix: improve daggerverse publishing (module descriptions, license format, release tags)"
    author: human:telchak
    last_modified: 2026-03-05T14:21:19+01:00
  - id: only-changed
    resource: https://github.com/telchak/daggerverse/commit/a97ec39829a5def59cfd2a81eb37a2a9037672bd
    title: "fix: only tag modules with actual code changes"
    author: human:telchak
    last_modified: 2026-01-01T21:49:57+01:00
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Publishing"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
---

# Steps

For every module and agent:[^ci]

1. `LATEST_TAG=$(git tag -l "<module>/v*" --sort=-v:refname | head -n1)`.
2. If a tag exists and `git diff --quiet $LATEST_TAG HEAD -- <module>/`, skip.[^only-changed]
3. Otherwise `dagger call -m ./semver release --source=. --tag-prefix="<module>/"
   --initial-version="v0.1.0" --github-token=env:GITHUB_TOKEN`.

The release job needs `test-modules`, `test-agents` and `test-angie-github-issue` to pass, and
`workflow_dispatch` with `dry_run=true` skips tagging.

Users install a version with `dagger install github.com/telchak/daggerverse/<module>@vX.Y.Z`.[^readme]
As of 2026-10-10 module versions are in the `v0.2.x` - `v0.4.x` range (e.g. `gcp-cloud-run/v0.4.4`,
`daggie/v0.3.5`).

# Gotchas

- A change under `_agent_base/` does not change any agent directory, so it does not by itself
  trigger an agent release.
- Bump type is computed from all repository commits since the module's tag; see the
  [semver module](/modules/semver.md).
- Commit messages therefore matter: see [Conventional Commits](/conventions/conventional-commits.md).

# History

Until 2026-03-05 the job also created a dated CalVer GitHub release (`vYYYY.MM.DD`) listing every
module version; that step was dropped in favour of a job summary table.[^publishing]

[^ci]: CI workflow, release job
[^publishing]: fix: improve daggerverse publishing (module descriptions, license format, release tags)
[^only-changed]: fix: only tag modules with actual code changes
[^readme]: Repository README, Publishing
