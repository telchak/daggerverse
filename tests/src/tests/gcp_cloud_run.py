"""Tests for gcp-cloud-run module."""

import time

import dagger
from dagger import dag


async def test_gcp_cloud_run(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
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

    svc = dag.gcp_cloud_run().service()

    try:
        # CREATE
        await svc.deploy(
            gcloud=gcloud, image=test_image, service_name=service_name,
            region=region, allow_unauthenticated=True,
        )
        results.append(f"PASS: CREATE - deployed {service_name}")

        # READ - check exists
        exists = await svc.exists(gcloud=gcloud, service_name=service_name, region=region)
        if not exists:
            raise Exception(f"Service {service_name} not found after deploy")
        results.append("PASS: READ - service exists")

        # READ - get URL
        url = await svc.get_url(gcloud=gcloud, service_name=service_name, region=region)
        results.append(f"PASS: READ - get_url -> {url}")

        # UPDATE
        await svc.deploy(
            gcloud=gcloud, image=test_image, service_name=service_name,
            region=region, env_vars=["TEST_VAR=updated"],
        )
        results.append("PASS: UPDATE - redeployed with env var")

        # READ - get logs
        logs = await svc.get_logs(gcloud=gcloud, service_name=service_name, region=region, limit=10)
        results.append(f"PASS: READ - get_logs returned {len(logs)} chars")

        # DELETE
        await svc.delete(gcloud=gcloud, service_name=service_name, region=region)
        results.append("PASS: DELETE - service deleted")

    except Exception as e:
        results.append(f"FAIL: {e}")
        try:
            await svc.delete(gcloud=gcloud, service_name=service_name, region=region)
            results.append(f"CLEANUP: deleted {service_name}")
        except Exception:
            pass
        raise

    return "\n".join(results)
