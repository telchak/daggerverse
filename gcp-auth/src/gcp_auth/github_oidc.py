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

# Verify URL has https scheme
case "$ACTIONS_ID_TOKEN_REQUEST_URL" in
  https://*)
    ;;
  *)
    echo "ERROR: ACTIONS_ID_TOKEN_REQUEST_URL does not start with https://" >&2
    echo "URL value (first 50 chars): $(printf '%.50s' "$ACTIONS_ID_TOKEN_REQUEST_URL")" >&2
    exit 1
    ;;
esac

# Build credential source URL - use explicit assignment
OIDC_URL="$ACTIONS_ID_TOKEN_REQUEST_URL"
OIDC_TOKEN="$ACTIONS_ID_TOKEN_REQUEST_TOKEN"

# Write JSON using a subshell with redirect to ensure proper variable expansion
(
echo '{{'
echo '  "type": "external_account",'
echo '  "audience": "{audience}",'
echo '  "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",'
echo '  "token_url": "https://sts.googleapis.com/v1/token",'
echo '  "credential_source": {{'
echo "    \\"url\\": \\"$OIDC_URL&audience={audience}\\","
echo "    \\"headers\\": {{\\"Authorization\\": \\"bearer $OIDC_TOKEN\\"}},"
echo '    "format": {{"type": "json", "subject_token_field_name": "value"}}'
echo '  }}{sa_impersonation}'
echo '}}'
) > /tmp/gcp-credentials.json
'''
