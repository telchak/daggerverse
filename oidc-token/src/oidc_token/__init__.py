"""Universal OIDC token handling for CI/CD providers.

This module provides functions to obtain OIDC JWT tokens from various CI/CD
providers (GitHub Actions, GitLab CI, CircleCI). These tokens can then be
used with cloud provider authentication modules (gcp-auth, aws-auth, etc.)
for keyless authentication via Workload Identity Federation.

Supported CI Providers:
- GitHub Actions (via ACTIONS_ID_TOKEN_REQUEST_* env vars)
- GitLab CI (via CI_JOB_JWT_V2 env var)
- CircleCI (via CIRCLE_OIDC_TOKEN env var)
"""

from .main import Oidc as Oidc
