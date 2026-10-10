---
type: Dagger Module
title: "gcp-auth"
description: "GCP authentication for Dagger pipelines: authenticated gcloud containers and access tokens from OIDC/WIF, service account keys or host ADC."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-auth
tags: [module, gcp, auth, oidc]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/src/gcp_auth/main.py
    title: "gcp-auth/src/gcp_auth/main.py"
    author: human:telchak
    last_modified: 2026-03-24T14:57:11+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/README.md
    title: "gcp-auth/README.md"
    author: human:telchak
    last_modified: 2026-02-17T10:31:33+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/dagger.json
    title: "gcp-auth/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: oidc-py
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-auth/src/gcp_auth/oidc.py
    title: "gcp-auth/src/gcp_auth/oidc.py"
    author: human:telchak
    last_modified: 2026-01-20T20:17:15+01:00
  - id: refactor-oidc
    resource: https://github.com/telchak/daggerverse/commit/56c40212e074785ee48432a5198f7fefa64c3168
    title: "refactor(gcp-auth): use oidc-token module for CI-agnostic authentication"
    author: human:telchak
    last_modified: 2026-01-06T18:57:34+01:00
  - id: no-host
    resource: https://github.com/telchak/daggerverse/commit/74849b205d4446822ffb09865915c8495dd8e340
    title: "fix(gcp-auth): replace dag.host() with Directory param in gcloud_container_from_host"
    author: human:telchak
    last_modified: 2026-03-24T14:57:11+01:00
---

# Functions

| Function | Returns |
|----------|---------|
| `gcloud_container(credentials, project_id, region, image, components)` | gcloud container from a service-account JSON key |
| `gcloud_container_from_oidc_token(oidc_token, workload_identity_provider, project_id, service_account_email?, region, image)` | gcloud container from any CI's OIDC token (WIF) |
| `gcloud_container_from_github_actions(workload_identity_provider, project_id, oidc_request_token, oidc_request_url, ...)` | same, fetching the token via [oidc-token](/modules/oidc-token.md) |
| `gcloud_container_from_host(project_id, gcloud_config: Directory, ...)` | from a host `~/.config/gcloud` passed as a Directory |
| `access_token_from_oidc_token(...)`, `access_token_from_github_actions(...)` | `Secret` bearer token |
| `oidc_token_from_github_actions(workload_identity_provider, ...)` | `Secret` JWT with the GCP audience |
| `with_credentials(container, credentials, ...)`, `with_oidc_token(container, ...)` | add credentials to any container |
| `verify_credentials(credentials)`, `get_project_id(credentials)` | introspect a key (or WIF config) |
| `configure_docker_auth(container, credentials, registries)` | docker login for Artifact Registry |

Default image `google/cloud-sdk:alpine`, default region `us-central1`.[^main]

# How OIDC/WIF works here

`oidc.py` writes an `external_account` credentials JSON with audience
`//iam.googleapis.com/<workload_identity_provider>`, `token_url`
`https://sts.googleapis.com/v1/token`, a file-based `credential_source` pointing at the
mounted token, and an optional `service_account_impersonation_url`.[^oidc-py]
The same function is intentionally duplicated in `gcp-firebase/src/gcp_firebase/credentials.py`
to keep gcp-firebase dependency-free; keep both copies in sync.

The generic `*_from_oidc_token` functions accept a token from any CI (GitLab:
`dag.oidc_token().gitlab_token(...)`); the `*_from_github_actions` wrappers were made
async and rebuilt on `oidc-token` on 2026-01-06.[^refactor-oidc]

`gcloud_container_from_host` takes a `Directory` argument since 2026-03-24, because
`dag.host()` was removed from modules in Dagger v0.20.[^no-host] See
[Dagger breaking changes](/dagger/breaking-changes.md).

Access tokens are fetched with a `CACHE_BUSTER` env var, see [cache busting](/conventions/cache-busting.md).
Downstream GCP modules take the resulting container; see the
[decoupling decision](/decisions/decouple-gcp-modules-from-gcp-auth.md).

# Tests

`tests gcp-auth` exercises OIDC (always), service account key (when `GCP_SA_KEY` is set) and
access-token paths. See [tests module](/infrastructure/tests-module.md).

[^main]: gcp-auth/src/gcp_auth/main.py
[^oidc-py]: gcp-auth/src/gcp_auth/oidc.py
[^refactor-oidc]: refactor(gcp-auth): use oidc-token module for CI-agnostic authentication
[^no-host]: fix(gcp-auth): replace dag.host() with Directory param in gcloud_container_from_host
