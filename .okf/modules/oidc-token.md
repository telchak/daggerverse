---
type: Dagger Module
title: "oidc-token"
description: "CI-agnostic OIDC JWT handling: fetch from GitHub Actions, pass through GitLab CI and CircleCI tokens, decode claims."
resource: https://github.com/telchak/daggerverse/tree/main/oidc-token
tags: [module, auth, oidc]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
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
    last_modified: 2026-10-24T22:00:00Z
  - id: manifest
    resource: https://github.com/telchak/daggerverse/blob/main/oidc-token/dagger-module.toml
    title: "oidc-token/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (workspace)"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
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

The caller passes the CI's token variables as secrets, e.g.
`dagger api call oidc-token gitlab-token --ci-job-jwt=env:CI_JOB_JWT_V2` (GitHub Actions:
`ACTIONS_ID_TOKEN_REQUEST_TOKEN` and `ACTIONS_ID_TOKEN_REQUEST_URL`; CircleCI:
`CIRCLE_OIDC_TOKEN`).[^module-readme]

The GitHub fetch sets a `CACHE_BUSTER` env var with the current timestamp[^main] so Dagger never
serves a cached (expired) token.[^cache-bust] See [cache busting](/conventions/cache-busting.md).

Originally named `oidc`, renamed to `oidc-token` on 2026-01-01.[^rename] It is the only
dependency of [gcp-auth](/modules/gcp-auth.md), as the `./oidc-token` client of the `gcp-auth`
scope in the root `dagger.toml`,[^workspace] and the base of the
[native OIDC decision](/decisions/native-oidc-instead-of-google-github-actions-auth.md).

# Layout

`dagger-module.toml` holds only `name` and the static entrypoint (`[entrypoint] kind = "dang"`,
`source = "./sdk/entrypoint"`); the generated `sdk/` and `clients/core` are committed. See
[Dagger 1.0 workspaces](/dagger/dagger-1-0-workspaces.md).[^manifest]

[^main]: oidc-token/src/oidc_token/main.py
[^module-readme]: oidc-token/README.md
[^manifest]: oidc-token/dagger-module.toml
[^workspace]: dagger.toml (workspace)
[^cache-bust]: fix: add cache busting to prevent stale OIDC/access tokens
[^rename]: refactor: rename oidc module to oidc-token
