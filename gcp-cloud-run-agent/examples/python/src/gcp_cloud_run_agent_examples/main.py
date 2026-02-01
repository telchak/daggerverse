"""Examples for using the gcp-cloud-run-agent Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpCloudRunAgentExamples:
    """Usage examples for gcp-cloud-run-agent module."""

    @function
    async def deploy_public_service(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        project_id: Annotated[str, Doc("GCP project ID")],
        service_name: Annotated[str, Doc("Service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: Deploy a public hello-world service using the AI agent."""
        return await dag.gcp_cloud_run_agent().deploy(
            gcloud=gcloud,
            assignment="Deploy gcr.io/google-samples/hello-app:1.0 as a public service with allow unauthenticated access",
            project_id=project_id,
            service_name=service_name,
            region=region,
        )

    @function
    async def troubleshoot_service(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        service_name: Annotated[str, Doc("Service name to troubleshoot")],
        project_id: Annotated[str, Doc("GCP project ID")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Example: Troubleshoot a Cloud Run service returning errors."""
        return await dag.gcp_cloud_run_agent().troubleshoot(
            gcloud=gcloud,
            service_name=service_name,
            issue="Service is returning 503 errors and seems to be crashing on startup",
            project_id=project_id,
            region=region,
        )
