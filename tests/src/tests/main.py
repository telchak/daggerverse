"""Tests Module - Centralized test orchestration for all daggerverse modules."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Tests:
    """Test orchestration for daggerverse modules."""

    @function
    async def calver(self) -> str:
        """Run calver module tests."""
        return await dag.calver().test_all()

    @function
    async def health_check(self) -> str:
        """Run health-check module tests."""
        return await dag.health_check().test_all()

    @function
    async def gcp_auth(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Run gcp-auth module tests (requires GCP credentials)."""
        return await dag.gcp_auth().test_all(credentials=credentials, project_id=project_id)

    @function
    async def gcp_artifact_registry(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Artifact Registry repository name")],
    ) -> str:
        """Run gcp-artifact-registry module tests (requires GCP credentials)."""
        return await dag.gcp_artifact_registry().test_all(
            credentials=credentials, project_id=project_id, repository=repository
        )

    @function
    async def gcp_cloud_run(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Run gcp-cloud-run module CRUD tests (requires GCP credentials)."""
        return await dag.gcp_cloud_run().test_crud(
            credentials=credentials, project_id=project_id
        )

    @function
    async def gcp_vertex_ai(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Run gcp-vertex-ai module tests (requires GCP credentials)."""
        return await dag.gcp_vertex_ai().test_all(credentials=credentials, project_id=project_id)

    @function
    async def gcp_firebase(
        self,
        source: Annotated[dagger.Directory, Doc("Test app source directory")],
    ) -> str:
        """Run gcp-firebase module tests."""
        return await dag.gcp_firebase().test_build(source=source)

    @function
    async def all_no_credentials(self) -> str:
        """Run all tests that don't require credentials."""
        results = []
        results.append(f"calver:\n{await self.calver()}")
        results.append(f"health-check:\n{await self.health_check()}")
        return "\n\n".join(results)

    @function
    async def all(
        self,
        credentials: Annotated[dagger.Secret | None, Doc("GCP credentials (optional)")] = None,
        project_id: Annotated[str, Doc("GCP project ID")] = "",
        artifact_registry_repository: Annotated[str, Doc("Artifact Registry repository")] = "",
    ) -> str:
        """Run all module tests.

        Tests requiring credentials are skipped if credentials not provided.
        """
        results = []

        # Tests without credentials
        results.append(f"calver:\n{await self.calver()}")
        results.append(f"health-check:\n{await self.health_check()}")

        # Tests with credentials
        if credentials and project_id:
            results.append(f"gcp-auth:\n{await self.gcp_auth(credentials, project_id)}")
            results.append(f"gcp-vertex-ai:\n{await self.gcp_vertex_ai(credentials, project_id)}")
            results.append(f"gcp-cloud-run:\n{await self.gcp_cloud_run(credentials, project_id)}")

            if artifact_registry_repository:
                results.append(
                    f"gcp-artifact-registry:\n{await self.gcp_artifact_registry(credentials, project_id, artifact_registry_repository)}"
                )
        else:
            results.append("gcp-auth: SKIPPED (no credentials)")
            results.append("gcp-artifact-registry: SKIPPED (no credentials)")
            results.append("gcp-cloud-run: SKIPPED (no credentials)")
            results.append("gcp-vertex-ai: SKIPPED (no credentials)")

        return "\n\n".join(results)
