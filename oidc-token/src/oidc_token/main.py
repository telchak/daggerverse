"""OIDC Token Module - Universal OIDC token handling for CI/CD providers."""

import time
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class OidcToken:
    """Universal OIDC token handling for various CI/CD providers."""

    @function
    async def github_token(
        self,
        request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        audience: Annotated[str, Doc("The audience claim for the token (e.g., GCP WIF provider)")],
    ) -> dagger.Secret:
        """Fetch OIDC JWT token from GitHub Actions.

        GitHub Actions provides OIDC tokens via a REST endpoint. This function
        fetches the token with the specified audience claim.

        Requires `id-token: write` permission in your workflow.
        """
        # Script that fetches the token from GitHub's OIDC endpoint
        script = f'''
curl -s -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
    "$ACTIONS_ID_TOKEN_REQUEST_URL&audience={audience}" \
    | jq -r '.value'
'''

        # Use timestamp to bust Dagger's cache - tokens must be fresh
        cache_buster = str(int(time.time()))

        token_value = await (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "add", "--no-cache", "curl", "jq"])
            .with_secret_variable("ACTIONS_ID_TOKEN_REQUEST_TOKEN", request_token)
            .with_secret_variable("ACTIONS_ID_TOKEN_REQUEST_URL", request_url)
            .with_env_variable("CACHE_BUSTER", cache_buster)
            .with_exec(["sh", "-c", script])
            .stdout()
        )
        return dag.set_secret("oidc-token", token_value.strip())

    @function
    def gitlab_token(
        self,
        ci_job_jwt: Annotated[dagger.Secret, Doc("CI_JOB_JWT_V2 from GitLab CI")],
    ) -> dagger.Secret:
        """Pass through GitLab CI OIDC JWT token.

        GitLab CI provides the OIDC token directly as CI_JOB_JWT_V2 env var.
        This function validates and returns it as a Secret.

        Requires `id_tokens` configuration in your .gitlab-ci.yml.
        """
        # GitLab provides the JWT directly, just pass it through
        return ci_job_jwt

    @function
    def circleci_token(
        self,
        oidc_token: Annotated[dagger.Secret, Doc("CIRCLE_OIDC_TOKEN from CircleCI")],
    ) -> dagger.Secret:
        """Pass through CircleCI OIDC JWT token.

        CircleCI provides the OIDC token directly as CIRCLE_OIDC_TOKEN env var.
        This function validates and returns it as a Secret.

        Requires OIDC to be enabled in your CircleCI project settings.
        """
        # CircleCI provides the JWT directly, just pass it through
        return oidc_token

    @function
    async def token_claims(
        self,
        token: Annotated[dagger.Secret, Doc("OIDC JWT token to inspect")],
    ) -> str:
        """Decode and display the claims from an OIDC JWT token (for debugging).

        Note: This only decodes the payload, it does not verify the signature.
        """
        # JWT uses base64url encoding without padding, need to convert to standard base64
        script = '''
PAYLOAD=$(echo "$OIDC_TOKEN" | cut -d'.' -f2)
# Add padding if needed
MOD=$((${#PAYLOAD} % 4))
if [ $MOD -eq 2 ]; then PAYLOAD="${PAYLOAD}=="; elif [ $MOD -eq 3 ]; then PAYLOAD="${PAYLOAD}="; fi
# Convert base64url to base64 and decode
echo "$PAYLOAD" | tr '_-' '/+' | base64 -d | jq .
'''
        return await (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "add", "--no-cache", "jq"])
            .with_secret_variable("OIDC_TOKEN", token)
            .with_exec(["sh", "-c", script])
            .stdout()
        )
