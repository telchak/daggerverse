"""Tests Module - Centralized test orchestration for all daggerverse modules."""

import time
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type

from .calver import test_calver
from .gcp_artifact_registry import test_gcp_artifact_registry
from .gcp_auth import test_gcp_auth
from .gcp_cloud_run import test_gcp_cloud_run
from .gcp_firebase import test_gcp_firebase
from .gcp_vertex_ai import test_gcp_vertex_ai
from .health_check import test_health_check
from .oidc_token import test_oidc_token
from .semver import test_semver


@object_type
class Tests:
    """Test orchestration for daggerverse modules."""

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
        return await test_gcp_auth(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
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
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run gcp-artifact-registry module tests using GitHub Actions OIDC."""
        return await test_gcp_artifact_registry(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            repository=repository,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
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
        return await test_gcp_cloud_run(
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
    ) -> str:
        """Run gcp-vertex-ai module tests using GitHub Actions OIDC."""
        return await test_gcp_vertex_ai(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
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
    ) -> str:
        """Run gcp-firebase module tests (Hosting + Firestore)."""
        return await test_gcp_firebase(
            workload_identity_provider=workload_identity_provider,
            service_account=service_account,
            project_id=project_id,
            oidc_token=oidc_token,
            oidc_url=oidc_url,
            region=region,
        )

    @function
    async def all_no_credentials(self) -> str:
        """Run all tests that don't require credentials."""
        results = []
        results.append(f"=== calver ===\n{await test_calver()}")
        results.append(f"=== health-check ===\n{await test_health_check()}")
        results.append(f"=== oidc-token ===\n{await test_oidc_token()}")
        return "\n\n".join(results)

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
    ) -> str:
        """Run all GCP tests with shared authentication."""
        results = []

        # Authenticate once, use everywhere
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        # Get access token for Firebase
        token_output = await gcloud.with_exec(["gcloud", "auth", "print-access-token"]).stdout()
        access_token = dag.set_secret("firebase_token", token_output.strip())

        # === gcp-auth ===
        results.append("=== gcp-auth ===")
        email = await gcloud.with_exec(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
        ).stdout()
        results.append(f"PASS: gcloud auth -> {email.strip()}")
        proj = await gcloud.with_exec(["gcloud", "config", "get", "project"]).stdout()
        results.append(f"PASS: gcloud project -> {proj.strip()}")

        # === gcp-artifact-registry ===
        results.append("\n=== gcp-artifact-registry ===")
        ar = dag.gcp_artifact_registry()
        uri = await ar.get_image_uri(
            project_id="test-project", repository="test-repo", image_name="test-image", tag="v1.0.0",
        )
        if uri != "us-central1-docker.pkg.dev/test-project/test-repo/test-image:v1.0.0":
            raise ValueError(f"Unexpected URI: {uri}")
        results.append(f"PASS: get_image_uri -> {uri}")
        await ar.list_images(gcloud=gcloud, project_id=project_id, repository=repository, region=region)
        results.append(f"PASS: list_images -> {repository}")

        # === gcp-vertex-ai ===
        results.append("\n=== gcp-vertex-ai ===")
        vai = dag.gcp_vertex_ai()
        await vai.list_models(gcloud=gcloud, region=region)
        results.append("PASS: list_models")
        await vai.list_endpoints(gcloud=gcloud, region=region)
        results.append("PASS: list_endpoints")

        # === gcp-cloud-run ===
        results.append("\n=== gcp-cloud-run ===")
        service_name = f"dagger-test-{int(time.time())}"
        cr = dag.gcp_cloud_run()
        try:
            await cr.deploy_service(
                gcloud=gcloud, image="gcr.io/google-samples/hello-app:1.0",
                service_name=service_name, region=region, allow_unauthenticated=True,
            )
            results.append(f"PASS: deploy_service -> {service_name}")
            exists = await cr.service_exists(gcloud=gcloud, service_name=service_name, region=region)
            if not exists:
                raise Exception(f"Service {service_name} not found")
            results.append("PASS: service_exists")
            url = await cr.get_service_url(gcloud=gcloud, service_name=service_name, region=region)
            results.append(f"PASS: get_service_url -> {url}")
            await cr.delete_service(gcloud=gcloud, service_name=service_name, region=region)
            results.append("PASS: delete_service")
        except Exception:
            try:
                await cr.delete_service(gcloud=gcloud, service_name=service_name, region=region)
            except Exception:
                pass
            raise

        # === gcp-firebase ===
        results.append("\n=== gcp-firebase ===")
        channel_id = f"dagger-test-{int(time.time())}"
        database_id = f"dagger-test-{int(time.time())}"
        source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()
        firebase = dag.gcp_firebase()

        # Hosting
        dist = firebase.build(source=source)
        entries = await dist.entries()
        results.append(f"PASS: build -> {len(entries)} files")
        try:
            preview_url = await firebase.deploy_preview(
                access_token=access_token, project_id=project_id, channel_id=channel_id, source=source,
            )
            results.append(f"PASS: deploy_preview -> {preview_url}")
            await firebase.delete_channel(access_token=access_token, project_id=project_id, channel_id=channel_id)
            results.append("PASS: delete_channel")
        except Exception:
            try:
                await firebase.delete_channel(access_token=access_token, project_id=project_id, channel_id=channel_id)
            except Exception:
                pass
            raise

        # Firestore
        firestore = firebase.firestore()
        try:
            await firestore.create(gcloud=gcloud, database_id=database_id, location=region)
            results.append(f"PASS: firestore.create -> {database_id}")
            exists = await firestore.exists(gcloud=gcloud, database_id=database_id)
            if not exists:
                raise Exception(f"Database {database_id} not found")
            results.append("PASS: firestore.exists")
            await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
            results.append("PASS: firestore.update")
            await firestore.delete(gcloud=gcloud, database_id=database_id)
            results.append("PASS: firestore.delete")
        except Exception:
            try:
                await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
                await firestore.delete(gcloud=gcloud, database_id=database_id)
            except Exception:
                pass
            raise

        return "\n".join(results)
