"""GCP credential mounting utilities (inlined from gcp-auth).

This module provides credential configuration for GCP authentication without
external dependencies, supporting:
- OIDC tokens with Workload Identity Federation
- Service account JSON credentials

NOTE: The generate_wif_credentials_json() function is intentionally duplicated
from gcp-auth/src/gcp_auth/oidc.py (generate_file_based_credentials) to keep
this module self-contained with no external dependencies.
If you modify this function, please keep the other copy in sync.
"""

import json

import dagger


def generate_wif_credentials_json(
    workload_identity_provider: str,
    service_account_email: str | None = None,
    token_file_path: str = "/tmp/oidc-token",
) -> str:
    """Generate external_account credentials JSON for Workload Identity Federation.

    Args:
        workload_identity_provider: Full resource name of the WIF provider.
        service_account_email: Optional service account to impersonate.
        token_file_path: Path where the OIDC token file will be mounted.

    Returns:
        JSON string for external_account credentials.
    """
    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    credentials = {
        "type": "external_account",
        "audience": audience,
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "file": token_file_path,
            "format": {"type": "text"},
        },
    }
    if service_account_email:
        credentials["service_account_impersonation_url"] = (
            f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
            f"{service_account_email}:generateAccessToken"
        )
    return json.dumps(credentials, indent=2)


def with_oidc_token(
    container: dagger.Container,
    oidc_token: dagger.Secret,
    workload_identity_provider: str,
    service_account_email: str | None = None,
) -> dagger.Container:
    """Configure container with OIDC token for GCP Workload Identity Federation.

    Args:
        container: Container to configure.
        oidc_token: OIDC JWT token from any CI provider.
        workload_identity_provider: GCP Workload Identity Federation provider.
        service_account_email: Optional service account to impersonate.

    Returns:
        Container with GCP credentials configured.
    """
    credentials_json = generate_wif_credentials_json(
        workload_identity_provider=workload_identity_provider,
        service_account_email=service_account_email,
    )
    return (
        container
        .with_mounted_secret("/tmp/oidc-token", oidc_token)
        .with_new_file("/tmp/gcp-credentials.json", contents=credentials_json)
        .with_env_variable("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/gcp-credentials.json")
        .with_env_variable("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", "/tmp/gcp-credentials.json")
    )


def with_service_account_credentials(
    container: dagger.Container,
    credentials: dagger.Secret,
    credentials_path: str = "/tmp/gcp-credentials.json",
) -> dagger.Container:
    """Configure container with GCP service account credentials JSON.

    Args:
        container: Container to configure.
        credentials: GCP service account credentials (JSON key).
        credentials_path: Path for credentials file in container.

    Returns:
        Container with GCP credentials configured.
    """
    return (
        container
        .with_mounted_secret(credentials_path, credentials)
        .with_env_variable("GOOGLE_APPLICATION_CREDENTIALS", credentials_path)
        .with_env_variable("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", credentials_path)
    )
