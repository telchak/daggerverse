"""GCP Firebase Hosting Module - Deploy Angular/web apps to Firebase Hosting."""

import re
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

from .firestore import Firestore


@object_type
class GcpFirebase:
    """Firebase Hosting deployment utilities for Dagger pipelines."""

    def _firebase_container(
        self,
        access_token: dagger.Secret,
        node_version: str = "20",
    ) -> dagger.Container:
        """Create a container with Firebase CLI authenticated via access token."""
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
        access_token: Annotated[dagger.Secret, Doc("GCP access token for Firebase")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        deploy_functions: Annotated[bool, Doc("Deploy Cloud Functions")] = True,
        force: Annotated[bool, Doc("Force deployment")] = True,
    ) -> str:
        """Build and deploy to Firebase Hosting."""
        deploy_target = "hosting,functions" if deploy_functions else "hosting"
        container = (
            self._firebase_container(access_token, node_version)
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
        access_token: Annotated[dagger.Secret, Doc("GCP access token for Firebase")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID (e.g., pr-123)")],
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Source directory")],
        build_command: Annotated[str, Doc("Build command")] = "npm run build",
        node_version: Annotated[str, Doc("Node.js version")] = "20",
        expires: Annotated[str, Doc("Channel expiration")] = "7d",
    ) -> str:
        """Deploy to a Firebase Hosting preview channel. Returns the preview URL."""
        output = await (
            self._firebase_container(access_token, node_version)
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
        access_token: Annotated[dagger.Secret, Doc("GCP access token for Firebase")],
        project_id: Annotated[str, Doc("Firebase project ID")],
        channel_id: Annotated[str, Doc("Preview channel ID to delete")],
        site: Annotated[str | None, Doc("Firebase site (defaults to project ID)")] = None,
        node_version: Annotated[str, Doc("Node.js version")] = "20",
    ) -> str:
        """Delete a Firebase Hosting preview channel."""
        return await (
            self._firebase_container(access_token, node_version)
            .with_workdir("/tmp/firebase")
            .with_new_file("/tmp/firebase/firebase.json", '{"hosting": {"public": "."}}')
            .with_exec([
                "firebase", "hosting:channel:delete", channel_id,
                "--site", site or project_id, "--project", project_id,
                "--non-interactive", "--force",
            ])
            .stdout()
        )

    @function
    def firestore(self) -> Firestore:
        """Access Firestore database management utilities."""
        return Firestore()
