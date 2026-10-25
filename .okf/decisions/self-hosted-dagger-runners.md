---
type: Decision
title: "Self-hosted ARC runners labelled by Dagger version"
description: "CI jobs run on self-hosted Actions Runner Controller runners labelled dagger-v<version> instead of ubuntu-latest with engine-cache restore."
tags: [decision, ci, runners, caching]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: arc
    resource: https://github.com/telchak/daggerverse/commit/432fe2f2187ad81bc2538dd9a14c3d212436a7fb
    title: "ci(github-actions): Add ARC GitHub Runners to CI workflow"
    author: human:telchak
    last_modified: 2026-03-31T19:10:13+02:00
  - id: revert-cache
    resource: https://github.com/telchak/daggerverse/commit/301a502f0cdbe72b194202d4292ee610e635fe7d
    title: "revert: remove Dagger engine caching (added latency instead of saving)"
    author: human:telchak
    last_modified: 2026-01-02T22:49:13+01:00
  - id: vol-cache
    resource: https://github.com/telchak/daggerverse/commit/69a8dafb8e9aef54033280b54636e8ffdbc6d128
    title: "ci: fix Dagger engine caching with docker-volume-cache-action"
    author: human:telchak
    last_modified: 2026-02-22T00:28:10+01:00
  - id: ci
    resource: https://github.com/telchak/daggerverse/blob/main/.github/workflows/ci.yml
    title: "CI workflow"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: contributing
    resource: https://github.com/telchak/daggerverse/blob/main/CONTRIBUTING.md
    title: "Contributing guide, Prerequisites"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: renovate
    resource: https://github.com/telchak/daggerverse/blob/main/renovate.json
    title: "renovate.json"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

# Timeline

1. 2026-01-02: caching the engine image with docker save/load was reverted, its overhead exceeded
   the pull time saved.[^revert-cache]
2. 2026-02-22: engine state cached with `BYK/docker-volume-cache-action`, saved on `main` only.[^vol-cache]
3. 2026-03-10: replaced by self-hosted ARC runners with label `dagger-v<version>`; all restore/save
   cache steps and `_EXPERIMENTAL_DAGGER_RUNNER_HOST` removed.[^arc]

# Consequences

The runner label embeds the engine version, so it is bumped by [Renovate](/infrastructure/renovate.md)
together with `DAGGER_VERSION`, and a runner for the new version must exist before the PR can run.

With Dagger 1.0 every Dagger job runs on `dagger-v1.0.0-beta.21` (`DAGGER_VERSION: "1.0.0-beta.21"`),
so an ARC runner scale set with that label must exist before the migration merges.[^ci] The CLI
starts an engine of its own version, so CLI and engine must match on the runners too.[^contributing] Renovate's
label regex accepts prerelease suffixes, and the 1.0 betas are read as Git tags (`github-tags`
datasource), since they have no GitHub Releases.[^renovate]

[^arc]: ci(github-actions): Add ARC GitHub Runners to CI workflow
[^revert-cache]: revert: remove Dagger engine caching (added latency instead of saving)
[^vol-cache]: ci: fix Dagger engine caching with docker-volume-cache-action
[^ci]: CI workflow
[^contributing]: Contributing guide, Prerequisites
[^renovate]: renovate.json
