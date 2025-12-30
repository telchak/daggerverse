"""Tests Module - Centralized test orchestration for all daggerverse modules."""

import time
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class Tests:
    """Test orchestration for daggerverse modules."""

    @function
    async def calver(self) -> str:
        """Run calver module tests."""
        results = []
        calver = dag.calver()

        # Test default format
        version = await calver.generate()
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Expected 3 parts, got {len(parts)}: {version}")
        results.append(f"PASS: generate default -> {version}")

        # Test with micro
        version = await calver.generate(format="YYYY.MM.MICRO", micro=5)
        if not version.endswith(".5"):
            raise ValueError(f"Expected version to end with .5, got {version}")
        results.append(f"PASS: generate with micro -> {version}")

        # Test custom format
        version = await calver.generate(format="v.YY.0M.0D")
        if not version.startswith("v."):
            raise ValueError(f"Expected version to start with 'v.', got {version}")
        results.append(f"PASS: generate custom format -> {version}")

        return "\n".join(results)

    @function
    async def health_check(self) -> str:
        """Run health-check module tests."""
        results = []
        hc = dag.health_check()

        # Test HTTP check with nginx
        nginx = dag.container().from_("nginx:alpine")
        await hc.http(nginx, port=80, path="/")
        results.append("PASS: HTTP check with nginx")

        # Test TCP check with redis
        redis = dag.container().from_("redis:alpine")
        await hc.tcp(redis, port=6379)
        results.append("PASS: TCP check with redis")

        # Test exec check
        alpine = dag.container().from_("alpine:latest")
        await hc.exec(alpine, command=["echo", "healthy"])
        results.append("PASS: Exec check")

        return "\n".join(results)

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
        results = []

        # Get authenticated gcloud container
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        # Test auth list
        email = await gcloud.with_exec(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
        ).stdout()
        results.append(f"PASS: gcloud auth -> {email.strip()}")

        # Test project config
        proj = await gcloud.with_exec(["gcloud", "config", "get", "project"]).stdout()
        results.append(f"PASS: gcloud project -> {proj.strip()}")

        # Test projects describe
        desc = await gcloud.with_exec(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectId)"]
        ).stdout()
        results.append(f"PASS: gcloud projects describe -> {desc.strip()}")

        return "\n".join(results)

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
        results = []

        # Test get_image_uri (no credentials needed)
        ar = dag.gcp_artifact_registry()
        uri = await ar.get_image_uri(
            project_id="test-project",
            repository="test-repo",
            image_name="test-image",
            tag="v1.0.0",
        )
        expected = "us-central1-docker.pkg.dev/test-project/test-repo/test-image:v1.0.0"
        if uri != expected:
            raise ValueError(f"Expected {expected}, got {uri}")
        results.append(f"PASS: get_image_uri -> {uri}")

        # Test list_images with OIDC
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        await gcloud.with_exec([
            "gcloud", "artifacts", "docker", "images", "list",
            f"{region}-docker.pkg.dev/{project_id}/{repository}",
            "--format=table(IMAGE,TAGS,CREATE_TIME)",
        ]).stdout()
        results.append(f"PASS: list_images -> {repository}")

        return "\n".join(results)

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
        results = []
        service_name = f"dagger-test-{int(time.time())}"
        test_image = "gcr.io/google-samples/hello-app:1.0"

        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        try:
            # CREATE
            await gcloud.with_exec([
                "gcloud", "run", "deploy", service_name, "--image", test_image,
                "--region", region, "--port", "8080", "--allow-unauthenticated", "--quiet",
            ]).stdout()
            results.append(f"PASS: CREATE - deployed {service_name}")

            # READ - check exists
            result = await gcloud.with_exec([
                "gcloud", "run", "services", "describe", service_name,
                "--region", region, "--format", "value(metadata.name)",
            ]).stdout()
            if not result.strip():
                raise Exception(f"Service {service_name} not found after deploy")
            results.append("PASS: READ - service exists")

            # READ - get URL
            url = await gcloud.with_exec([
                "gcloud", "run", "services", "describe", service_name,
                "--region", region, "--format", "value(status.url)",
            ]).stdout()
            results.append(f"PASS: READ - get_service_url -> {url.strip()}")

            # UPDATE
            await gcloud.with_exec([
                "gcloud", "run", "deploy", service_name, "--image", test_image,
                "--region", region, "--set-env-vars", "TEST_VAR=updated", "--quiet",
            ]).stdout()
            results.append("PASS: UPDATE - redeployed with env var")

            # DELETE
            await gcloud.with_exec([
                "gcloud", "run", "services", "delete", service_name, "--region", region, "--quiet",
            ]).stdout()
            results.append("PASS: DELETE - service deleted")

        except Exception as e:
            results.append(f"FAIL: {e}")
            try:
                await gcloud.with_exec([
                    "gcloud", "run", "services", "delete", service_name, "--region", region, "--quiet",
                ]).stdout()
                results.append(f"CLEANUP: deleted {service_name}")
            except Exception:
                pass
            raise

        return "\n".join(results)

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
        results = []

        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        # Test list models
        await gcloud.with_exec([
            "gcloud", "ai", "models", "list", f"--region={region}",
        ]).stdout()
        results.append("PASS: list_models")

        # Test list endpoints
        await gcloud.with_exec([
            "gcloud", "ai", "endpoints", "list", f"--region={region}",
        ]).stdout()
        results.append("PASS: list_endpoints")

        return "\n".join(results)

    @function
    async def gcp_firebase(
        self,
        source: Annotated[dagger.Directory, Doc("Test app source directory")],
    ) -> str:
        """Run gcp-firebase module tests."""
        results = []

        # Test build (no credentials needed)
        dist = dag.gcp_firebase().build(source=source)
        entries = await dist.entries()
        if len(entries) == 0:
            raise ValueError("Build produced no output files")
        results.append(f"PASS: build -> {len(entries)} files")

        return "\n".join(results)

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
        region: Annotated[str, Doc("GCP region")] = "us-central1",
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
            results.append(f"gcp-auth:\n{await self.gcp_auth(workload_identity_provider, service_account, project_id, oidc_token, oidc_url, region)}")
            results.append(f"gcp-vertex-ai:\n{await self.gcp_vertex_ai(workload_identity_provider, service_account, project_id, oidc_token, oidc_url, region)}")
            results.append(f"gcp-cloud-run:\n{await self.gcp_cloud_run(workload_identity_provider, service_account, project_id, oidc_token, oidc_url, region)}")

            if artifact_registry_repository:
                results.append(
                    f"gcp-artifact-registry:\n{await self.gcp_artifact_registry(workload_identity_provider, service_account, project_id, artifact_registry_repository, oidc_token, oidc_url, region)}"
                )
        else:
            results.append("gcp-auth: SKIPPED (no OIDC params)")
            results.append("gcp-artifact-registry: SKIPPED (no OIDC params)")
            results.append("gcp-cloud-run: SKIPPED (no OIDC params)")
            results.append("gcp-vertex-ai: SKIPPED (no OIDC params)")

        return "\n\n".join(results)
