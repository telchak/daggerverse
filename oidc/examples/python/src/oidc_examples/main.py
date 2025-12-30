"""Examples for using the oidc Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class OidcExamples:
    """Usage examples for oidc module."""

    @function
    def github_oidc_to_gcp(
        self,
        request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        workload_identity_provider: Annotated[str, Doc("GCP WIF provider resource name")],
    ) -> dagger.Secret:
        """Example: Fetch GitHub Actions OIDC token for GCP authentication.

        Use this in a GitHub Actions workflow with `id-token: write` permission
        to get a token for authenticating with GCP via Workload Identity Federation.
        """
        return dag.oidc().github_token(
            request_token=request_token,
            request_url=request_url,
            audience=workload_identity_provider,
        )

    @function
    def gitlab_oidc_passthrough(
        self,
        ci_job_jwt: Annotated[dagger.Secret, Doc("CI_JOB_JWT_V2 from GitLab CI")],
    ) -> dagger.Secret:
        """Example: Pass through GitLab CI OIDC token.

        GitLab provides the JWT directly as an environment variable.
        Configure `id_tokens` in your .gitlab-ci.yml to use this.
        """
        return dag.oidc().gitlab_token(ci_job_jwt=ci_job_jwt)

    @function
    async def debug_token_claims(
        self,
        token: Annotated[dagger.Secret, Doc("OIDC JWT token to inspect")],
    ) -> str:
        """Example: Decode and display OIDC token claims for debugging.

        Useful for troubleshooting Workload Identity Federation issues
        by inspecting the token's issuer, subject, and audience claims.
        """
        return await dag.oidc().token_claims(token=token)
