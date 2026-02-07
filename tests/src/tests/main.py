"""Tests Module - Centralized test orchestration for all daggerverse modules.

Supports multiple authentication methods for GCP modules:
- OIDC (recommended): Workload Identity Federation via GitHub Actions
- Service Account: Direct JSON key file (optional)
- Access Token (legacy): Pre-fetched bearer token
"""

import time
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type

from .calver import test_calver
from .gcp_artifact_registry import test_gcp_artifact_registry
from .gcp_auth import test_gcp_auth
from .gcp_cloud_run import test_gcp_cloud_run
from .gcp_orchestrator_agent import test_gcp_orchestrator_agent
from .gcp_firebase import test_gcp_firebase
from .gcp_vertex_ai import test_gcp_vertex_ai
from .health_check import test_health_check
from .oidc_token import test_oidc_token
from .semver import test_semver


@object_type
class Tests:
    """Test orchestration for daggerverse modules.

    GCP tests support multiple authentication methods:
    - OIDC via GitHub Actions (always tested)
    - Service Account JSON key (tested if credentials provided)
    - Access Token (legacy, tested with deprecation warning)
    """

    # ========== NON-GCP TESTS ==========

    @function
    async def calver(self) -> str:
        """Run calver module tests."""
        return await test_calver()

    @function
    async def health_check(self) -> str:
        """Run health-check module tests."""
        return await test_health_check()

    @function
    async def oidc_token(self) -> str:
        """Run oidc-token module tests."""
        return await test_oidc_token()

    @function
    async def semver(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository with tags")],
    ) -> str:
        """Run semver module tests."""
        return await test_semver(source=source)

    @function
    async def all_no_credentials(self) -> str:
        """Run all tests that don't require credentials."""
        results = []
        results.append(f"=== calver ===\n{await test_calver()}")
        results.append(f"=== health-check ===\n{await test_health_check()}")
        results.append(f"=== oidc-token ===\n{await test_oidc_token()}")
        return "\n\n".join(results)

    # ========== GCP MODULE TESTS (MULTI-AUTH) ==========

    @function
    async def gcp_auth(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (optional)")] = None,
    ) -> str:
        """Run gcp-auth module tests with all available auth methods."""
        return await test_gcp_auth(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
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
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (optional)")] = None,
    ) -> str:
        """Run gcp-artifact-registry module tests with all available auth methods."""
        return await test_gcp_artifact_registry(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            repository=repository,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
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
        credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (optional)")] = None,
    ) -> str:
        """Run gcp-cloud-run module CRUD tests with all available auth methods."""
        return await test_gcp_cloud_run(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        )

    @function
    async def gcp_orchestrator_agent(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (unused, accepted for CI compatibility)")] = None,
    ) -> str:
        """Run gcp-orchestrator-agent module tests."""
        return await test_gcp_orchestrator_agent(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
        )

    @function
    async def gcp_vertex_ai(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (optional)")] = None,
    ) -> str:
        """Run gcp-vertex-ai module tests with all available auth methods."""
        return await test_gcp_vertex_ai(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        )

    @function
    async def gcp_firebase(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region for Firestore")] = "europe-west9",
        credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (optional)")] = None,
    ) -> str:
        """Run gcp-firebase module tests with all available auth methods."""
        return await test_gcp_firebase(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        )

    # ========== COMBINED GCP TESTS ==========

    @function
    async def all_gcp(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Artifact Registry repository name")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "europe-west9",
        credentials: Annotated[dagger.Secret | None, Doc("Service account JSON key (optional)")] = None,
    ) -> str:
        """Run all GCP module tests with all available auth methods.

        Each module is tested with:
        - OIDC (always, via GitHub Actions)
        - Service Account (if credentials provided)
        - Access Token (legacy, with deprecation warning)
        """
        results = []

        # Test each module with all auth methods
        results.append("=" * 60)
        results.append("GCP-AUTH MODULE")
        results.append("=" * 60)
        results.append(await test_gcp_auth(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        ))

        results.append("\n" + "=" * 60)
        results.append("GCP-ARTIFACT-REGISTRY MODULE")
        results.append("=" * 60)
        results.append(await test_gcp_artifact_registry(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            repository=repository,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        ))

        results.append("\n" + "=" * 60)
        results.append("GCP-VERTEX-AI MODULE")
        results.append("=" * 60)
        results.append(await test_gcp_vertex_ai(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        ))

        results.append("\n" + "=" * 60)
        results.append("GCP-CLOUD-RUN MODULE")
        results.append("=" * 60)
        results.append(await test_gcp_cloud_run(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        ))

        results.append("\n" + "=" * 60)
        results.append("GCP-FIREBASE MODULE")
        results.append("=" * 60)
        results.append(await test_gcp_firebase(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
            credentials=credentials,
        ))

        return "\n".join(results)

    @function
    async def all_gcp_quick(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        repository: Annotated[str, Doc("Artifact Registry repository name")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "europe-west9",
    ) -> str:
        """Run quick GCP tests (OIDC only, minimal CRUD).

        This is a faster test that only uses OIDC authentication and
        runs minimal operations. Use all_gcp() for comprehensive testing.
        """
        results = []

        # Get OIDC token from GitHub Actions with GCP audience
        audience = f"//iam.googleapis.com/{workload_identity_provider}"
        firebase_oidc_token = dag.oidc_token().github_token(
            request_token=oidc_token,
            request_url=oidc_url,
            audience=audience,
        )

        # Get gcloud container
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        # === gcp-auth ===
        results.append("=== gcp-auth (OIDC) ===")
        email = await gcloud.with_exec(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
        ).stdout()
        results.append(f"PASS: gcloud auth -> {email.strip()}")

        # === gcp-artifact-registry ===
        results.append("\n=== gcp-artifact-registry (OIDC) ===")
        ar = dag.gcp_artifact_registry()
        uri = await ar.get_image_uri(
            project_id="test-project", repository="test-repo", image_name="test-image", tag="v1.0.0",
        )
        results.append(f"PASS: get_image_uri -> {uri}")
        await ar.list_images(gcloud=gcloud, project_id=project_id, repository=repository, region=region)
        results.append(f"PASS: list_images -> {repository}")

        # === gcp-vertex-ai ===
        results.append("\n=== gcp-vertex-ai (OIDC) ===")
        vai = dag.gcp_vertex_ai()
        await vai.list_models(gcloud=gcloud, region=region)
        results.append("PASS: list_models")
        await vai.list_endpoints(gcloud=gcloud, region=region)
        results.append("PASS: list_endpoints")

        # === gcp-cloud-run ===
        results.append("\n=== gcp-cloud-run (OIDC) ===")
        service_name = f"quick-test-{int(time.time())}"
        svc = dag.gcp_cloud_run().service()
        try:
            await svc.deploy(
                gcloud=gcloud, image="gcr.io/google-samples/hello-app:1.0",
                service_name=service_name, region=region, allow_unauthenticated=True,
            )
            results.append(f"PASS: deploy -> {service_name}")
            await svc.delete(gcloud=gcloud, service_name=service_name, region=region)
            results.append("PASS: delete")
        except Exception:
            try:
                await svc.delete(gcloud=gcloud, service_name=service_name, region=region)
            except Exception:
                pass
            raise

        # === gcp-firebase ===
        results.append("\n=== gcp-firebase (OIDC) ===")
        channel_id = f"quick-test-{int(time.time())}"
        source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()
        firebase = dag.gcp_firebase()

        dist = firebase.build(source=source)
        entries = await dist.entries()
        results.append(f"PASS: build -> {len(entries)} files")

        try:
            preview_url = await firebase.deploy_preview(
                project_id=project_id,
                channel_id=channel_id,
                source=source,
                oidc_token=firebase_oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account,
            )
            results.append(f"PASS: deploy_preview -> {preview_url}")
            await firebase.delete_channel(
                project_id=project_id,
                channel_id=channel_id,
                oidc_token=firebase_oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account,
            )
            results.append("PASS: delete_channel")
        except Exception:
            try:
                await firebase.delete_channel(
                    project_id=project_id,
                    channel_id=channel_id,
                    oidc_token=firebase_oidc_token,
                    workload_identity_provider=workload_identity_provider,
                    service_account_email=service_account,
                )
            except Exception:
                pass
            raise

        return "\n".join(results)
