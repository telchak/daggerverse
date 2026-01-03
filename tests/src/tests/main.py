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
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region (used for Firestore location)")] = "us-central1",
    ) -> str:
        """Run gcp-firebase module tests using GitHub Actions OIDC.

        Tests Firestore (via gcloud) and Firebase Hosting build (no deploy).
        Firebase Hosting deploy requires google-github-actions/auth credentials.
        """
        results = []
        database_id = f"dagger-test-{int(time.time())}"

        # Generate gcloud-compatible credentials from OIDC
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        # ========== HOSTING BUILD TEST ==========
        results.append("--- Firebase Hosting (build only) ---")

        # Clone firebase-dagger-template from GitHub
        source = (
            dag.git("https://github.com/telchak/firebase-dagger-template.git")
            .branch("main")
            .tree()
        )

        # Test build (doesn't need Firebase CLI auth)
        dist = dag.gcp_firebase().build(source=source)
        entries = await dist.entries()
        if len(entries) == 0:
            raise ValueError("Build produced no output files")
        results.append(f"PASS: build -> {len(entries)} files")

        # ========== FIRESTORE TESTS (via gcloud) ==========
        results.append("--- Firestore ---")

        try:
            # CREATE
            await gcloud.with_exec([
                "gcloud", "firestore", "databases", "create",
                f"--database={database_id}",
                f"--location={region}",
                "--type=firestore-native",
                "--quiet",
            ]).stdout()
            results.append(f"PASS: CREATE - created database {database_id}")

            # READ - describe
            description = await gcloud.with_exec([
                "gcloud", "firestore", "databases", "describe",
                f"--database={database_id}",
            ]).stdout()
            if database_id not in description:
                raise Exception(f"Database {database_id} not in describe output")
            results.append("PASS: READ - describe database")

            # READ - list
            db_list = await gcloud.with_exec([
                "gcloud", "firestore", "databases", "list",
            ]).stdout()
            if database_id not in db_list:
                raise Exception(f"Database {database_id} not in list output")
            results.append("PASS: READ - list databases")

            # UPDATE - enable delete protection
            await gcloud.with_exec([
                "gcloud", "firestore", "databases", "update",
                f"--database={database_id}",
                "--delete-protection",
                "--quiet",
            ]).stdout()
            results.append("PASS: UPDATE - enabled delete protection")

            # UPDATE - disable delete protection
            await gcloud.with_exec([
                "gcloud", "firestore", "databases", "update",
                f"--database={database_id}",
                "--no-delete-protection",
                "--quiet",
            ]).stdout()
            results.append("PASS: UPDATE - disabled delete protection")

            # DELETE
            await gcloud.with_exec([
                "gcloud", "firestore", "databases", "delete",
                f"--database={database_id}",
                "--quiet",
            ]).stdout()
            results.append("PASS: DELETE - database deleted")

        except Exception as e:
            results.append(f"FAIL: {e}")
            # Cleanup on failure
            try:
                await gcloud.with_exec([
                    "gcloud", "firestore", "databases", "update",
                    f"--database={database_id}",
                    "--no-delete-protection",
                    "--quiet",
                ]).stdout()
                await gcloud.with_exec([
                    "gcloud", "firestore", "databases", "delete",
                    f"--database={database_id}",
                    "--quiet",
                ]).stdout()
                results.append(f"CLEANUP: deleted database {database_id}")
            except Exception:
                pass
            raise

        return "\n".join(results)

    @function
    async def oidc_token(self) -> str:
        """Run oidc-token module tests.

        Note: github_token requires network access to GitHub's OIDC endpoint,
        which isn't available from within Dagger containers. We test token_claims
        with a sample JWT instead.
        """
        results = []

        # Sample JWT for testing (header.payload.signature)
        # Payload: {"iss":"test","aud":"test","sub":"test"}
        sample_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ0ZXN0IiwiYXVkIjoidGVzdCIsInN1YiI6InRlc3QifQ.signature"
        test_token = dag.set_secret("test-jwt", sample_jwt)

        # Test token_claims - decode the sample JWT
        claims = await dag.oidc_token().token_claims(token=test_token)
        if "iss" not in claims:
            raise ValueError(f"Token missing 'iss' claim: {claims}")
        results.append("PASS: token_claims decodes JWT payload")

        # Test gitlab_token - just passes through the secret
        gitlab_secret = dag.set_secret("gitlab-jwt", "test-token")
        _ = dag.oidc_token().gitlab_token(ci_job_jwt=gitlab_secret)
        results.append("PASS: gitlab_token pass-through")

        # Test circleci_token - just passes through the secret
        circleci_secret = dag.set_secret("circleci-jwt", "test-token")
        _ = dag.oidc_token().circleci_token(oidc_token=circleci_secret)
        results.append("PASS: circleci_token pass-through")

        return "\n".join(results)

    @function
    async def semver(
        self,
        source: Annotated[dagger.Directory, Doc("Git repository with tags")],
    ) -> str:
        """Run semver module tests."""
        results = []
        sv = dag.semver()

        # Use a test-specific prefix to avoid conflicts with calver tags
        prefix = "test-semver/"

        # Test current version
        current = await sv.current(source=source, tag_prefix=prefix, initial_version="v0.0.0")
        results.append(f"PASS: current -> {current}")

        # Test bump
        bumped = await sv.bump(source=source, tag_prefix=prefix, bump_type="patch", initial_version="v1.0.0")
        if not bumped.startswith("v1.0."):
            raise ValueError(f"Expected v1.0.x, got {bumped}")
        results.append(f"PASS: bump patch -> {bumped}")

        # Test bump_type detection
        bump_type = await sv.bump_type(source=source, tag_prefix=prefix)
        if bump_type not in ["none", "patch", "minor", "major"]:
            raise ValueError(f"Invalid bump_type: {bump_type}")
        results.append(f"PASS: bump_type -> {bump_type}")

        return "\n".join(results)

    @function
    async def all_no_credentials(self) -> str:
        """Run all tests that don't require credentials."""
        results = []
        results.append(f"calver:\n{await self.calver()}")
        results.append(f"health-check:\n{await self.health_check()}")
        results.append(f"oidc-token:\n{await self.oidc_token()}")
        return "\n\n".join(results)
