"""GitHub Actions OIDC credential generation script."""

import json


def generate_credentials_json(
    workload_identity_provider: str,
    oidc_url: str,
    oidc_token: str,
    service_account_email: str | None = None,
) -> str:
    """Generate GCP external_account credentials JSON.

    Args:
        workload_identity_provider: WIF provider resource name.
        oidc_url: GitHub Actions OIDC request URL.
        oidc_token: GitHub Actions OIDC request token.
        service_account_email: Optional service account to impersonate.

    Returns:
        JSON string for GCP credentials file.
    """
    audience = f"//iam.googleapis.com/{workload_identity_provider}"

    credentials = {
        "type": "external_account",
        "audience": audience,
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "url": f"{oidc_url}&audience={audience}",
            "headers": {"Authorization": f"bearer {oidc_token}"},
            "format": {"type": "json", "subject_token_field_name": "value"},
        },
    }

    if service_account_email:
        credentials["service_account_impersonation_url"] = (
            f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
            f"{service_account_email}:generateAccessToken"
        )

    return json.dumps(credentials, indent=2)


def generate_credentials_script(
    workload_identity_provider: str,
    service_account_email: str | None = None,
) -> str:
    """Generate a shell script that creates the GCP credentials JSON.

    The script reads ACTIONS_ID_TOKEN_REQUEST_TOKEN and ACTIONS_ID_TOKEN_REQUEST_URL
    from env vars and embeds them in the credentials file. This keeps secrets out
    of Dagger's cache.

    Args:
        workload_identity_provider: WIF provider resource name.
        service_account_email: Optional service account to impersonate.

    Returns:
        Shell script that generates /tmp/gcp-credentials.json.
    """
    audience = f"//iam.googleapis.com/{workload_identity_provider}"

    # Build optional service account impersonation line
    sa_line = ""
    if service_account_email:
        sa_url = (
            f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
            f"{service_account_email}:generateAccessToken"
        )
        sa_line = f',\n  "service_account_impersonation_url": "{sa_url}"'

    # Use heredoc with variable expansion (no external tools needed)
    # Note: In Python f-strings, {{ and }} produce literal { and }
    return f'''set -e
[ -z "$ACTIONS_ID_TOKEN_REQUEST_URL" ] && echo "ERROR: ACTIONS_ID_TOKEN_REQUEST_URL not set" >&2 && exit 1
[ -z "$ACTIONS_ID_TOKEN_REQUEST_TOKEN" ] && echo "ERROR: ACTIONS_ID_TOKEN_REQUEST_TOKEN not set" >&2 && exit 1
cat > /tmp/gcp-credentials.json <<EOF
{{
  "type": "external_account",
  "audience": "{audience}",
  "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
  "token_url": "https://sts.googleapis.com/v1/token",
  "credential_source": {{
    "url": "$ACTIONS_ID_TOKEN_REQUEST_URL&audience={audience}",
    "headers": {{"Authorization": "bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN"}},
    "format": {{"type": "json", "subject_token_field_name": "value"}}
  }}{sa_line}
}}
EOF
'''
