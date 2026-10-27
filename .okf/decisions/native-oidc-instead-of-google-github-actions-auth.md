---
type: Decision
title: "Native OIDC in Dagger instead of google-github-actions/auth"
description: "GCP authentication in CI is done inside Dagger modules from the GitHub OIDC request token, with no external auth Action."
tags: [decision, gcp, auth, oidc, ci]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: native
    resource: https://github.com/telchak/daggerverse/commit/b14b924fd7c46a87a896a66dce55fbe6ff9789e9
    title: "feat: remove google-github-actions/auth dependency, use native OIDC"
    author: human:telchak
    last_modified: 2025-12-30T10:54:04+01:00
  - id: agnostic
    resource: https://github.com/telchak/daggerverse/commit/56c40212e074785ee48432a5198f7fefa64c3168
    title: "refactor(gcp-auth): use oidc-token module for CI-agnostic authentication"
    author: human:telchak
    last_modified: 2026-01-06T18:57:34+01:00
---

# Decision (2025-12-30)

Drop `google-github-actions/auth`; pass `ACTIONS_ID_TOKEN_REQUEST_TOKEN` and
`ACTIONS_ID_TOKEN_REQUEST_URL` straight to Dagger (`env:` secrets) and build Workload Identity
Federation credentials inside the module.[^native]

# Why

The pipeline stays portable: the same Dagger call works on GitHub Actions, GitLab CI or
CircleCI, with only the token source changing. Generalised on 2026-01-06 with
[oidc-token](/modules/oidc-token.md) and the `*_from_oidc_token` functions.[^agnostic]

A short-lived return to the Action for Firebase tests (2026-01-02) was undone once gcp-firebase
supported OIDC directly.

[^native]: feat: remove google-github-actions/auth dependency, use native OIDC
[^agnostic]: refactor(gcp-auth): use oidc-token module for CI-agnostic authentication
