"""GCP Vertex AI Module - Operations for Google Cloud Vertex AI."""

from typing import Annotated
import time

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpVertexAi:
    """Google Cloud Vertex AI utilities."""

    @function
    async def deploy_model(
        self,
        image_uri: Annotated[str, Doc("Container image URI")],
        project_id: Annotated[str, Doc("GCP project ID")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        model_name: Annotated[str, Doc("Model display name")],
        endpoint_name: Annotated[str, Doc("Endpoint display name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        machine_type: Annotated[str, Doc("VM machine type")] = "n1-standard-4",
        accelerator_type: Annotated[str, Doc("GPU type")] = "NVIDIA_TESLA_T4",
        accelerator_count: Annotated[int, Doc("Number of GPUs")] = 1,
        min_replicas: Annotated[int, Doc("Minimum replicas")] = 1,
        max_replicas: Annotated[int, Doc("Maximum replicas")] = 3,
    ) -> str:
        """Deploy a containerized model to Vertex AI."""
        gcp_auth = dag.gcp_auth()
        gcloud = gcp_auth.gcloud_container(credentials, project_id, region=region)

        gcloud = gcloud.with_exec([
            "gcloud", "config", "set", "ai/region", region
        ])

        gcloud = gcloud.with_exec([
            "gcloud", "services", "enable",
            "aiplatform.googleapis.com",
            "compute.googleapis.com",
            "artifactregistry.googleapis.com",
        ])

        output = await self._upload_model(gcloud, image_uri, model_name, region)

        output += await self._setup_endpoint(gcloud, endpoint_name, region)

        output += await self._deploy_to_endpoint(
            gcloud, model_name, endpoint_name, region,
            machine_type, accelerator_type, accelerator_count,
            min_replicas, max_replicas,
        )

        return output

    async def _upload_model(self, gcloud: dagger.Container, image_uri: str, model_name: str, region: str) -> str:
        """Upload model to Vertex AI."""
        check_cmd = [
            "sh", "-c",
            f"gcloud ai models list --region={region} --filter='displayName:{model_name}' --format='value(name)' || echo ''"
        ]
        existing_model = (await gcloud.with_exec(check_cmd).stdout()).strip()

        upload_cmd = [
            "gcloud", "ai", "models", "upload",
            f"--region={region}",
            f"--container-image-uri={image_uri}",
            "--container-health-route=/health",
            "--container-predict-route=/predict",
            "--container-ports=8080",
        ]

        if existing_model:
            upload_cmd.append(f"--parent-model={existing_model}")
            msg = "Uploaded new version to existing model"
        else:
            upload_cmd.append(f"--display-name={model_name}")
            msg = "Created new model"

        output = await gcloud.with_exec(upload_cmd).stdout()
        return f"{msg}\n{output}\n"

    async def _setup_endpoint(self, gcloud: dagger.Container, endpoint_name: str, region: str) -> str:
        """Create or get endpoint."""
        check_cmd = [
            "sh", "-c",
            f"gcloud ai endpoints list --region={region} --filter='displayName:{endpoint_name}' --format='value(name)' || echo ''"
        ]
        existing_endpoint = (await gcloud.with_exec(check_cmd).stdout()).strip()

        if existing_endpoint:
            return f"Using existing endpoint: {existing_endpoint}\n"

        output = await gcloud.with_exec([
            "gcloud", "ai", "endpoints", "create",
            f"--region={region}",
            f"--display-name={endpoint_name}",
        ]).stdout()
        return f"Created new endpoint\n{output}\n"

    async def _deploy_to_endpoint(
        self,
        gcloud: dagger.Container,
        model_name: str,
        endpoint_name: str,
        region: str,
        machine_type: str,
        accelerator_type: str,
        accelerator_count: int,
        min_replicas: int,
        max_replicas: int,
    ) -> str:
        """Deploy model to endpoint."""
        deployment_id = f"deployment-{int(time.time())}"

        get_ids_cmd = f"""
MODEL_ID=$(gcloud ai models list --region={region} --filter='displayName:{model_name}' --format='value(name)')
ENDPOINT_ID=$(gcloud ai endpoints list --region={region} --filter='displayName:{endpoint_name}' --format='value(name)')

gcloud ai endpoints deploy-model $ENDPOINT_ID \\
    --region={region} \\
    --model=$MODEL_ID \\
    --display-name={deployment_id} \\
    --machine-type={machine_type} \\
    --accelerator=type={accelerator_type},count={accelerator_count} \\
    --min-replica-count={min_replicas} \\
    --max-replica-count={max_replicas} \\
    --traffic-split=0=100
"""

        output = await (
            gcloud
            .with_exec(["sh", "-c", get_ids_cmd])
            .stdout()
        )

        return f"Deployed model to endpoint\n{output}\n"

    @function
    async def list_models(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """List all models in Vertex AI."""
        gcp_auth = dag.gcp_auth()
        gcloud = gcp_auth.gcloud_container(credentials, project_id, region=region)

        output = await (
            gcloud
            .with_exec([
                "gcloud", "ai", "models", "list",
                f"--region={region}",
            ])
            .stdout()
        )

        return output

    @function
    async def list_endpoints(
        self,
        project_id: Annotated[str, Doc("GCP project ID")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """List all endpoints in Vertex AI."""
        gcp_auth = dag.gcp_auth()
        gcloud = gcp_auth.gcloud_container(credentials, project_id, region=region)

        output = await (
            gcloud
            .with_exec([
                "gcloud", "ai", "endpoints", "list",
                f"--region={region}",
            ])
            .stdout()
        )

        return output

    @function
    async def test_all(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Run all tests (requires GCP credentials)."""
        results = []
        await self.list_models(project_id, credentials)
        results.append("PASS: list_models")
        await self.list_endpoints(project_id, credentials)
        results.append("PASS: list_endpoints")
        return "\n".join(results)

    @function
    async def test_all_oidc(
        self,
        workload_identity_provider: Annotated[str, Doc("WIF provider resource name")],
        service_account: Annotated[str, Doc("Service account email")],
        project_id: Annotated[str, Doc("GCP project ID")],
        oidc_token: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_TOKEN")],
        oidc_url: Annotated[dagger.Secret, Doc("ACTIONS_ID_TOKEN_REQUEST_URL")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Run all tests using GitHub Actions OIDC directly."""
        results = []

        # Use gcloud_container_from_github_actions directly (bypasses oidc_credentials)
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )

        await (
            gcloud
            .with_exec([
                "gcloud", "ai", "models", "list",
                f"--region={region}",
            ])
            .stdout()
        )
        results.append("PASS: list_models")

        await (
            gcloud
            .with_exec([
                "gcloud", "ai", "endpoints", "list",
                f"--region={region}",
            ])
            .stdout()
        )
        results.append("PASS: list_endpoints")

        return "\n".join(results)
