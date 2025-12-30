"""GitHub Actions OIDC credential generation script."""


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

    sa_impersonation = ""
    if service_account_email:
        sa_url = (
            f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
            f"{service_account_email}:generateAccessToken"
        )
        sa_impersonation = f',\n  "service_account_impersonation_url": "{sa_url}"'

    # Use explicit variable assignment to ensure proper expansion
    return f'''
# Verify env vars are set
if [ -z "$ACTIONS_ID_TOKEN_REQUEST_URL" ]; then
  echo "ERROR: ACTIONS_ID_TOKEN_REQUEST_URL is not set" >&2
  exit 1
fi
if [ -z "$ACTIONS_ID_TOKEN_REQUEST_TOKEN" ]; then
  echo "ERROR: ACTIONS_ID_TOKEN_REQUEST_TOKEN is not set" >&2
  exit 1
fi

# Build credential source URL
CRED_URL="$ACTIONS_ID_TOKEN_REQUEST_URL&audience={audience}"
AUTH_HEADER="bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN"

cat > /tmp/gcp-credentials.json << EOF
{{
  "type": "external_account",
  "audience": "{audience}",
  "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
  "token_url": "https://sts.googleapis.com/v1/token",
  "credential_source": {{
    "url": "$CRED_URL",
    "headers": {{"Authorization": "$AUTH_HEADER"}},
    "format": {{"type": "json", "subject_token_field_name": "value"}}
  }}{sa_impersonation}
}}
EOF
'''
