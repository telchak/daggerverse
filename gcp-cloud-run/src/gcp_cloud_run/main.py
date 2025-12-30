"""Google Cloud Run deployment module for Dagger."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpCloudRun:
    """Google Cloud Run deployment utilities."""

    @function
    async def deploy_service(
        self,
        image: Annotated[str, Doc("Container image URI")],
        service_name: Annotated[str, Doc("Service name")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        port: Annotated[int, Doc("Container port")] = 8080,
        cpu: Annotated[str, Doc("CPU allocation")] = "1",
        memory: Annotated[str, Doc("Memory allocation")] = "512Mi",
        min_instances: Annotated[int, Doc("Minimum instances")] = 0,
        max_instances: Annotated[int, Doc("Maximum instances")] = 10,
        concurrency: Annotated[int, Doc("Max concurrent requests")] = 80,
        timeout: Annotated[str, Doc("Request timeout")] = "300s",
        allow_unauthenticated: Annotated[bool, Doc("Allow public access")] = False,
        env_vars: Annotated[list[str], Doc("Environment variables (KEY=VALUE)")] = [],
        secrets: Annotated[list[str], Doc("Secrets (NAME=VERSION)")] = [],
        vpc_connector: Annotated[str, Doc("VPC connector")] = "",
        service_account: Annotated[str, Doc("Service account email")] = "",
        cpu_boost: Annotated[bool, Doc("Enable CPU boost during startup")] = False,
    ) -> str:
        """Deploy a Cloud Run service."""
        gcloud = dag.gcp_auth().gcloud_container(credentials, project_id, region=region)

        cmd = [
            "gcloud", "run", "deploy", service_name,
            "--image", image,
            "--region", region,
            "--port", str(port),
            "--cpu", cpu,
            "--memory", memory,
            "--min-instances", str(min_instances),
            "--max-instances", str(max_instances),
            "--concurrency", str(concurrency),
            "--timeout", timeout,
            "--quiet",
        ]

        if allow_unauthenticated:
            cmd.append("--allow-unauthenticated")
        else:
            cmd.append("--no-allow-unauthenticated")

        if env_vars:
            cmd.extend(["--set-env-vars", ",".join(env_vars)])
        if secrets:
            cmd.extend(["--set-secrets", ",".join(secrets)])
        if vpc_connector:
            cmd.extend(["--vpc-connector", vpc_connector])
        if service_account:
            cmd.extend(["--service-account", service_account])
        if cpu_boost:
            cmd.append("--cpu-boost")

        return await gcloud.with_exec(cmd).stdout()

    @function
    async def deploy_job(
        self,
        image: Annotated[str, Doc("Container image URI")],
        job_name: Annotated[str, Doc("Job name")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        cpu: Annotated[str, Doc("CPU allocation")] = "1",
        memory: Annotated[str, Doc("Memory allocation")] = "512Mi",
        max_retries: Annotated[int, Doc("Max retry attempts")] = 0,
        timeout: Annotated[str, Doc("Task timeout")] = "600s",
        parallelism: Annotated[int, Doc("Number of parallel tasks")] = 1,
        tasks: Annotated[int, Doc("Number of tasks to execute")] = 1,
        env_vars: Annotated[list[str], Doc("Environment variables (KEY=VALUE)")] = [],
        secrets: Annotated[list[str], Doc("Secrets (NAME=VERSION)")] = [],
        vpc_connector: Annotated[str, Doc("VPC connector")] = "",
        service_account: Annotated[str, Doc("Service account email")] = "",
        command: Annotated[list[str], Doc("Override container command")] = [],
        args: Annotated[list[str], Doc("Override container args")] = [],
    ) -> str:
        """Deploy a Cloud Run job."""
        gcloud = dag.gcp_auth().gcloud_container(credentials, project_id, region=region)

        cmd = [
            "gcloud", "run", "jobs", "deploy", job_name,
            "--image", image,
            "--region", region,
            "--cpu", cpu,
            "--memory", memory,
            "--max-retries", str(max_retries),
            "--task-timeout", timeout,
            "--parallelism", str(parallelism),
            "--tasks", str(tasks),
            "--quiet",
        ]

        if env_vars:
            cmd.extend(["--set-env-vars", ",".join(env_vars)])
        if secrets:
            cmd.extend(["--set-secrets", ",".join(secrets)])
        if vpc_connector:
            cmd.extend(["--vpc-connector", vpc_connector])
        if service_account:
            cmd.extend(["--service-account", service_account])
        if command:
            cmd.extend(["--command", ",".join(command)])
        if args:
            cmd.extend(["--args", ",".join(args)])

        return await gcloud.with_exec(cmd).stdout()

    @function
    async def execute_job(
        self,
        job_name: Annotated[str, Doc("Job name")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        wait: Annotated[bool, Doc("Wait for execution to complete")] = True,
    ) -> str:
        """Execute a Cloud Run job."""
        gcloud = dag.gcp_auth().gcloud_container(credentials, project_id, region=region)
        cmd = ["gcloud", "run", "jobs", "execute", job_name, "--region", region, "--quiet"]
        if wait:
            cmd.append("--wait")
        return await gcloud.with_exec(cmd).stdout()

    @function
    async def delete_service(
        self,
        service_name: Annotated[str, Doc("Service name")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Delete a Cloud Run service."""
        gcloud = dag.gcp_auth().gcloud_container(credentials, project_id, region=region)
        return await gcloud.with_exec([
            "gcloud", "run", "services", "delete", service_name,
            "--region", region, "--quiet",
        ]).stdout()

    @function
    async def delete_job(
        self,
        job_name: Annotated[str, Doc("Job name")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Delete a Cloud Run job."""
        gcloud = dag.gcp_auth().gcloud_container(credentials, project_id, region=region)
        return await gcloud.with_exec([
            "gcloud", "run", "jobs", "delete", job_name,
            "--region", region, "--quiet",
        ]).stdout()

    @function
    async def get_service_url(
        self,
        service_name: Annotated[str, Doc("Service name")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Get the URL of a deployed service."""
        gcloud = dag.gcp_auth().gcloud_container(credentials, project_id, region=region)
        output = await gcloud.with_exec([
            "gcloud", "run", "services", "describe", service_name,
            "--region", region, "--format", "value(status.url)",
        ]).stdout()
        return output.strip()

    @function
    async def service_exists(
        self,
        service_name: Annotated[str, Doc("Service name")],
        credentials: Annotated[dagger.Secret, Doc("GCP service account credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> bool:
        """Check if a Cloud Run service exists."""
        gcloud = dag.gcp_auth().gcloud_container(credentials, project_id, region=region)
        # Use shell to handle potential errors gracefully
        result = await gcloud.with_exec([
            "sh", "-c",
            f"gcloud run services describe {service_name} --region {region} --format 'value(metadata.name)' 2>/dev/null || echo ''"
        ]).stdout()
        return bool(result.strip())

    @function
    async def test_crud(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run CRUD test: Create, Read, Update, Delete a test service."""
        import time
        results = []
        service_name = f"dagger-test-{int(time.time())}"
        test_image = "gcr.io/google-samples/hello-app:1.0"

        try:
            # CREATE
            await self.deploy_service(
                image=test_image,
                service_name=service_name,
                credentials=credentials,
                project_id=project_id,
                region=region,
                allow_unauthenticated=True,
            )
            results.append(f"PASS: CREATE - deployed {service_name}")

            # READ
            exists = await self.service_exists(service_name, credentials, project_id, region)
            if not exists:
                raise Exception(f"Service {service_name} not found after deploy")
            results.append("PASS: READ - service_exists returned True")

            url = await self.get_service_url(service_name, credentials, project_id, region)
            if not url:
                raise Exception("get_service_url returned empty")
            results.append(f"PASS: READ - get_service_url -> {url}")

            # UPDATE
            await self.deploy_service(
                image=test_image,
                service_name=service_name,
                credentials=credentials,
                project_id=project_id,
                region=region,
                allow_unauthenticated=True,
                env_vars=["TEST_VAR=updated"],
            )
            results.append("PASS: UPDATE - redeployed with env var")

            # DELETE
            await self.delete_service(service_name, credentials, project_id, region)
            results.append("PASS: DELETE - service deleted")

            # Verify deletion
            exists = await self.service_exists(service_name, credentials, project_id, region)
            if exists:
                results.append("WARN: Service still exists after delete")
            else:
                results.append("PASS: VERIFY - service no longer exists")

        except Exception as e:
            results.append(f"FAIL: {e}")
            # Cleanup on failure
            try:
                await self.delete_service(service_name, credentials, project_id, region)
                results.append(f"CLEANUP: deleted {service_name}")
            except Exception:
                pass
            raise

        return "\n".join(results)

    @function
    async def test_all(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_name: Annotated[str, Doc("Existing service name")] = "",
    ) -> str:
        """Run all tests. If no service_name provided, runs CRUD test."""
        if service_name:
            # Legacy: check existing service
            results = []
            exists = await self.service_exists(service_name, credentials, project_id)
            results.append(f"PASS: service_exists -> {exists}")
            if exists:
                url = await self.get_service_url(service_name, credentials, project_id)
                results.append(f"PASS: get_service_url -> {url}")
            return "\n".join(results)
        else:
            # Run CRUD test
            return await self.test_crud(credentials, project_id)

    @function
    async def test_crud_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run CRUD test using GitHub Actions OIDC directly."""
        import time
        results = []
        service_name = f"dagger-test-{int(time.time())}"
        test_image = "gcr.io/google-samples/hello-app:1.0"

        # Create gcloud container once using OIDC (bypasses oidc_credentials)
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
            await (
                gcloud
                .with_exec([
                    "gcloud", "run", "deploy", service_name,
                    "--image", test_image,
                    "--region", region,
                    "--port", "8080",
                    "--allow-unauthenticated",
                    "--quiet",
                ])
                .stdout()
            )
            results.append(f"PASS: CREATE - deployed {service_name}")

            # READ - check if exists
            result = await (
                gcloud
                .with_exec([
                    "gcloud", "run", "services", "describe", service_name,
                    "--region", region, "--format", "value(metadata.name)",
                ])
                .stdout()
            )
            if not result.strip():
                raise Exception(f"Service {service_name} not found after deploy")
            results.append("PASS: READ - service exists")

            # READ - get URL
            url = await (
                gcloud
                .with_exec([
                    "gcloud", "run", "services", "describe", service_name,
                    "--region", region, "--format", "value(status.url)",
                ])
                .stdout()
            )
            results.append(f"PASS: READ - get_service_url -> {url.strip()}")

            # UPDATE
            await (
                gcloud
                .with_exec([
                    "gcloud", "run", "deploy", service_name,
                    "--image", test_image,
                    "--region", region,
                    "--set-env-vars", "TEST_VAR=updated",
                    "--quiet",
                ])
                .stdout()
            )
            results.append("PASS: UPDATE - redeployed with env var")

            # DELETE
            await (
                gcloud
                .with_exec([
                    "gcloud", "run", "services", "delete", service_name,
                    "--region", region, "--quiet",
                ])
                .stdout()
            )
            results.append("PASS: DELETE - service deleted")

        except Exception as e:
            results.append(f"FAIL: {e}")
            # Cleanup on failure
            try:
                await (
                    gcloud
                    .with_exec([
                        "gcloud", "run", "services", "delete", service_name,
                        "--region", region, "--quiet",
                    ])
                    .stdout()
                )
                results.append(f"CLEANUP: deleted {service_name}")
            except Exception:
                pass
            raise

        return "\n".join(results)