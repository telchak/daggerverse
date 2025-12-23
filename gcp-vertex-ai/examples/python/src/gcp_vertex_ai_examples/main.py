"""Examples for using the gcp-vertex-ai Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpVertexAiExamples:
    """Usage examples for gcp-vertex-ai module."""

    @function
    async def deploy_ml_model(
        self,
        image_uri: Annotated[str, Doc("Container image URI for the model")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
        model_name: Annotated[str, Doc("Model display name")],
        endpoint_name: Annotated[str, Doc("Endpoint display name")],
    ) -> str:
        """Example: Deploy a containerized ML model to Vertex AI."""
        result = await dag.gcp_vertex_ai().deploy_model(
            image_uri=image_uri,
            project_id=project_id,
            credentials=credentials,
            model_name=model_name,
            endpoint_name=endpoint_name,
            machine_type="n1-standard-4",
            accelerator_type="NVIDIA_TESLA_T4",
            accelerator_count=1,
            min_replicas=1,
            max_replicas=3,
        )

        return f"Deployed model: {result}"

    @function
    async def list_deployed_models(
        self,
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Example: List all deployed models and endpoints."""
        models = await dag.gcp_vertex_ai().list_models(
            project_id=project_id,
            credentials=credentials,
        )

        endpoints = await dag.gcp_vertex_ai().list_endpoints(
            project_id=project_id,
            credentials=credentials,
        )

        return f"Models:\n{models}\n\nEndpoints:\n{endpoints}"
