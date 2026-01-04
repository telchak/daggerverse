"""GCP Vertex AI Module - Operations for Google Cloud Vertex AI."""

from typing import Annotated
import time

import dagger
from dagger import Doc, function, object_type


@object_type
class GcpVertexAi:
    """Google Cloud Vertex AI utilities."""

    @function
    async def deploy_model(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        image_uri: Annotated[str, Doc("Container image URI")],
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
        gcloud = gcloud.with_exec(["gcloud", "config", "set", "ai/region", region])
        gcloud = gcloud.with_exec([
            "gcloud", "services", "enable",
            "aiplatform.googleapis.com", "compute.googleapis.com", "artifactregistry.googleapis.com",
        ])

        output = await self._upload_model(gcloud, image_uri, model_name, region)
        output += await self._setup_endpoint(gcloud, endpoint_name, region)
        output += await self._deploy_to_endpoint(
            gcloud, model_name, endpoint_name, region,
            machine_type, accelerator_type, accelerator_count, min_replicas, max_replicas,
        )
        return output

    async def _upload_model(self, gcloud: dagger.Container, image_uri: str, model_name: str, region: str) -> str:
        """Upload model to Vertex AI."""
        existing = (await gcloud.with_exec([
            "sh", "-c",
            f"gcloud ai models list --region={region} --filter='displayName:{model_name}' --format='value(name)' || echo ''"
        ]).stdout()).strip()

        cmd = [
            "gcloud", "ai", "models", "upload", f"--region={region}",
            f"--container-image-uri={image_uri}",
            "--container-health-route=/health", "--container-predict-route=/predict", "--container-ports=8080",
        ]

        if existing:
            cmd.append(f"--parent-model={existing}")
            msg = "Uploaded new version to existing model"
        else:
            cmd.append(f"--display-name={model_name}")
            msg = "Created new model"

        output = await gcloud.with_exec(cmd).stdout()
        return f"{msg}\n{output}\n"

    async def _setup_endpoint(self, gcloud: dagger.Container, endpoint_name: str, region: str) -> str:
        """Create or get endpoint."""
        existing = (await gcloud.with_exec([
            "sh", "-c",
            f"gcloud ai endpoints list --region={region} --filter='displayName:{endpoint_name}' --format='value(name)' || echo ''"
        ]).stdout()).strip()

        if existing:
            return f"Using existing endpoint: {existing}\n"

        output = await gcloud.with_exec([
            "gcloud", "ai", "endpoints", "create", f"--region={region}", f"--display-name={endpoint_name}",
        ]).stdout()
        return f"Created new endpoint\n{output}\n"

    async def _deploy_to_endpoint(
        self, gcloud: dagger.Container, model_name: str, endpoint_name: str, region: str,
        machine_type: str, accelerator_type: str, accelerator_count: int, min_replicas: int, max_replicas: int,
    ) -> str:
        """Deploy model to endpoint."""
        deployment_id = f"deployment-{int(time.time())}"
        cmd = f"""
MODEL_ID=$(gcloud ai models list --region={region} --filter='displayName:{model_name}' --format='value(name)')
ENDPOINT_ID=$(gcloud ai endpoints list --region={region} --filter='displayName:{endpoint_name}' --format='value(name)')
gcloud ai endpoints deploy-model $ENDPOINT_ID --region={region} --model=$MODEL_ID --display-name={deployment_id} \
    --machine-type={machine_type} --accelerator=type={accelerator_type},count={accelerator_count} \
    --min-replica-count={min_replicas} --max-replica-count={max_replicas} --traffic-split=0=100
"""
        output = await gcloud.with_exec(["sh", "-c", cmd]).stdout()
        return f"Deployed model to endpoint\n{output}\n"

    @function
    async def list_models(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """List all models in Vertex AI."""
        return await gcloud.with_exec(["gcloud", "ai", "models", "list", f"--region={region}"]).stdout()

    @function
    async def list_endpoints(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """List all endpoints in Vertex AI."""
        return await gcloud.with_exec(["gcloud", "ai", "endpoints", "list", f"--region={region}"]).stdout()
