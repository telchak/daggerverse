"""Examples for using the gcp-firebase Dagger module.

This module demonstrates the three authentication approaches supported by gcp-firebase:

- Option A: Service Account Credentials (JSON key file)
- Option B: OIDC Token with Workload Identity Federation (recommended for CI/CD)
- Option C: Legacy Access Token (deprecated, for backward compatibility)
"""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type

_DEFAULT_BUILD_CMD = "npm run build"


@object_type
class GcpFirebaseExamples:
    """Usage examples for gcp-firebase module demonstrating all authentication options."""

    # =========================================================================
    # OPTION A: Service Account Credentials (JSON key)
    # =========================================================================
    # Use when you have a service account JSON key file.
    # The module mounts the credentials and sets GOOGLE_APPLICATION_CREDENTIALS.

    @function
    async def deploy_with_service_account(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials JSON")],
        project_id: Annotated[str, Doc("Firebase project ID")],
    ) -> str:
        """Deploy using service account JSON credentials.

        This is the simplest approach when you have a service account key file.
        The module handles mounting the credentials and setting environment variables.

        Example:
            dagger call deploy-with-service-account \
                --source=. \
                --credentials=env:GOOGLE_CREDENTIALS \
                --project-id=my-project
        """
        return await dag.gcp_firebase().deploy(
            project_id=project_id,
            source=source,
            credentials=credentials,
            build_command=_DEFAULT_BUILD_CMD,
            deploy_functions=True,
        )

    @function
    async def run_script_with_service_account(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials JSON")],
        script: Annotated[str, Doc("Script path to run")],
    ) -> str:
        """Run a Node.js/TypeScript script with service account credentials.

        Example:
            dagger call run-script-with-service-account \
                --source=. \
                --credentials=env:GOOGLE_CREDENTIALS \
                --script="src/seed-data.ts"
        """
        return await dag.gcp_firebase().scripts().node(
            source=source,
            script=script,
            credentials=credentials,
            working_dir="functions",
        )

    # =========================================================================
    # OPTION B: OIDC Token with Workload Identity Federation (Recommended)
    # =========================================================================
    # Use for CI/CD pipelines (GitHub Actions, GitLab CI, CircleCI).
    # No long-lived credentials needed - uses short-lived OIDC tokens.

    @function
    async def deploy_with_oidc_token(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        oidc_token: Annotated[dagger.Secret, Doc("OIDC JWT token from CI provider")],
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> str:
        """Deploy using OIDC token with Workload Identity Federation.

        This is the recommended approach for CI/CD pipelines. It uses short-lived
        OIDC tokens instead of long-lived service account keys.

        The OIDC token can come from any CI provider:
        - GitHub Actions: dag.oidc_token().github_token(...)
        - GitLab CI: dag.oidc_token().gitlab_token(...)
        - CircleCI: dag.oidc_token().circleci_token(...)

        Example (with pre-fetched token):
            dagger call deploy-with-oidc-token \
                --source=. \
                --oidc-token=env:OIDC_TOKEN \
                --workload-identity-provider="projects/123/locations/global/..." \
                --project-id=my-project
        """
        return await dag.gcp_firebase().deploy(
            project_id=project_id,
            source=source,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            build_command=_DEFAULT_BUILD_CMD,
            deploy_functions=True,
        )

    @function
    async def deploy_from_github_actions(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> str:
        """Complete example: Deploy from GitHub Actions using OIDC.

        This shows the full flow for GitHub Actions:
        1. Fetch OIDC token using oidc-token module
        2. Deploy using the token with Workload Identity Federation

        GitHub Actions workflow requirements:
        - permissions: id-token: write
        - Pass ACTIONS_ID_TOKEN_REQUEST_TOKEN and ACTIONS_ID_TOKEN_REQUEST_URL

        Example GitHub Actions step:
            - name: Deploy to Firebase
              run: |
                dagger call deploy-from-github-actions \
                  --source=. \
                  --workload-identity-provider="${{ secrets.WIF_PROVIDER }}" \
                  --project-id="${{ secrets.PROJECT_ID }}" \
                  --oidc-request-token=env:ACTIONS_ID_TOKEN_REQUEST_TOKEN \
                  --oidc-request-url=env:ACTIONS_ID_TOKEN_REQUEST_URL
              env:
                ACTIONS_ID_TOKEN_REQUEST_TOKEN: ${{ secrets.ACTIONS_ID_TOKEN_REQUEST_TOKEN }}
                ACTIONS_ID_TOKEN_REQUEST_URL: ${{ secrets.ACTIONS_ID_TOKEN_REQUEST_URL }}
        """
        # Step 1: Fetch OIDC token from GitHub Actions with GCP audience
        audience = f"//iam.googleapis.com/{workload_identity_provider}"
        oidc_token = dag.oidc_token().github_token(
            request_token=oidc_request_token,
            request_url=oidc_request_url,
            audience=audience,
        )

        # Step 2: Deploy using the OIDC token
        return await dag.gcp_firebase().deploy(
            project_id=project_id,
            source=source,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            build_command=_DEFAULT_BUILD_CMD,
            deploy_functions=True,
        )

    @function
    async def deploy_preview_from_github_actions(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID (e.g., pr-123)")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> str:
        """Deploy a preview channel from GitHub Actions using OIDC.

        Returns the preview URL.
        """
        audience = f"//iam.googleapis.com/{workload_identity_provider}"
        oidc_token = dag.oidc_token().github_token(
            request_token=oidc_request_token,
            request_url=oidc_request_url,
            audience=audience,
        )

        return await dag.gcp_firebase().deploy_preview(
            project_id=project_id,
            channel_id=channel_id,
            source=source,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            build_command=_DEFAULT_BUILD_CMD,
            expires="7d",
        )

    # =========================================================================
    # OPTION C: Legacy Access Token (Deprecated)
    # =========================================================================
    # For backward compatibility. Prefer OIDC or service account credentials.

    @function
    async def deploy_with_access_token(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory with firebase.json")],
        access_token: Annotated[dagger.Secret, Doc("GCP access token (deprecated)")],
        project_id: Annotated[str, Doc("Firebase project ID")],
    ) -> str:
        """Deploy using a pre-fetched access token (deprecated).

        This method is deprecated. Prefer:
        - OIDC tokens for CI/CD (Option B)
        - Service account credentials for local development (Option A)

        Access tokens expire quickly and require external token refresh.
        """
        return await dag.gcp_firebase().deploy(
            project_id=project_id,
            source=source,
            access_token=access_token,
            build_command=_DEFAULT_BUILD_CMD,
            deploy_functions=True,
        )
