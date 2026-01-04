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
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        image_uri: Annotated[str, Doc("Container image URI for the model")],
        model_name: Annotated[str, Doc("Model display name")],
        endpoint_name: Annotated[str, Doc("Endpoint display name")],
    ) -> str:
        """Example: Deploy a containerized ML model to Vertex AI."""
        result = await dag.gcp_vertex_ai().deploy_model(
            gcloud=gcloud,
            image_uri=image_uri,
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
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
    ) -> str:
        """Example: List all deployed models and endpoints."""
        vai = dag.gcp_vertex_ai()

        models = await vai.list_models(gcloud=gcloud)
        endpoints = await vai.list_endpoints(gcloud=gcloud)

        return f"Models:\n{models}\n\nEndpoints:\n{endpoints}"
