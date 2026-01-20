"""Firestore Database Management - Create, update, and delete Firestore databases."""

import re
from typing import Annotated

import dagger
from dagger import Doc, function, object_type


# Validation pattern for Firestore database ID
# Must be 4-63 chars, lowercase letters, numbers, and hyphens
_DATABASE_ID_PATTERN = re.compile(r'^[a-z][a-z0-9-]{3,62}$')


def _validate_database_id(database_id: str) -> str:
    """Validate Firestore database ID format."""
    if not _DATABASE_ID_PATTERN.match(database_id):
        raise ValueError(
            f"Invalid database ID: '{database_id}'. Must be 4-63 characters, "
            "lowercase letters, numbers, and hyphens, starting with a letter."
        )
    return database_id


@object_type
class Firestore:
    """Firestore database management utilities using gcloud CLI."""

    @function
    async def create(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        database_id: Annotated[str, Doc("Database ID (4-63 chars, lowercase, hyphens)")],
        location: Annotated[str, Doc("Database location (e.g., us-central1, nam5)")],
        database_type: Annotated[str, Doc("Type: firestore-native or datastore-mode")] = "firestore-native",
        delete_protection: Annotated[bool, Doc("Enable delete protection")] = False,
    ) -> str:
        """Create a new Firestore database."""
        cmd = [
            "gcloud", "firestore", "databases", "create",
            f"--database={database_id}", f"--location={location}", f"--type={database_type}", "--quiet",
        ]
        if delete_protection:
            cmd.append("--delete-protection")
        return await gcloud.with_exec(cmd).stdout()

    @function
    async def delete(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        database_id: Annotated[str, Doc("Database ID to delete")],
    ) -> str:
        """Delete a Firestore database."""
        return await gcloud.with_exec([
            "gcloud", "firestore", "databases", "delete", f"--database={database_id}", "--quiet",
        ]).stdout()

    @function
    async def update(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        database_id: Annotated[str, Doc("Database ID to update")],
        delete_protection: Annotated[bool, Doc("Enable or disable delete protection")],
    ) -> str:
        """Update a Firestore database configuration."""
        flag = "--delete-protection" if delete_protection else "--no-delete-protection"
        return await gcloud.with_exec([
            "gcloud", "firestore", "databases", "update", f"--database={database_id}", flag, "--quiet",
        ]).stdout()

    @function
    async def describe(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        database_id: Annotated[str, Doc("Database ID to describe")],
    ) -> str:
        """Get details of a Firestore database."""
        return await gcloud.with_exec([
            "gcloud", "firestore", "databases", "describe", f"--database={database_id}",
        ]).stdout()

    @function
    async def list(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
    ) -> str:
        """List all Firestore databases in the project."""
        return await gcloud.with_exec(["gcloud", "firestore", "databases", "list"]).stdout()

    @function
    async def exists(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        database_id: Annotated[str, Doc("Database ID to check")],
    ) -> bool:
        """Check if a Firestore database exists."""
        # Validate input to prevent command injection
        _validate_database_id(database_id)

        try:
            result = await gcloud.with_exec([
                "gcloud", "firestore", "databases", "describe",
                f"--database={database_id}", "--format=value(name)",
            ]).stdout()
            return bool(result.strip())
        except dagger.ExecError:
            return False
