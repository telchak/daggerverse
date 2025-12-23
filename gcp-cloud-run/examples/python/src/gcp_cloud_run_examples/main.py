"""Examples for using the gcp-cloud-run Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class GcpCloudRunExamples:
    """Usage examples for gcp-cloud-run module."""

    @function
    async def deploy_service(
        self,
        image: Annotated[str, Doc("Container image URI")],
        service_name: Annotated[str, Doc("Service name")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Example: Deploy a service to Cloud Run with scale-to-zero."""
        result = await dag.gcp_cloud_run().deploy_service(
            image=image,
            service_name=service_name,
            credentials=credentials,
            project_id=project_id,
            min_instances=0,
            max_instances=10,
            allow_unauthenticated=False,
        )

        url = await dag.gcp_cloud_run().get_service_url(
            service_name=service_name,
            credentials=credentials,
            project_id=project_id,
        )

        return f"Deployed {service_name} at {url}"

    @function
    async def deploy_and_run_job(
        self,
        image: Annotated[str, Doc("Container image URI")],
        job_name: Annotated[str, Doc("Job name")],
        credentials: Annotated[dagger.Secret, Doc("GCP credentials")],
        project_id: Annotated[str, Doc("GCP project ID")],
    ) -> str:
        """Example: Deploy and execute a Cloud Run job."""
        await dag.gcp_cloud_run().deploy_job(
            image=image,
            job_name=job_name,
            credentials=credentials,
            project_id=project_id,
            tasks=1,
            timeout="600s",
        )

        result = await dag.gcp_cloud_run().execute_job(
            job_name=job_name,
            credentials=credentials,
            project_id=project_id,
            wait=True,
        )

        return f"Job {job_name} completed: {result}"
