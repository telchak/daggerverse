"""GCP Firebase Hosting Module - Deploy Angular/web apps to Firebase Hosting."""

import re
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

from .credentials import with_oidc_token, with_service_account_credentials
from .firestore import Firestore
from .scripts import FirebaseScripts


def _with_firebase_credentials(
    container: dagger.Container,
    # OIDC/WIF auth (recommended)
    oidc_token: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account_email: str | None = None,
    # Service account JSON auth
    credentials: dagger.Secret | None = None,
    # Legacy access token auth (deprecated)
    access_token: dagger.Secret | None = None,
) -> dagger.Container:
    """Configure Firebase CLI authentication.

    Supports three authentication methods:
    1. OIDC/WIF (recommended): Provide oidc_token + workload_identity_provider
    2. Service account: Provide credentials (JSON key)
    3. Access token (deprecated): Provide access_token
    """
    # Priority 1: OIDC/WIF authentication
    if oidc_token and workload_identity_provider:
        return with_oidc_token(
            container=container,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
        )

    # Priority 2: Service account credentials
    if credentials:
        return with_service_account_credentials(container=container, credentials=credentials)

    # Priority 3: Access token (deprecated, kept for backward compatibility)
    if access_token:
        return container.with_secret_variable("FIREBASE_TOKEN", access_token)

    raise ValueError(
        "Must provide one of: (oidc_token + workload_identity_provider), credentials, or access_token"
    )


