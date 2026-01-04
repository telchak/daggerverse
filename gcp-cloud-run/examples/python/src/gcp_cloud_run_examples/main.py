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
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        image: Annotated[str, Doc("Container image URI")],
        service_name: Annotated[str, Doc("Service name")],
    ) -> str:
        """Example: Deploy a service to Cloud Run with scale-to-zero."""
        cr = dag.gcp_cloud_run()

        await cr.deploy_service(
            gcloud=gcloud,
            image=image,
            service_name=service_name,
            min_instances=0,
            max_instances=10,
            allow_unauthenticated=False,
        )

        url = await cr.get_service_url(
            gcloud=gcloud,
            service_name=service_name,
        )

        return f"Deployed {service_name} at {url}"

    @function
    async def deploy_and_run_job(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        image: Annotated[str, Doc("Container image URI")],
        job_name: Annotated[str, Doc("Job name")],
    ) -> str:
        """Example: Deploy and execute a Cloud Run job."""
        cr = dag.gcp_cloud_run()

        await cr.deploy_job(
            gcloud=gcloud,
            image=image,
            job_name=job_name,
            tasks=1,
            timeout="600s",
        )

        result = await cr.execute_job(
            gcloud=gcloud,
            job_name=job_name,
            wait=True,
        )

        return f"Job {job_name} completed: {result}"
