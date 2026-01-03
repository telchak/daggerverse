"""Firestore Database Management - Create, update, and delete Firestore databases."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Firestore:
    """Firestore database management utilities.

    Manage Firestore databases using gcloud CLI commands.
    See: https://firebase.google.com/docs/firestore/manage-databases
    """

    def _gcloud_container(
        self,
        credentials: dagger.Secret,
        project_id: str,
    ) -> dagger.Container:
        """Get authenticated gcloud container via gcp-auth module."""
        return dag.gcp_auth().gcloud_container(
            credentials=credentials,
            project_id=project_id,
        )

    def _gcloud_container_from_oidc(
        self,
        workload_identity_provider: str,
        project_id: str,
        oidc_request_token: dagger.Secret,
        oidc_request_url: dagger.Secret,
        service_account_email: str | None = None,
    ) -> dagger.Container:
        """Get authenticated gcloud container via GitHub Actions OIDC."""
        return dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_request_token,
            oidc_request_url=oidc_request_url,
            service_account_email=service_account_email,
        )

    @function
    async def create(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID (lowercase letters, numbers, hyphens, 4-63 chars)")],
        location: Annotated[str, Doc("Database location (e.g., us-central1, nam5, eur3)")],
        database_type: Annotated[str, Doc("Database type: 'firestore-native' or 'datastore-mode'")] = "firestore-native",
        delete_protection: Annotated[bool, Doc("Enable delete protection")] = False,
    ) -> str:
        """Create a new Firestore database.

        Args:
            credentials: GCP service account credentials
            project_id: GCP project ID
            database_id: Database ID (use lowercase letters, numbers, hyphens; 4-63 characters starting with letter)
            location: Cloud Firestore region (e.g., us-central1) or multi-region (e.g., nam5, eur3)
            database_type: Either 'firestore-native' (default) or 'datastore-mode'
            delete_protection: Enable delete protection to prevent accidental deletion

        Returns:
            Command output confirming database creation
        """
        cmd = [
            "gcloud", "firestore", "databases", "create",
            f"--database={database_id}",
            f"--location={location}",
            f"--type={database_type}",
            "--quiet",
        ]

        if delete_protection:
            cmd.append("--delete-protection")

        return await (
            self._gcloud_container(credentials, project_id)
            .with_exec(cmd)
            .stdout()
        )

    @function
    async def delete(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to delete (use '(default)' for default database)")],
    ) -> str:
        """Delete a Firestore database.

        Note: Delete protection must be disabled before deletion.
        Use '(default)' as database_id to delete the default database.

        Args:
            credentials: GCP service account credentials
            project_id: GCP project ID
            database_id: Database ID to delete

        Returns:
            Command output confirming database deletion
        """
        return await (
            self._gcloud_container(credentials, project_id)
            .with_exec([
                "gcloud", "firestore", "databases", "delete",
                f"--database={database_id}",
                "--quiet",
            ])
            .stdout()
        )

    @function
    async def update(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to update")],
        delete_protection: Annotated[bool, Doc("Enable or disable delete protection")],
    ) -> str:
        """Update a Firestore database configuration.

        Currently supports enabling/disabling delete protection.

        Args:
            credentials: GCP service account credentials
            project_id: GCP project ID
            database_id: Database ID to update
            delete_protection: True to enable, False to disable delete protection

        Returns:
            Command output confirming database update
        """
        protection_flag = "--delete-protection" if delete_protection else "--no-delete-protection"

        return await (
            self._gcloud_container(credentials, project_id)
            .with_exec([
                "gcloud", "firestore", "databases", "update",
                f"--database={database_id}",
                protection_flag,
                "--quiet",
            ])
            .stdout()
        )

    @function
    async def describe(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to describe")],
    ) -> str:
        """Get details of a Firestore database.

        Args:
            credentials: GCP service account credentials
            project_id: GCP project ID
            database_id: Database ID to describe

        Returns:
            Database details in YAML format
        """
        return await (
            self._gcloud_container(credentials, project_id)
            .with_exec([
                "gcloud", "firestore", "databases", "describe",
                f"--database={database_id}",
            ])
            .stdout()
        )

    @function
    async def list(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """List all Firestore databases in the project.

        Args:
            credentials: GCP service account credentials
            project_id: GCP project ID

        Returns:
            List of databases in table format
        """
        return await (
            self._gcloud_container(credentials, project_id)
            .with_exec([
                "gcloud", "firestore", "databases", "list",
            ])
            .stdout()
        )

    @function
    async def exists(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials (JSON)")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to check")],
    ) -> bool:
        """Check if a Firestore database exists.

        Args:
            credentials: GCP service account credentials
            project_id: GCP project ID
            database_id: Database ID to check

        Returns:
            True if database exists, False otherwise
        """
        result = await (
            self._gcloud_container(credentials, project_id)
            .with_exec([
                "sh", "-c",
                f"gcloud firestore databases describe --database={database_id} "
                f"--format='value(name)' 2>/dev/null || echo ''",
            ])
            .stdout()
        )
        return bool(result.strip())

    # ========== OIDC versions ==========

    @function
    async def create_with_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID")],
        location: Annotated[str, Doc("Database location")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
        database_type: Annotated[str, Doc("Database type")] = "firestore-native",
        delete_protection: Annotated[bool, Doc("Enable delete protection")] = False,
    ) -> str:
        """Create a new Firestore database using GitHub Actions OIDC."""
        cmd = [
            "gcloud", "firestore", "databases", "create",
            f"--database={database_id}",
            f"--location={location}",
            f"--type={database_type}",
            "--quiet",
        ]
        if delete_protection:
            cmd.append("--delete-protection")

        return await (
            self._gcloud_container_from_oidc(
                workload_identity_provider, project_id,
                oidc_request_token, oidc_request_url, service_account_email
            )
            .with_exec(cmd)
            .stdout()
        )

    @function
    async def delete_with_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to delete")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> str:
        """Delete a Firestore database using GitHub Actions OIDC."""
        return await (
            self._gcloud_container_from_oidc(
                workload_identity_provider, project_id,
                oidc_request_token, oidc_request_url, service_account_email
            )
            .with_exec([
                "gcloud", "firestore", "databases", "delete",
                f"--database={database_id}",
                "--quiet",
            ])
            .stdout()
        )

    @function
    async def update_with_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to update")],
        delete_protection: Annotated[bool, Doc("Enable or disable delete protection")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> str:
        """Update a Firestore database using GitHub Actions OIDC."""
        protection_flag = "--delete-protection" if delete_protection else "--no-delete-protection"

        return await (
            self._gcloud_container_from_oidc(
                workload_identity_provider, project_id,
                oidc_request_token, oidc_request_url, service_account_email
            )
            .with_exec([
                "gcloud", "firestore", "databases", "update",
                f"--database={database_id}",
                protection_flag,
                "--quiet",
            ])
            .stdout()
        )

    @function
    async def describe_with_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to describe")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> str:
        """Get details of a Firestore database using GitHub Actions OIDC."""
        return await (
            self._gcloud_container_from_oidc(
                workload_identity_provider, project_id,
                oidc_request_token, oidc_request_url, service_account_email
            )
            .with_exec([
                "gcloud", "firestore", "databases", "describe",
                f"--database={database_id}",
            ])
            .stdout()
        )

    @function
    async def list_with_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> str:
        """List all Firestore databases using GitHub Actions OIDC."""
        return await (
            self._gcloud_container_from_oidc(
                workload_identity_provider, project_id,
                oidc_request_token, oidc_request_url, service_account_email
            )
            .with_exec([
                "gcloud", "firestore", "databases", "list",
            ])
            .stdout()
        )

    @function
    async def exists_with_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        project_id: Annotated[str, Doc("GCP project ID")],
        database_id: Annotated[str, Doc("Database ID to check")],
        oidc_request_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_request_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        service_account_email: Annotated[str | None, Doc("Service account to impersonate")] = None,
    ) -> bool:
        """Check if a Firestore database exists using GitHub Actions OIDC."""
        result = await (
            self._gcloud_container_from_oidc(
                workload_identity_provider, project_id,
                oidc_request_token, oidc_request_url, service_account_email
            )
            .with_exec([
                "sh", "-c",
                f"gcloud firestore databases describe --database={database_id} "
                f"--format='value(name)' 2>/dev/null || echo ''",
            ])
            .stdout()
        )
        return bool(result.strip())
