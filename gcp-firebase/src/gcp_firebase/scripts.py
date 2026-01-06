"""Firebase Scripts - Run scripts with Firebase/Firestore credentials.

This module provides utilities to execute scripts that interact with Firebase services
(Firestore, Firebase Admin SDK) using GCP credentials or access tokens.

Supported languages:
- Node.js/TypeScript: Using firebase-admin or @google-cloud/firestore
- Python: Using firebase-admin or google-cloud-firestore
- Any language: Via the generic container() method

Authentication options:
- credentials: Service account JSON key (recommended for most use cases)
- access_token: GCP access token (for CI/CD with OIDC/Workload Identity)

For more information on Firebase Admin SDKs:
https://firebase.google.com/docs/firestore/manage-data/add-data
"""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


def _with_gcp_credentials(
    container: dagger.Container,
    credentials: dagger.Secret | None = None,
    access_token: dagger.Secret | None = None,
    project_id: str | None = None,
) -> dagger.Container:
    """Configure a container with GCP credentials or access token."""
    if access_token:
        # Use access token (for CI/CD with OIDC)
        container = container.with_secret_variable("GOOGLE_ACCESS_TOKEN", access_token)
        if project_id:
            container = container.with_env_variable("GOOGLE_CLOUD_PROJECT", project_id)
        return container

    if credentials:
        # Use service account credentials (ADC)
        credentials_path = "/tmp/gcp-credentials.json"
        return (
            container
            .with_mounted_secret(credentials_path, credentials)
            .with_env_variable("GOOGLE_APPLICATION_CREDENTIALS", credentials_path)
        )

    raise ValueError("Either credentials or access_token must be provided")


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
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory containing the script")],
        script: Annotated[str, Doc("Script path relative to working_dir (e.g., 'src/seed-data.ts')")],
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials (JSON)")] = None,
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token (for CI/CD with OIDC)")] = None,
        project_id: Annotated[str | None, Doc("GCP project ID (required with access_token)")] = None,
        working_dir: Annotated[str, Doc("Working directory relative to source root")] = ".",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        install_command: Annotated[str, Doc("Package install command")] = "npm ci",
        env: Annotated[list[str] | None, Doc("Environment variables (KEY=VALUE format)")] = None,
    ) -> str:
        """Run a Node.js or TypeScript script with Firebase credentials.

        The script can use firebase-admin, @google-cloud/firestore, or any GCP SDK.
        Supports either service account credentials (JSON) or access tokens.

        Example with credentials:
            dag.gcp_firebase().scripts().node(
                credentials=credentials,
                source=source,
                script="src/seed-data.ts",
                working_dir="functions",
            )

        Example with access token (for CI/CD):
            dag.gcp_firebase().scripts().node(
                access_token=token,
                project_id="my-project",
                source=source,
                script="src/seed-data.ts",
            )
        """
        # Determine the runner based on file extension
        # tsx handles ESM TypeScript automatically without extra configuration
        if script.endswith(".ts"):
            run_cmd = ["npx", "tsx", script]
        else:
            run_cmd = ["node", script]

        container = (
            dag.container()
            .from_(f"node:{node_version}-alpine")
            .with_directory("/app", source)
            .with_workdir(f"/app/{working_dir}" if working_dir != "." else "/app")
            .with_exec(["sh", "-c", install_command])
        )
        container = _with_gcp_credentials(container, credentials, access_token, project_id)

        # Add custom environment variables
        if env:
            for env_var in env:
                key, _, value = env_var.partition("=")
                container = container.with_env_variable(key, value)

        return await container.with_exec(run_cmd).stdout()

    @function
    async def python(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory containing the script")],
        script: Annotated[str, Doc("Script path relative to working_dir (e.g., 'seed_data.py')")],
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials (JSON)")] = None,
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token (for CI/CD with OIDC)")] = None,
        project_id: Annotated[str | None, Doc("GCP project ID (required with access_token)")] = None,
        working_dir: Annotated[str, Doc("Working directory relative to source root")] = ".",
        python_version: Annotated[str, Doc("Python version")] = "3.12",
        install_command: Annotated[str | None, Doc("Package install command (e.g., 'pip install -r requirements.txt')")] = None,
        env: Annotated[list[str] | None, Doc("Environment variables (KEY=VALUE format)")] = None,
    ) -> str:
        """Run a Python script with Firebase credentials.

        The script can use firebase-admin, google-cloud-firestore, or any GCP SDK.
        Supports either service account credentials (JSON) or access tokens.

        Example with credentials:
            dag.gcp_firebase().scripts().python(
                credentials=credentials,
                source=source,
                script="seed_data.py",
                working_dir="scripts",
                install_command="pip install -r requirements.txt",
            )

        Example with access token (for CI/CD):
            dag.gcp_firebase().scripts().python(
                access_token=token,
                project_id="my-project",
                source=source,
                script="seed_data.py",
            )
        """
        container = (
            dag.container()
            .from_(f"python:{python_version}-alpine")
            .with_directory("/app", source)
            .with_workdir(f"/app/{working_dir}" if working_dir != "." else "/app")
        )

        if install_command:
            container = container.with_exec(["sh", "-c", install_command])

        container = _with_gcp_credentials(container, credentials, access_token, project_id)

        # Add custom environment variables
        if env:
            for env_var in env:
                key, _, value = env_var.partition("=")
                container = container.with_env_variable(key, value)

        return await container.with_exec(["python", script]).stdout()

    @function
    def container(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        base_image: Annotated[str, Doc("Base container image (e.g., 'golang:1.22-alpine', 'ruby:3.3-alpine')")],
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials (JSON)")] = None,
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token (for CI/CD with OIDC)")] = None,
        project_id: Annotated[str | None, Doc("GCP project ID (required with access_token)")] = None,
        working_dir: Annotated[str, Doc("Working directory relative to source root")] = ".",
    ) -> dagger.Container:
        """Get a container with Firebase credentials configured for any language.

        Returns a container with:
        - GCP credentials or access token configured
        - Source directory mounted at /app
        - Working directory set

        When using credentials:
        - Credentials mounted at /tmp/gcp-credentials.json
        - GOOGLE_APPLICATION_CREDENTIALS environment variable set

        When using access_token:
        - GOOGLE_ACCESS_TOKEN environment variable set
        - GOOGLE_CLOUD_PROJECT environment variable set (if project_id provided)

        Use this for languages not covered by node() or python(), such as:
        - Go: google.golang.org/api/option
        - Java: com.google.auth.oauth2.GoogleCredentials
        - Ruby: google-cloud-firestore gem
        - C#: Google.Cloud.Firestore

        Example (Go):
            container = dag.gcp_firebase().scripts().container(
                credentials=credentials,
                source=source,
                base_image="golang:1.22-alpine",
            )
            result = await container.with_exec(["go", "run", "main.go"]).stdout()

        Example (Ruby):
            container = dag.gcp_firebase().scripts().container(
                credentials=credentials,
                source=source,
                base_image="ruby:3.3-alpine",
            )
            result = await (
                container
                .with_exec(["bundle", "install"])
                .with_exec(["ruby", "seed_data.rb"])
                .stdout()
            )
        """
        container = (
            dag.container()
            .from_(base_image)
            .with_directory("/app", source)
            .with_workdir(f"/app/{working_dir}" if working_dir != "." else "/app")
        )
        return _with_gcp_credentials(container, credentials, access_token, project_id)
