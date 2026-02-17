"""GCP Vertex AI Module - Operations for Google Cloud Vertex AI."""

import re
import time
from typing import Annotated

import dagger
from dagger import Doc, function, object_type


# Validation patterns
_GCP_REGION_PATTERN = re.compile(r'^[a-z]+-[a-z]+\d+(-[a-z])?$')
_DISPLAY_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{0,127}$')
_MACHINE_TYPE_PATTERN = re.compile(r'^[a-z][a-z0-9-]+$')
_ACCELERATOR_TYPE_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]+$')

_GCLOUD_FORMAT_NAME = "--format=value(name)"


def _validate_region(region: str) -> str:
    """Validate GCP region format."""
    if not _GCP_REGION_PATTERN.match(region):
        raise ValueError(f"Invalid GCP region format: '{region}'")
    return region


def _validate_display_name(name: str, field: str = "name") -> str:
    """Validate Vertex AI display name."""
    if not _DISPLAY_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid {field}: '{name}'. Must start with a letter, "
            "contain only letters, numbers, underscores, hyphens, and be 1-128 characters."
        )
    return name


def _validate_machine_type(machine_type: str) -> str:
    """Validate machine type format."""
    if not _MACHINE_TYPE_PATTERN.match(machine_type):
        raise ValueError(f"Invalid machine type: '{machine_type}'")
    return machine_type


def _validate_accelerator_type(accelerator_type: str) -> str:
    """Validate accelerator type format."""
    if not _ACCELERATOR_TYPE_PATTERN.match(accelerator_type):
        raise ValueError(f"Invalid accelerator type: '{accelerator_type}'")
    return accelerator_type


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
        # Validate inputs to prevent command injection
        _validate_region(region)
        _validate_display_name(model_name, "model_name")
        _validate_display_name(endpoint_name, "endpoint_name")
        _validate_machine_type(machine_type)
        _validate_accelerator_type(accelerator_type)

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
        """Upload model to Vertex AI.

        Note: Inputs are validated in deploy_model() before calling this method.
        """
        # Check for existing model using array-based command
        try:
            existing = (await gcloud.with_exec([
                "gcloud", "ai", "models", "list",
                f"--region={region}",
                f"--filter=displayName:{model_name}",
                _GCLOUD_FORMAT_NAME,
            ]).stdout()).strip()
        except dagger.ExecError:
            existing = ""

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
        """Create or get endpoint.

        Note: Inputs are validated in deploy_model() before calling this method.
        """
        # Check for existing endpoint using array-based command
        try:
            existing = (await gcloud.with_exec([
                "gcloud", "ai", "endpoints", "list",
                f"--region={region}",
                f"--filter=displayName:{endpoint_name}",
                _GCLOUD_FORMAT_NAME,
            ]).stdout()).strip()
        except dagger.ExecError:
            existing = ""

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
        """Deploy model to endpoint.

        Note: Inputs are validated in deploy_model() before calling this method.
        """
        deployment_id = f"deployment-{int(time.time())}"

        # Get model ID using array-based command
        model_id = (await gcloud.with_exec([
            "gcloud", "ai", "models", "list",
            f"--region={region}",
            f"--filter=displayName:{model_name}",
            _GCLOUD_FORMAT_NAME,
        ]).stdout()).strip()

        # Get endpoint ID using array-based command
        endpoint_id = (await gcloud.with_exec([
            "gcloud", "ai", "endpoints", "list",
            f"--region={region}",
            f"--filter=displayName:{endpoint_name}",
            _GCLOUD_FORMAT_NAME,
        ]).stdout()).strip()

        # Deploy model to endpoint using array-based command
        output = await gcloud.with_exec([
            "gcloud", "ai", "endpoints", "deploy-model", endpoint_id,
            f"--region={region}",
            f"--model={model_id}",
            f"--display-name={deployment_id}",
            f"--machine-type={machine_type}",
            f"--accelerator=type={accelerator_type},count={accelerator_count}",
            f"--min-replica-count={min_replicas}",
            f"--max-replica-count={max_replicas}",
            "--traffic-split=0=100",
        ]).stdout()
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
