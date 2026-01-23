"""Tests for gcp-cloud-run-agent module.

Tests the AI agent's ability to deploy a Cloud Run service
using OIDC authentication via GitHub Actions.
"""

import time
import uuid

import dagger
from dagger import dag


async def test_gcp_cloud_run_agent(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> str:
    """Test gcp-cloud-run-agent deploy with OIDC authentication.

    Deploys a sample container via the AI agent, verifies the service
    exists and has a valid URL, then cleans up.
    """
    results = []
    service_name = f"agent-test-{int(time.time())}"

    # Authenticate via OIDC
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
        # Deploy via agent
        assignment = (
            f"Deploy gcr.io/google-samples/hello-app:1.0 as service {service_name}, "
            "allow unauthenticated access, use scale-to-zero"
        )
        result = await dag.gcp_cloud_run_agent().deploy(
            gcloud=gcloud,
            assignment=assignment,
            project_id=project_id,
            service_name=service_name,
            region=region,
        )
        results.append(f"[OK] Agent deploy completed: {result[:100]}...")

        # Use a cache-busted gcloud container for verification.
        # The agent's internal service_exists call (before deploying) caches
        # a stale "not found" result in Dagger. Adding a unique env var
        # creates a fresh container layer that bypasses the cache.
        verify_gcloud = gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))

        # Verify service exists
        exists = await svc.exists(
            gcloud=verify_gcloud,
            service_name=service_name,
            region=region,
        )
        if not exists:
            raise Exception(f"Service {service_name} not found after agent deploy")
        results.append("[OK] Service exists after deploy")

        # Verify URL
        url = await svc.get_url(
            gcloud=verify_gcloud,
            service_name=service_name,
            region=region,
        )
        if not url.startswith("https://"):
            raise Exception(f"Invalid service URL: {url}")
        results.append(f"[OK] Service URL: {url}")

        # Cleanup
        await svc.delete(
            gcloud=verify_gcloud,
            service_name=service_name,
            region=region,
        )
        results.append("[OK] Service deleted")

    except Exception as e:
        results.append(f"[!!] Error: {e}")
        # Cleanup attempt
        try:
            cleanup_gcloud = gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))
            await svc.delete(
                gcloud=cleanup_gcloud,
                service_name=service_name,
                region=region,
            )
            results.append("[OK] Cleanup: service deleted")
        except Exception:
            pass
        raise

    return "\n".join(results)
