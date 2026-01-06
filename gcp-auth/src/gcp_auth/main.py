"""GCP Authentication Module - Dagger utilities for Google Cloud Platform authentication."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type

from .gcloud_config import (
    authenticate_with_cred_file,
    configure_gcloud_project,
    create_base_gcloud_container,
    install_gcloud_components,
)
from .oidc import generate_file_based_credentials


@object_type
class GcpAuth:
    """GCP authentication utilities for Dagger pipelines.

    Supports multiple authentication methods:
    - Service account credentials (JSON key)
    - OIDC tokens from any CI provider (via oidc-token module)
    - Application Default Credentials from host

    For OIDC authentication, use the oidc-token module to fetch tokens:
        token = dag.oidc_token().github_token(...)  # or gitlab_token, circleci_token
        gcloud = dag.gcp_auth().gcloud_container_from_oidc_token(token, ...)
    """

    # ========== CREDENTIAL HELPERS ==========

    @function
    def with_credentials(
        self,
        container: Annotated[dagger.Container, Doc("Container to configure")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        credentials_path: Annotated[str, Doc("Path for credentials file")] = "/tmp/gcp-credentials.json",
        export_env_vars: Annotated[bool, Doc("Export GCP environment variables")] = True,
    ) -> dagger.Container:
        """Add GCP credentials to container and optionally export environment variables."""
        configured = container.with_mounted_secret(credentials_path, credentials)

        if export_env_vars:
            configured = (
                configured
                .with_env_variable("GOOGLE_APPLICATION_CREDENTIALS", credentials_path)
                .with_env_variable("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", credentials_path)
            )

        return configured

    @function
    def with_oidc_token(
        self,
        container: Annotated[dagger.Container, Doc("Container to configure")],
        oidc_token: Annotated[dagger.Secret, Doc("OIDC JWT token from any CI provider")],
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Container:
        """Configure container with an OIDC token for GCP authentication.

        The token can come from any CI provider (GitHub, GitLab, CircleCI, etc.).
        Use the oidc-token module to fetch tokens from your CI provider.

        Example:
            token = dag.oidc_token().github_token(request_token, request_url, audience)
            container = dag.gcp_auth().with_oidc_token(container, token, wif_provider)
        """
        credentials_json = generate_file_based_credentials(
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

    # ========== GCLOUD CONTAINERS ==========

    @function
    def gcloud_container(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("Default GCP region")] = "us-central1",
        image: Annotated[str, Doc("Google Cloud SDK image")] = "google/cloud-sdk:alpine",
        components: Annotated[list[str] | None, Doc("Additional gcloud components")] = None,
    ) -> dagger.Container:
        """Create authenticated gcloud SDK container using service account credentials."""
        container = create_base_gcloud_container(image)
        container = self.with_credentials(container, credentials)
        container = authenticate_with_cred_file(container)
        container = configure_gcloud_project(container, project_id, region)
        return install_gcloud_components(container, components)

    @function
    def gcloud_container_from_oidc_token(
        self,
        oidc_token: Annotated[dagger.Secret, Doc("OIDC JWT token from any CI provider")],
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        region: Annotated[str, Doc("Default GCP region")] = "us-central1",
        image: Annotated[str, Doc("Google Cloud SDK image")] = "google/cloud-sdk:alpine",
    ) -> dagger.Container:
        """Create authenticated gcloud container using an OIDC token.

        This is the generic, CI-agnostic method. Use the oidc-token module
        to fetch tokens from your CI provider (GitHub, GitLab, CircleCI, etc.).

        Example (GitHub Actions):
            token = dag.oidc_token().github_token(request_token, request_url, audience)
            gcloud = dag.gcp_auth().gcloud_container_from_oidc_token(token, wif_provider, project_id)

        Example (GitLab CI):
            token = dag.oidc_token().gitlab_token(ci_job_jwt)
            gcloud = dag.gcp_auth().gcloud_container_from_oidc_token(token, wif_provider, project_id)
        """
        container = create_base_gcloud_container(image)
        container = self.with_oidc_token(
            container, oidc_token, workload_identity_provider, service_account_email
        )
        container = authenticate_with_cred_file(container)
        return configure_gcloud_project(container, project_id, region)

    @function
    async def gcloud_container_from_github_actions(
        self,
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        region: Annotated[str, Doc("Default GCP region")] = "us-central1",
        image: Annotated[str, Doc("Google Cloud SDK image")] = "google/cloud-sdk:alpine",
    ) -> dagger.Container:
        """Create authenticated gcloud container using GitHub Actions OIDC.

        Convenience wrapper that uses oidc-token module to fetch the token.
        Equivalent to: dag.oidc_token().github_token() + gcloud_container_from_oidc_token()
        """
        # Use oidc-token module to fetch the GitHub Actions token
        oidc_token = await dag.oidc_token().github_token(
            request_token=oidc_request_token,
            request_url=oidc_request_url,
            audience=f"//iam.googleapis.com/{workload_identity_provider}",
        )
        return self.gcloud_container_from_oidc_token(
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            service_account_email=service_account_email,
            region=region,
            image=image,
        )

    @function
    def gcloud_container_from_host(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("Default GCP region")] = "us-central1",
        image: Annotated[str, Doc("Google Cloud SDK image")] = "google/cloud-sdk:alpine",
        components: Annotated[list[str] | None, Doc("Additional gcloud components")] = None,
        gcloud_config_path: Annotated[str, Doc("Path to gcloud config on host")] = "",
    ) -> dagger.Container:
        """Create authenticated gcloud SDK container using ADC from host."""
        container = create_base_gcloud_container(image)

        if not gcloud_config_path:
            gcloud_config_dir = dag.host().directory(
                path="~/.config/gcloud",
                exclude=["logs/", "legacy_credentials/", "credentials.db"],
            )
        else:
            gcloud_config_dir = dag.host().directory(path=gcloud_config_path)

        container = (
            container
            .with_directory("/root/.config/gcloud", gcloud_config_dir)
            .with_env_variable(
                "GOOGLE_APPLICATION_CREDENTIALS",
                "/root/.config/gcloud/application_default_credentials.json",
            )
        )

        container = configure_gcloud_project(container, project_id, region)
        return install_gcloud_components(container, components)

    # ========== CREDENTIALS & ACCESS TOKENS ==========

    @function
    async def credentials_from_oidc_token(
        self,
        oidc_token: Annotated[dagger.Secret, Doc("OIDC JWT token from any CI provider")],
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Secret:
        """Get GCP credentials as a Secret from an OIDC token.

        Returns credentials JSON that can be used with any GCP SDK via
        GOOGLE_APPLICATION_CREDENTIALS. Works with any CI provider.

        Example (GitHub Actions):
            token = dag.oidc_token().github_token(request_token, request_url, audience)
            credentials = dag.gcp_auth().credentials_from_oidc_token(token, wif_provider, project_id)

        Example (GitLab CI):
            token = dag.oidc_token().gitlab_token(ci_job_jwt)
            credentials = dag.gcp_auth().credentials_from_oidc_token(token, wif_provider, project_id)
        """
        gcloud = self.gcloud_container_from_oidc_token(
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            service_account_email=service_account_email,
        )
        credentials_content = await gcloud.file("/tmp/gcp-credentials.json").contents()
        return dag.set_secret("gcp_credentials", credentials_content)

    @function
    async def credentials_from_github_actions(
        self,
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Secret:
        """Get GCP credentials as a Secret from GitHub Actions OIDC.

        Convenience wrapper for GitHub Actions. Returns credentials JSON that
        can be used with any GCP SDK via GOOGLE_APPLICATION_CREDENTIALS.
        """
        oidc_token = await dag.oidc_token().github_token(
            request_token=oidc_request_token,
            request_url=oidc_request_url,
            audience=f"//iam.googleapis.com/{workload_identity_provider}",
        )
        return await self.credentials_from_oidc_token(
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            service_account_email=service_account_email,
        )

    @function
    async def access_token_from_oidc_token(
        self,
        oidc_token: Annotated[dagger.Secret, Doc("OIDC JWT token from any CI provider")],
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Secret:
        """Get a GCP access token from an OIDC token.

        Returns an access token for APIs that accept Bearer tokens (e.g., Firebase CLI).
        For SDKs that use ADC, use credentials_from_oidc_token instead.
        """
        gcloud = self.gcloud_container_from_oidc_token(
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            service_account_email=service_account_email,
        )
        token_output = await gcloud.with_exec(["gcloud", "auth", "print-access-token"]).stdout()
        return dag.set_secret("gcp_access_token", token_output.strip())

    @function
    async def access_token_from_github_actions(
        self,
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Secret:
        """Get a GCP access token from GitHub Actions OIDC.

        Convenience wrapper for GitHub Actions. Returns an access token for APIs
        that accept Bearer tokens (e.g., Firebase CLI).
        """
        oidc_token = await dag.oidc_token().github_token(
            request_token=oidc_request_token,
            request_url=oidc_request_url,
            audience=f"//iam.googleapis.com/{workload_identity_provider}",
        )
        return await self.access_token_from_oidc_token(
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            service_account_email=service_account_email,
        )

    # ========== UTILITIES ==========

    @function
    async def verify_credentials(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
    ) -> str:
        """Verify GCP credentials and return service account email."""
        container = create_base_gcloud_container()
        container = self.with_credentials(container, credentials)
        container = authenticate_with_cred_file(container)

        output = await (
            container
            .with_exec(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
            .stdout()
        )

        email = output.strip()
        if not email:
            raise ValueError("Failed to authenticate: no active account found")

        return email

    @function
    async def get_project_id(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
    ) -> str:
        """Extract project ID from credentials (service account key or WIF)."""
        from .helpers import GET_PROJECT_ID_SCRIPT
        output = await (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "add", "--no-cache", "jq"])
            .with_secret_variable("GCP_CREDENTIALS", credentials)
            .with_exec(["sh", "-c", GET_PROJECT_ID_SCRIPT])
            .stdout()
        )
        project_id = output.strip()
        if not project_id:
            raise ValueError("No project_id found in credentials")
        return project_id

    @function
    def configure_docker_auth(
        self,
        container: Annotated[dagger.Container, Doc("Container with Docker CLI")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        registries: Annotated[list[str] | None, Doc("Artifact Registry hostnames")] = None,
    ) -> dagger.Container:
        """Configure Docker authentication for GCP Artifact Registry."""
        configured = self.with_credentials(container, credentials)

        if registries is None:
            registries = ["us-central1-docker.pkg.dev", "gcr.io", "us.gcr.io", "eu.gcr.io", "asia.gcr.io"]

        for registry in registries:
            configured = configured.with_exec(["gcloud", "auth", "configure-docker", registry, "--quiet"])

        return configured
