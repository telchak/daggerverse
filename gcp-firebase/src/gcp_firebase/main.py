"""GCP Firebase Hosting Module - Deploy Angular/web apps to Firebase Hosting."""

import re
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

from .firestore import Firestore


@object_type
class GcpFirebase:
    """Firebase Hosting deployment utilities for Dagger pipelines.

    Uses GCP service account credentials for authentication.
    Supports both service account keys and Workload Identity Federation credentials.
    """

    async def _get_access_token(
        self,
        credentials: dagger.Secret,
        project_id: str,
    ) -> dagger.Secret:
        """Get an access token using gcloud (handles external_account credentials)."""
        gcloud = dag.gcp_auth().gcloud_container(
            credentials=credentials,
            project_id=project_id,
        )
        token_output = await (
            gcloud
            .with_exec(["gcloud", "auth", "print-access-token"])
            .stdout()
        )
        return dag.set_secret("firebase_access_token", token_output.strip())

    @function
    async def _base_container(
        self,
        credentials: dagger.Secret,
        project_id: str,
        node_version: str = "20",
    ) -> dagger.Container:
        """Create a base container with Node.js and Firebase CLI, authenticated with GCP credentials."""
        # Get access token using gcloud (supports external_account credentials)
        access_token = await self._get_access_token(credentials, project_id)

        return (
            dag.container()
            .from_(f"node:{node_version}-alpine")
            .with_exec(["apk", "add", "--no-cache", "openjdk17-jre"])
            .with_exec(["npm", "install", "-g", "firebase-tools"])
            .with_secret_variable("FIREBASE_TOKEN", access_token)
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
        base = await self._base_container(credentials, project_id, node_version)
        container = (
            base
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
        base = await self._base_container(credentials, project_id, node_version)
        output = await (
            base
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

    @function
    async def delete_channel(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID to delete")],
        site: Annotated[str | None, Doc("Firebase Hosting site (defaults to project ID)")] = None,
        node_version: Annotated[str, Doc("Node.js version")] = "20",
    ) -> str:
        """Delete a Firebase Hosting preview channel."""
        site_name = site or project_id
        # Firebase CLI requires firebase.json even for channel deletion
        minimal_firebase_json = '{"hosting": {"public": "."}}'
        base = await self._base_container(credentials, project_id, node_version)
        return await (
            base
            .with_workdir("/tmp/firebase")
            .with_new_file("/tmp/firebase/firebase.json", minimal_firebase_json)
            .with_exec([
                "firebase", "hosting:channel:delete", channel_id,
                "--site", site_name,
                "--project", project_id,
                "--non-interactive",
                "--force",
            ])
            .stdout()
        )

    @function
    def firestore(self) -> Firestore:
        """Access Firestore database management utilities.

        Returns a Firestore object with functions to create, update,
        delete, and manage Firestore databases.
        """
        return Firestore()

