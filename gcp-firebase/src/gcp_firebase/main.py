"""GCP Firebase Hosting Module - Deploy Angular/web apps to Firebase Hosting."""

import re
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


@object_type
class GcpFirebase:
    """Firebase Hosting deployment utilities for Dagger pipelines.

    Uses GCP service account credentials for authentication (via GOOGLE_APPLICATION_CREDENTIALS).
    This works with both service account keys and Workload Identity Federation credentials
    from google-github-actions/auth.
    """

    @function
    def _base_container(
        self,
        credentials: dagger.Secret,
        node_version: str = "20",
    ) -> dagger.Container:
        """Create a base container with Node.js and Firebase CLI, authenticated with GCP credentials."""
        credentials_path = "/tmp/gcp-credentials.json"
        return (
            dag.container()
            .from_(f"node:{node_version}-alpine")
            .with_exec(["apk", "add", "--no-cache", "openjdk17-jre"])  # Required for Firebase Functions emulator/deploy
            .with_exec(["npm", "install", "-g", "firebase-tools"])
            .with_mounted_secret(credentials_path, credentials)
            .with_env_variable("GOOGLE_APPLICATION_CREDENTIALS", credentials_path)
        )

    @function
    def build(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory containing the Angular/web app")],
        build_command: Annotated[str, Doc("Build command to run")] = "npm run build",
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
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory containing firebase.json")],
        build_command: Annotated[str, Doc("Build command to run")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        deploy_functions: Annotated[bool, Doc("Deploy Cloud Functions alongside Hosting")] = True,
        force: Annotated[bool, Doc("Force deployment and auto-setup cleanup policies")] = True,
    ) -> str:
        """Build and deploy to Firebase Hosting and optionally Cloud Functions using GCP credentials."""
        deploy_target = "hosting,functions" if deploy_functions else "hosting"
        container = (
            self._base_container(credentials, node_version)
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["npm", "ci"])
            .with_exec(["sh", "-c", build_command])
        )
        # Install functions dependencies if deploying functions
        if deploy_functions:
            container = container.with_exec(["sh", "-c", "cd functions && npm ci"])
        deploy_args = [
            "firebase", "deploy",
            "--only", deploy_target,
            "--project", project_id,
            "--non-interactive",
        ]
        if force:
            deploy_args.append("--force")
        return await (
            container
            .with_exec(deploy_args)
            .stdout()
        )

    @function
    async def deploy_preview(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID (e.g., pr-123)")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory containing firebase.json")],
        build_command: Annotated[str, Doc("Build command to run")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        expires: Annotated[str, Doc("Channel expiration (e.g., 7d, 30d)")] = "7d",
    ) -> str:
        """Build and deploy to a Firebase Hosting preview channel using GCP credentials.

        Returns the preview channel URL.
        """
        output = await (
            self._base_container(credentials, node_version)
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["npm", "ci"])
            .with_exec(["sh", "-c", build_command])
            .with_exec([
                "firebase", "hosting:channel:deploy", channel_id,
                "--project", project_id,
                "--expires", expires,
                "--non-interactive",
            ])
            .stdout()
        )
        # Extract the preview URL from Firebase CLI output
        # Pattern matches: "Channel URL (site-name): https://..."
        match = re.search(r"Channel URL[^:]*:\s*(https://[^\s\[\]]+)", output)
        if match:
            return match.group(1)
        # Fallback: return any https URL containing the channel ID
        fallback_match = re.search(rf"(https://[^\s]*--{re.escape(channel_id)}[^\s]*\.web\.app)", output)
        if fallback_match:
            return fallback_match.group(1)
        # If no URL found, raise an error with the output for debugging
        msg = f"Could not extract preview URL from Firebase output:\n{output}"
        raise ValueError(msg)