@object_type
class GcpFirebase:
    """Firebase Hosting deployment utilities for Dagger pipelines."""

    def _firebase_container(
        self,
        node_version: str = "20",
        # OIDC/WIF auth (recommended)
        oidc_token: dagger.Secret | None = None,
        workload_identity_provider: str | None = None,
        service_account_email: str | None = None,
        # Service account JSON auth
        credentials: dagger.Secret | None = None,
        # Legacy access token auth (deprecated)
        access_token: dagger.Secret | None = None,
    ) -> dagger.Container:
        """Create a container with Firebase CLI and authentication configured.

        Supports three authentication methods:
        1. OIDC/WIF: oidc_token + workload_identity_provider (recommended)
        2. Service account: credentials JSON
        3. Access token: FIREBASE_TOKEN (deprecated)
        """
        container = (
            dag.container()
            .from_(f"node:{node_version}-alpine")
            .with_exec(["apk", "add", "--no-cache", "openjdk17-jre"])
            .with_exec(["npm", "install", "-g", "firebase-tools"])
        )
        return _with_firebase_credentials(
            container,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            credentials=credentials,
            access_token=access_token,
        )

    @function
    def build(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        build_command: Annotated[str, Doc("Build command (empty string to skip build)")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
    ) -> dagger.Directory:
        """Build the web application and return the dist directory."""
        container = (
            dag.container()
            .from_(f"node:{node_version}-alpine")
            .with_directory("/app", source)
            .with_workdir("/app")
        )
        if build_command.strip():
            container = container.with_exec(["npm", "ci"]).with_exec(["sh", "-c", build_command])
        return container.directory("/app/dist")

    @function
    async def deploy(
        self,
        project_id: Annotated[str, Doc("Firebase project ID")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        # OIDC/WIF auth (recommended)
        oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token from CI provider")] = None,
        workload_identity_provider: Annotated[str | None, Doc("GCP Workload Identity Federation provider")] = None,
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        # Service account JSON auth
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials JSON")] = None,
        # Legacy access token auth (deprecated)
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token (deprecated, use OIDC or credentials)")] = None,
        # Build options
        build_command: Annotated[str, Doc("Build command (empty string to skip build)")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        skip_build: Annotated[bool, Doc("Skip npm ci and build step (use when source is pre-built)")] = False,
        deploy_functions: Annotated[bool, Doc("Deploy Cloud Functions")] = True,
        force: Annotated[bool, Doc("Force deployment")] = True,
    ) -> str:
        """Build and deploy to Firebase Hosting.

        Supports three authentication methods:
        1. OIDC/WIF (recommended): Provide oidc_token + workload_identity_provider
        2. Service account: Provide credentials (JSON key)
        3. Access token (deprecated): Provide access_token
        """
        deploy_target = "hosting,functions" if deploy_functions else "hosting"
        container = (
            self._firebase_container(
                node_version=node_version,
                oidc_token=oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account_email,
                credentials=credentials,
                access_token=access_token,
            )
            .with_directory("/app", source)
            .with_workdir("/app")
        )
        if not skip_build and build_command.strip():
            container = container.with_exec(["npm", "ci"]).with_exec(["sh", "-c", build_command])
        if not skip_build and deploy_functions:
            container = container.with_exec(["sh", "-c", "cd functions && npm ci"])

        cmd = ["firebase", "deploy", "--only", deploy_target, "--project", project_id, "--non-interactive"]
        if force:
            cmd.append("--force")
        return await container.with_exec(cmd).stdout()

    @function
    async def deploy_preview(
        self,
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID (e.g., pr-123)")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        # OIDC/WIF auth (recommended)
        oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token from CI provider")] = None,
        workload_identity_provider: Annotated[str | None, Doc("GCP Workload Identity Federation provider")] = None,
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        # Service account JSON auth
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials JSON")] = None,
        # Legacy access token auth (deprecated)
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token (deprecated, use OIDC or credentials)")] = None,
        # Build options
        build_command: Annotated[str, Doc("Build command (empty string to skip build)")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        skip_build: Annotated[bool, Doc("Skip npm ci and build step (use when source is pre-built)")] = False,
        expires: Annotated[str, Doc("Channel expiration")] = "7d",
    ) -> str:
        """Deploy to a Firebase Hosting preview channel. Returns the preview URL.

        Supports three authentication methods:
        1. OIDC/WIF (recommended): Provide oidc_token + workload_identity_provider
        2. Service account: Provide credentials (JSON key)
        3. Access token (deprecated): Provide access_token
        """
        container = (
            self._firebase_container(
                node_version=node_version,
                oidc_token=oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account_email,
                credentials=credentials,
                access_token=access_token,
            )
            .with_directory("/app", source)
            .with_workdir("/app")
        )
        if not skip_build and build_command.strip():
            container = container.with_exec(["npm", "ci"]).with_exec(["sh", "-c", build_command])
        output = await (
            container
            .with_exec([
                "firebase", "hosting:channel:deploy", channel_id,
                "--project", project_id, "--expires", expires, "--non-interactive",
            ])
            .stdout()
        )
        # Extract preview URL
        match = re.search(r"Channel URL[^:]*:\s*(https://[^\s\[\]]+)", output)
        if match:
            return match.group(1)
        fallback = re.search(rf"(https://[^\s]*--{re.escape(channel_id)}[^\s]*\.web\.app)", output)
        if fallback:
            return fallback.group(1)
        raise ValueError(f"Could not extract preview URL from output:\n{output}")

    @function
    async def delete_channel(
        self,
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID to delete")],
        # OIDC/WIF auth (recommended)
        oidc_token: Annotated[dagger.Secret | None, Doc("OIDC JWT token from CI provider")] = None,
        workload_identity_provider: Annotated[str | None, Doc("GCP Workload Identity Federation provider")] = None,
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        # Service account JSON auth
        credentials: Annotated[dagger.Secret | None, Doc("GCP service account credentials JSON")] = None,
        # Legacy access token auth (deprecated)
        access_token: Annotated[dagger.Secret | None, Doc("GCP access token (deprecated, use OIDC or credentials)")] = None,
        # Options
        site: Annotated[str | None, Doc("Firebase site (defaults to project ID)")] = None,
        node_version: Annotated[str, Doc("Node.js version")] = "20",
    ) -> str:
        """Delete a Firebase Hosting preview channel.

        Supports three authentication methods:
        1. OIDC/WIF (recommended): Provide oidc_token + workload_identity_provider
        2. Service account: Provide credentials (JSON key)
        3. Access token (deprecated): Provide access_token
        """
        return await (
            self._firebase_container(
                node_version=node_version,
                oidc_token=oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account_email,
                credentials=credentials,
                access_token=access_token,
            )
            .with_workdir("/tmp/firebase")
            .with_new_file("/tmp/firebase/firebase.json", '{"hosting": {"public": "."}}')
            .with_exec([
                "firebase", "hosting:channel:delete", channel_id,
                "--site", site or project_id, "--project", project_id,
                "--non-interactive", "--force",
            ])
            .stdout()
        )

    # ========== Utility Methods ==========

    @function
    def firestore(self) -> Firestore:
        """Access Firestore database management utilities."""
        return Firestore()

    @function
    def scripts(self) -> FirebaseScripts:
        """Access script runners for Firebase/Firestore data operations.

        Provides methods to run scripts in various languages (Node.js, Python, etc.)
        with GCP Application Default Credentials configured for Firebase services.

        Example (Node.js/TypeScript):
            await dag.gcp_firebase().scripts().node(
                credentials=credentials,
                source=source,
                script="src/seed-data.ts",
                working_dir="functions",
            )

        Example (Python):
            await dag.gcp_firebase().scripts().python(
                credentials=credentials,
                source=source,
                script="seed_data.py",
                install_command="pip install firebase-admin",
            )

        Example (Other languages):
            container = dag.gcp_firebase().scripts().container(
                credentials=credentials,
                source=source,
                base_image="golang:1.22-alpine",
            )
            await container.with_exec(["go", "run", "main.go"]).stdout()
        """
        return FirebaseScripts()
