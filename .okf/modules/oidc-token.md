---
type: Dagger Module
title: "oidc-token"
description: "CI-agnostic OIDC JWT handling: fetch from GitHub Actions, pass through GitLab CI and CircleCI tokens, decode claims."
resource: https://github.com/telchak/daggerverse/tree/main/oidc-token
tags: [module, auth, oidc]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/oidc-token/src/oidc_token/main.py
    title: "oidc-token/src/oidc_token/main.py"
    author: human:telchak
    last_modified: 2026-01-20T20:17:15+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/oidc-token/README.md
    title: "oidc-token/README.md"
    author: human:telchak
    last_modified: 2026-01-06T19:29:21+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/oidc-token/dagger.json
    title: "oidc-token/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: cache-bust
    resource: https://github.com/telchak/daggerverse/commit/c72c7ec505d08ee4f1e9481cacbdb46020dc6722
    title: "fix: add cache busting to prevent stale OIDC/access tokens"
    author: human:telchak
    last_modified: 2026-01-09T00:24:45+01:00
  - id: rename
    resource: https://github.com/telchak/daggerverse/commit/e166bebfa89f5c88423a853d38a7537c1cc38003
    title: "refactor: rename oidc module to oidc-token"
    author: human:telchak
    last_modified: 2026-01-01T12:25:27+01:00
---

# Functions

| Function | Returns | Notes |
|----------|---------|-------|
| `github_token(request_token, request_url, audience)` | `Secret` | curls `ACTIONS_ID_TOKEN_REQUEST_URL` with the request token inside an alpine container |
| `gitlab_token(ci_job_jwt)` | `Secret` | pass-through |
| `circleci_token(oidc_token)` | `Secret` | pass-through |
| `token_claims(token)` | `str` | base64url-decodes the JWT payload, for debugging |

The GitHub fetch sets a `CACHE_BUSTER` env var with the current timestamp so Dagger never
serves a cached (expired) token.[^cache-bust] See [cache busting](/conventions/cache-busting.md).

Originally named `oidc`, renamed to `oidc-token` on 2026-01-01.[^rename] It is the only
dependency of [gcp-auth](/modules/gcp-auth.md) and the base of the
[native OIDC decision](/decisions/native-oidc-instead-of-google-github-actions-auth.md).

[^cache-bust]: fix: add cache busting to prevent stale OIDC/access tokens
[^rename]: refactor: rename oidc module to oidc-token
