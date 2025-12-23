# OIDC - Dagger Module

Universal OIDC token handling for CI/CD providers.

## Overview

This module provides functions to obtain OIDC JWT tokens from various CI/CD providers. These tokens can be used with cloud provider authentication modules (like `gcp-auth`) for **keyless authentication** via Workload Identity Federation.

## Supported CI Providers

| Provider | Function | Environment Variables |
|----------|----------|----------------------|
| GitHub Actions | `github-token` | `ACTIONS_ID_TOKEN_REQUEST_TOKEN`, `ACTIONS_ID_TOKEN_REQUEST_URL` |
| GitLab CI | `gitlab-token` | `CI_JOB_JWT_V2` |
| CircleCI | `circleci-token` | `CIRCLE_OIDC_TOKEN` |

## Functions

### `github-token`

Fetch OIDC JWT token from GitHub Actions.

```bash
dagger call github-token \
  --request-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
  --request-url=env:ACTIONS_ID_TOKEN_REQUEST_URL \
  --audience="//iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/providers/github"
```

**Requirements:**
- `id-token: write` permission in your workflow

### `gitlab-token`

Pass through GitLab CI OIDC JWT token.

```bash
dagger call gitlab-token \
  --ci-job-jwt=env:CI_JOB_JWT_V2
```

**Requirements:**
- `id_tokens` configuration in your `.gitlab-ci.yml`

### `circleci-token`

Pass through CircleCI OIDC JWT token.

```bash
dagger call circleci-token \
  --oidc-token=env:CIRCLE_OIDC_TOKEN
```

**Requirements:**
- OIDC enabled in your CircleCI project settings

### `token-claims`

Decode and display the claims from an OIDC JWT token (for debugging).

```bash
dagger call token-claims --token=env:MY_TOKEN
```

## Usage with Cloud Providers

### With gcp-auth module

```yaml
# GitHub Actions
jobs:
  deploy:
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: |
          # Get OIDC token and use with gcp-auth
          dagger call -m oidc github-token \
            --request-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
            --request-url=env:ACTIONS_ID_TOKEN_REQUEST_URL \
            --audience="//iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/providers/github" \
            --output=token.txt

          dagger call -m gcp-auth gcloud-container-from-oidc \
            --oidc-token=file:token.txt \
            --workload-identity-provider="projects/123/locations/global/workloadIdentityPools/pool/providers/github" \
            --project-id="my-project" \
            with-exec --args="gcloud","version"
```

### GitLab CI Example

```yaml
# .gitlab-ci.yml
deploy:
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: https://iam.googleapis.com/projects/123/locations/global/workloadIdentityPools/pool/providers/gitlab
  script:
    - dagger call -m gcp-auth gcloud-container-from-oidc \
        --oidc-token=env:GITLAB_OIDC_TOKEN \
        --workload-identity-provider="projects/123/locations/global/workloadIdentityPools/pool/providers/gitlab" \
        --project-id="my-project" \
        with-exec --args="gcloud","version"
```

## Why Use This Module?

1. **Abstraction**: Separates CI provider token handling from cloud authentication
2. **Reusability**: Same token can be used with multiple cloud providers
3. **Debugging**: `token-claims` helps troubleshoot OIDC issues
4. **Extensibility**: Easy to add new CI providers

## License

Apache-2.0
