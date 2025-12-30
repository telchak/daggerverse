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
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run gcp-auth module tests using GitHub Actions OIDC."""
        return await dag.gcp_auth().test_oidc(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            region=region,
        )

    @function
    async def gcp_artifact_registry(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Artifact Registry repository name")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
    ) -> str:
        """Run gcp-artifact-registry module tests using GitHub Actions OIDC."""
        credentials = dag.gcp_auth().oidc_credentials(
            workload_identity_provider=workload_identity_provider,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
        )
        return await dag.gcp_artifact_registry().test_all(
            credentials=credentials, project_id=project_id, repository=repository
        )

    @function
    async def gcp_cloud_run(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run gcp-cloud-run module CRUD tests using GitHub Actions OIDC."""
        credentials = dag.gcp_auth().oidc_credentials(
            workload_identity_provider=workload_identity_provider,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
        )
        return await dag.gcp_cloud_run().test_crud(
            credentials=credentials, project_id=project_id, region=region
        )

    @function
    async def gcp_vertex_ai(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
    ) -> str:
        """Run gcp-vertex-ai module tests using GitHub Actions OIDC."""
        credentials = dag.gcp_auth().oidc_credentials(
            workload_identity_provider=workload_identity_provider,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
        )
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
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")] = "",
        service_account: Annotated[str, Doc("Service account email")] = "",
        project_id: Annotated[str, Doc("GCP project ID")] = "",
        artifact_registry_repository: Annotated[str, Doc("Artifact Registry repository")] = "",
        oidc_token: Annotated[dagger.Secret | None, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")] = None,
        oidc_url: Annotated[dagger.Secret | None, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")] = None,
    ) -> str:
        """Run all module tests.

        Tests requiring OIDC are skipped if OIDC params not provided.
        """
        results = []

        # Tests without credentials
        results.append(f"calver:\n{await self.calver()}")
        results.append(f"health-check:\n{await self.health_check()}")

        # Tests with OIDC
        if workload_identity_provider and service_account and project_id and oidc_token and oidc_url:
            results.append(f"gcp-auth:\n{await self.gcp_auth(workload_identity_provider, service_account, project_id, oidc_token, oidc_url)}")
            results.append(f"gcp-vertex-ai:\n{await self.gcp_vertex_ai(workload_identity_provider, service_account, project_id, oidc_token, oidc_url)}")
            results.append(f"gcp-cloud-run:\n{await self.gcp_cloud_run(workload_identity_provider, service_account, project_id, oidc_token, oidc_url)}")

            if artifact_registry_repository:
                results.append(
                    f"gcp-artifact-registry:\n{await self.gcp_artifact_registry(workload_identity_provider, service_account, project_id, artifact_registry_repository, oidc_token, oidc_url)}"
                )
        else:
            results.append("gcp-auth: SKIPPED (no OIDC params)")
            results.append("gcp-artifact-registry: SKIPPED (no OIDC params)")
            results.append("gcp-cloud-run: SKIPPED (no OIDC params)")
            results.append("gcp-vertex-ai: SKIPPED (no OIDC params)")

        return "\n\n".join(results)
