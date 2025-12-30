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
from .github_oidc import generate_credentials_script
from .oidc import generate_file_based_credentials


@object_type
class GcpAuth:
    """GCP authentication utilities for Dagger pipelines."""

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
    async def oidc_credentials(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Secret:
        """Generate GCP credentials from GitHub Actions OIDC.

        Returns a Secret containing the external_account credentials JSON
        that can be used with other modules expecting credentials.
        """
        script = generate_credentials_script(workload_identity_provider, service_account_email)

        credentials_json = await (
            dag.container()
            .from_("alpine:latest")
            .with_secret_variable("ACTIONS_ID_TOKEN_REQUEST_TOKEN", oidc_request_token)
            .with_secret_variable("ACTIONS_ID_TOKEN_REQUEST_URL", oidc_request_url)
            .with_exec(["sh", "-c", script])
            .with_exec(["cat", "/tmp/gcp-credentials.json"])
            .stdout()
        )
        return dag.set_secret("gcp-oidc-credentials", credentials_json)

    @function
    def with_oidc_token(
        self,
        container: Annotated[dagger.Container, Doc("Container to configure")],
        oidc_token: Annotated[dagger.Secret, Doc("OIDC JWT token")],
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Container:
        """Configure container with a pre-obtained OIDC token (file-based credential source)."""
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

    @function
    def with_github_actions_oidc(
        self,
        container: Annotated[dagger.Container, Doc("Container to configure")],
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> dagger.Container:
        """Configure container with GitHub Actions OIDC (like google-github-actions/auth).

        The credentials file will automatically fetch OIDC tokens from GitHub's endpoint.
        No separate token fetching step needed - just like the official GitHub Action.
        """
        script = generate_credentials_script(workload_identity_provider, service_account_email)

        return (
            container
            .with_secret_variable("ACTIONS_ID_TOKEN_REQUEST_TOKEN", oidc_request_token)
            .with_secret_variable("ACTIONS_ID_TOKEN_REQUEST_URL", oidc_request_url)
            .with_exec(["sh", "-c", script])
            .with_env_variable("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/gcp-credentials.json")
            .with_env_variable("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", "/tmp/gcp-credentials.json")
        )

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
    def gcloud_container_from_github_actions(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        region: Annotated[str, Doc("Default GCP region")] = "us-central1",
        image: Annotated[str, Doc("Google Cloud SDK image")] = "google/cloud-sdk:alpine",
    ) -> dagger.Container:
        """Create authenticated gcloud container using GitHub Actions OIDC.

        This is equivalent to using google-github-actions/auth followed by gcloud setup.
        Just pass the GitHub Actions OIDC environment variables.
        """
        container = create_base_gcloud_container(image)
        container = self.with_github_actions_oidc(
            container, workload_identity_provider, oidc_request_token,
            oidc_request_url, service_account_email
        )
        container = authenticate_with_cred_file(container)
        return configure_gcloud_project(container, project_id, region)

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

    @function
    async def test_all(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Run all tests with pre-made credentials file."""
        email = await self.verify_credentials(credentials)
        out = await self.gcloud_container(credentials, project_id).with_exec(["gcloud", "config", "get", "project"]).stdout()
        pid = await self.get_project_id(credentials)
        return f"PASS: verify_credentials -> {email}\nPASS: gcloud_container -> {out.strip()}\nPASS: get_project_id -> {pid}"

    @function
    async def test_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email to impersonate")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run tests using GitHub Actions OIDC (no google-github-actions/auth needed)."""
        container = self.gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider, project_id=project_id,
            oidc_request_token=oidc_request_token, oidc_request_url=oidc_request_url,
            service_account_email=service_account, region=region,
        )
        email = await container.with_exec(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
        ).stdout()
        proj = await container.with_exec(["gcloud", "config", "get", "project"]).stdout()
        desc = await container.with_exec(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectId)"]
        ).stdout()
        return f"PASS: gcloud auth -> {email.strip()}\nPASS: gcloud project -> {proj.strip()}\nPASS: gcloud projects describe -> {desc.strip()}"
