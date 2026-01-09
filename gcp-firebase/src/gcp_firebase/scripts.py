"""Firebase Scripts - Run scripts with Firebase/Firestore credentials."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


def _with_script_credentials(
    container: dagger.Container,
    # OIDC/WIF auth (recommended) - uses gcp-auth module
    oidc_token: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account_email: str | None = None,
    # Service account JSON auth - uses gcp-auth module
    credentials: dagger.Secret | None = None,
    # Legacy access token auth
    access_token: dagger.Secret | None = None,
    project_id: str | None = None,
) -> dagger.Container:
    """Configure a container with GCP credentials using gcp-auth module."""
    # Priority 1: OIDC/WIF authentication (via gcp-auth)
    if oidc_token and workload_identity_provider:
        container = dag.gcp_auth().with_oidc_token(
            container=container,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
        )
        if project_id:
            container = container.with_env_variable("GOOGLE_CLOUD_PROJECT", project_id)
        return container

    # Priority 2: Service account credentials (via gcp-auth)
    if credentials:
        return dag.gcp_auth().with_credentials(container=container, credentials=credentials)

    # Priority 3: Access token
    if access_token:
        container = container.with_secret_variable("GOOGLE_ACCESS_TOKEN", access_token)
        if project_id:
            container = container.with_env_variable("GOOGLE_CLOUD_PROJECT", project_id)
        return container

    raise ValueError(
        "Must provide one of: (oidc_token + workload_identity_provider), credentials, or access_token"
    )


@object_type
class FirebaseScripts:
    """Run scripts with Firebase/Firestore credentials.

    Provides language-specific runners for common use cases (Node.js, Python)
    and a generic container method for other languages (Go, Java, Ruby, etc.).

    All methods configure GCP Application Default Credentials (ADC), which works with:
    - Firebase Admin SDK
    - Google Cloud Firestore SDK
    - Any GCP client library that supports ADC
    """

    @function
    async def node(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        script: Annotated[str, Doc("Script path relative to working_dir")],
        # OIDC/WIF auth (recommended)
        oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token from CI provider")] = None,
        workload_identity_provider: Annotated[str | None, Doc("GCP Workload Identity Federation provider")] = None,
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        # Service account JSON auth
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials JSON")] = None,
        # Legacy access token auth
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token")] = None,
        project_id: Annotated[str | None, Doc("GCP project ID")] = None,
        # Script options
        working_dir: Annotated[str, Doc("Working directory relative to source root")] = ".",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        install_command: Annotated[str, Doc("Package install command")] = "npm ci",
        env: Annotated[list[str] | None, Doc("Environment variables (KEY=VALUE format)")] = None,
    ) -> str:
        """Run a Node.js or TypeScript script with Firebase credentials."""
        run_cmd = ["npx", "tsx", script] if script.endswith(".ts") else ["node", script]

        container = (
            dag.container()
            .from_(f"node:{node_version}-alpine")
            .with_directory("/app", source)
            .with_workdir(f"/app/{working_dir}" if working_dir != "." else "/app")
            .with_exec(["sh", "-c", install_command])
        )
        container = _with_script_credentials(
            container,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            credentials=credentials,
            access_token=access_token,
            project_id=project_id,
        )

        if env:
            for env_var in env:
                key, _, value = env_var.partition("=")
                container = container.with_env_variable(key, value)

        return await container.with_exec(run_cmd).stdout()

    @function
    async def python(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        script: Annotated[str, Doc("Script path relative to working_dir")],
        # OIDC/WIF auth (recommended)
        oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token from CI provider")] = None,
        workload_identity_provider: Annotated[str | None, Doc("GCP Workload Identity Federation provider")] = None,
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        # Service account JSON auth
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials JSON")] = None,
        # Legacy access token auth
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token")] = None,
        project_id: Annotated[str | None, Doc("GCP project ID")] = None,
        # Script options
        working_dir: Annotated[str, Doc("Working directory relative to source root")] = ".",
        python_version: Annotated[str, Doc("Python version")] = "3.12",
        install_command: Annotated[str | None, Doc("Package install command")] = None,
        env: Annotated[list[str] | None, Doc("Environment variables (KEY=VALUE format)")] = None,
    ) -> str:
        """Run a Python script with Firebase credentials."""
        container = (
            dag.container()
            .from_(f"python:{python_version}-alpine")
            .with_directory("/app", source)
            .with_workdir(f"/app/{working_dir}" if working_dir != "." else "/app")
        )

        if install_command:
            container = container.with_exec(["sh", "-c", install_command])

        container = _with_script_credentials(
            container,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            credentials=credentials,
            access_token=access_token,
            project_id=project_id,
        )

        if env:
            for env_var in env:
                key, _, value = env_var.partition("=")
                container = container.with_env_variable(key, value)

        return await container.with_exec(["python", script]).stdout()

    @function
    def container(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        base_image: Annotated[str, Doc("Base container image")],
        # OIDC/WIF auth (recommended)
        oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token from CI provider")] = None,
        workload_identity_provider: Annotated[str | None, Doc("GCP Workload Identity Federation provider")] = None,
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        # Service account JSON auth
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials JSON")] = None,
        # Legacy access token auth
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token")] = None,
        project_id: Annotated[str | None, Doc("GCP project ID")] = None,
        # Options
        working_dir: Annotated[str, Doc("Working directory relative to source root")] = ".",
    ) -> dagger.Container:
        """Get a container with Firebase credentials configured for any language."""
        container = (
            dag.container()
            .from_(base_image)
            .with_directory("/app", source)
            .with_workdir(f"/app/{working_dir}" if working_dir != "." else "/app")
        )
        return _with_script_credentials(
            container,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            credentials=credentials,
            access_token=access_token,
            project_id=project_id,
        )
