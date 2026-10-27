---
type: Dagger Module
title: "semver"
description: "Semantic Versioning driven by Conventional Commits, with monorepo tag prefixes; the engine behind this repository's releases."
resource: https://github.com/telchak/daggerverse/tree/main/semver
tags: [module, versioning, release]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/semver/src/semver/main.py
    title: "semver/src/semver/main.py"
    author: human:telchak
    last_modified: 2026-03-01T19:35:32+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/semver/README.md
    title: "semver/README.md"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/semver/dagger-module.toml
    title: "semver/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow, release job"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Installation"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: first-release
    resource: https://github.com/telchak/daggerverse/commit/37df6a5f95253dc625307aed59a6cddb06928658
    title: "fix(semver): use initial version as-is for first release"
    author: human:telchak
    last_modified: 2026-03-01T19:35:32+01:00
---

# Functions

| Function | Purpose |
|----------|---------|
| `next(source, tag_prefix="", default_bump, initial_version)` | Next version from commits since the last matching tag |
| `bump_type(source, tag_prefix)` | `major` / `minor` / `patch` / `none` |
| `current(source, tag_prefix, initial_version)` | Latest matching tag |
| `release(source, github_token, tag_prefix, default_bump, initial_version, dry_run)` | `next` + create and push the tag |
| `bump(source, bump_type, tag_prefix, initial_version)` | Explicit bump, ignores commits |
| `tag(source, version, github_token, tag_prefix, dry_run)` | Create and push a given tag |
| `changed_paths(source, tag_prefix)` | Paths changed since the last tag |

# Rules

- `BREAKING CHANGE` (anywhere in a subject or body line) or `type!:` -> major; `feat:` -> minor;
  `fix:`, `perf:`, `refactor:` -> patch.[^main] [^module-readme] When no commit matches (only
  `chore:`, `docs:`, `ci:`...), `default_bump` applies, `patch` by default.
- `tag_prefix` scopes tags for monorepos (e.g. `gcp-auth/`). It is validated against
  `^[a-zA-Z0-9._/-]*$` to prevent shell injection.
- When no tag exists yet for a prefix, `initial_version` is used as-is (not bumped).[^first-release]

# Gotcha: commits are not filtered by path

`_analyze_commits` runs `git log <last_tag>..HEAD` with no pathspec, so the bump type of a
module is computed from **every** commit in the repository since that module's last tag,
not only commits touching its directory.[^main] A `feat(angie): ...` commit therefore bumps
the minor version of every other module released in the same run. The function docstring
says the prefix filters "tags and commits by path"; only tags are filtered. Treat this as
known behaviour until it is fixed (observed in code on 2026-10-10, not yet confirmed by the
maintainer).

# Used by CI

The [release job](/infrastructure/release-process.md) runs
`dagger api call -m ./semver release --source=. --tag-prefix="<module>/" --initial-version="v0.1.0" --github-token=env:GITHUB_TOKEN`
for every module whose directory changed since its last tag.[^ci] Because the repo releases itself
with its own module, a broken `semver` breaks releases for every module.

The Dagger 1.0 migration changes every module directory, and a major bump resets to `X+1.0.0`,[^main]
so one `feat!:` commit releases every module as v1.0.0 (the latest 0.x tags range from
`speck/v0.2.3` to `gcp-cloud-run/v0.4.4`). The 0.x tags keep `dagger.json` and keep working for
Dagger 0.x users.[^readme] See the
[migration decision](/decisions/migrate-to-dagger-1-0.md).

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: semver/src/semver/main.py
[^module-readme]: semver/README.md
[^manifest]: semver/dagger-module.toml
[^ci]: CI workflow, release job
[^readme]: Repository README, Installation
[^first-release]: fix(semver): use initial version as-is for first release
