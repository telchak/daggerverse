---
type: Process
title: "Release process (per-module semver tags)"
description: "On every push to main, each module changed since its last tag gets a new <module>/vX.Y.Z tag computed by the repo's own semver module; a feat! migration commit takes every module to v1.0.0 for Dagger 1.0."
tags: [release, versioning, ci]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, release job"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: semver
    resource: https://github.com/telchak/daggerverse/blob/main/semver/src/semver/main.py
    title: "semver/src/semver/main.py"
    author: human:telchak
    last_modified: 2026-03-01T19:35:32+01:00
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
    title: "Repository README, Installation and Publishing"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Steps

For every module and agent:[^ci]

1. `LATEST_TAG=$(git tag -l "<module>/v*" --sort=-v:refname | head -n1)`.
2. If a tag exists and `git diff --quiet $LATEST_TAG HEAD -- <module>/`, skip.[^only-changed]
3. Otherwise `dagger api call -m ./semver release --source=. --tag-prefix="<module>/"
   --initial-version="v0.1.0" --github-token=env:GITHUB_TOKEN`.

The release job needs `check`, `test-modules`, `test-agents` and `test-angie-github-issue` to
pass, and `workflow_dispatch` with `dry_run=true` skips tagging. The Dagger 1.0 migration changed
only the CLI verb and the `check` dependency; the mechanism is the same.

# Installing a release

On Dagger 1.0: `dagger module install github.com/telchak/daggerverse/<module>@vX.Y.Z` (into the
workspace) or `dagger module client add <ref> --sdk=python` (as a dependency of a module).
`@vX.Y.Z` selects the module's own `<module>/vX.Y.Z` tag, `@vX.Y` and `@vX` pick the latest
matching one, and no version means the latest release; the resolved tag is recorded in
`dagger.lock`.[^readme] As of 2026-10-24 the latest tags range from `speck/v0.2.3` to
`gcp-cloud-run/v0.4.4` (e.g. `daggie/v0.3.5`).

# The Dagger 1.0 release

Commit the migration as `feat!:` (or with `BREAKING CHANGE`). The semver module turns a breaking
commit into a major bump, `0.3.x` -> `1.0.0`,[^semver] and it reads every repository commit since
a module's tag, so every module (all of them changed in the migration) is released as
`<module>/v1.0.0`. The `<module>/v0.x` tags stay: they still carry `dagger.json` and keep working
for Dagger 0.x users.[^readme]

# Gotchas

- A change under `_agent_base/` does not change any agent directory, so it does not by itself
  trigger an agent release.
- Bump type is computed from all repository commits since the module's tag; see the
  [semver module](/modules/semver.md).
- Commit messages therefore matter: see [Conventional Commits](/conventions/conventional-commits.md).
- Whether daggerverse.dev indexes modules that only have a `dagger-module.toml` is unverified, and
  1.0 has no `dagger publish`; see [known issues](/dagger/known-issues-1-0-beta.md) and
  [Daggerverse publishing](/dagger/daggerverse-publishing.md).

# History

Until 2026-03-05 the job also created a dated CalVer GitHub release (`vYYYY.MM.DD`) listing every
module version; that step was dropped in favour of a job summary table.[^publishing]

[^ci]: CI workflow, release job
[^semver]: semver/src/semver/main.py
[^publishing]: fix: improve daggerverse publishing (module descriptions, license format, release tags)
[^only-changed]: fix: only tag modules with actual code changes
[^readme]: Repository README, Installation and Publishing
