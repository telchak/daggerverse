"""GCP Firebase Hosting Module - Deploy Angular/web apps to Firebase Hosting."""

import re
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

from .firestore import Firestore
from .scripts import FirebaseScripts


def _with_firebase_credentials(
    container: dagger.Container,
    # OIDC/WIF auth (recommended) - uses gcp-auth module
    oidc_token: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account_email: str | None = None,
    # Service account JSON auth - uses gcp-auth module
    credentials: dagger.Secret | None = None,
    # Legacy access token auth (deprecated)
    access_token: dagger.Secret | None = None,
) -> dagger.Container:
    """Configure Firebase CLI authentication using gcp-auth module."""
    # Priority 1: OIDC/WIF authentication (via gcp-auth)
    if oidc_token and workload_identity_provider:
        return dag.gcp_auth().with_oidc_token(
            container=container,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
        )

    # Priority 2: Service account credentials (via gcp-auth)
    if credentials:
        return dag.gcp_auth().with_credentials(container=container, credentials=credentials)

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
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
    ) -> dagger.Directory:
        """Build the web application and return the dist directory."""
        return (
            dag.container()
            .from_(f"node:{node_version}-alpine")
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["npm", "ci"])
            .with_exec(["sh", "-c", build_command])
            .directory("/app/dist")
        )

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
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
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
            .with_exec(["npm", "ci"])
            .with_exec(["sh", "-c", build_command])
        )
        if deploy_functions:
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
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        expires: Annotated[str, Doc("Channel expiration")] = "7d",
    ) -> str:
        """Deploy to a Firebase Hosting preview channel. Returns the preview URL.

        Supports three authentication methods:
        1. OIDC/WIF (recommended): Provide oidc_token + workload_identity_provider
        2. Service account: Provide credentials (JSON key)
        3. Access token (deprecated): Provide access_token
        """
        output = await (
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
            .with_exec(["npm", "ci"])
            .with_exec(["sh", "-c", build_command])
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

    # ========== GitHub Actions Convenience Methods ==========

    @function
    async def deploy_from_github_actions(
        self,
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        deploy_functions: Annotated[bool, Doc("Deploy Cloud Functions")] = True,
        force: Annotated[bool, Doc("Force deployment")] = True,
    ) -> str:
        """Deploy to Firebase Hosting using GitHub Actions OIDC.

        Convenience wrapper that fetches the OIDC token from GitHub Actions
        and uses Workload Identity Federation for authentication.

        Example:
            dag.gcp_firebase().deploy_from_github_actions(
                workload_identity_provider="projects/.../providers/github",
                project_id="my-project",
                oidc_request_token=env.ACTIONS_ID_TOKEN_REQUEST_TOKEN,
                oidc_request_url=env.ACTIONS_ID_TOKEN_REQUEST_URL,
                source=source,
            )
        """
        oidc_token = dag.gcp_auth().oidc_token_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            oidc_request_token=oidc_request_token,
            oidc_request_url=oidc_request_url,
        )
        return await self.deploy(
            project_id=project_id,
            source=source,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            build_command=build_command,
            node_version=node_version,
            deploy_functions=deploy_functions,
            force=force,
        )

    @function
    async def deploy_preview_from_github_actions(
        self,
        workload_identity_provider: Annotated[str, Doc("GCP Workload Identity Federation provider")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID (e.g., pr-123)")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        expires: Annotated[str, Doc("Channel expiration")] = "7d",
    ) -> str:
        """Deploy to Firebase preview channel using GitHub Actions OIDC.

        Convenience wrapper that fetches the OIDC token from GitHub Actions
        and uses Workload Identity Federation for authentication.
        """
        oidc_token = dag.gcp_auth().oidc_token_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            oidc_request_token=oidc_request_token,
            oidc_request_url=oidc_request_url,
        )
        return await self.deploy_preview(
            project_id=project_id,
            channel_id=channel_id,
            source=source,
            oidc_token=oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account_email,
            build_command=build_command,
            node_version=node_version,
            expires=expires,
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
