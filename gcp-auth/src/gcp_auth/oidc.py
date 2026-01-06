"""OIDC credential generation for GCP Workload Identity Federation."""

import json


def generate_file_based_credentials(
    workload_identity_provider: str,
    service_account_email: str | None = None,
    token_file_path: str = "/tmp/oidc-token",
) -> str:
    """Generate external_account credentials with file-based token source.

    Use this when you already have the OIDC token and want to pass it directly.

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
