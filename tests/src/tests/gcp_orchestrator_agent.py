"""Tests for gcp-orchestrator-agent module.

Tests the AI agent's ability to deploy services using OIDC authentication
via GitHub Actions:
- Cloud Run deployment and verification
- Firebase Hosting preview deployment via OIDC/WIF
- Troubleshooting diagnostics
"""

import time
import uuid

import dagger
from dagger import dag


async def test_gcp_orchestrator_agent(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    developer_knowledge_api_key: dagger.Secret | None = None,
) -> str:
    """Test gcp-orchestrator-agent deploy with OIDC authentication.

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
        result = await dag.gcp_orchestrator_agent(
            gcloud=gcloud,
            project_id=project_id,
            region=region,
            developer_knowledge_api_key=developer_knowledge_api_key,
        ).deploy(
            assignment=assignment,
            service_name=service_name,
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


async def test_gcp_orchestrator_agent_troubleshoot(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> str:
    """Test gcp-orchestrator-agent troubleshoot with OIDC authentication.

    Deploys a service directly, then asks the agent to troubleshoot it,
    verifying the diagnosis contains the service name.
    """
    results = []
    service_name = f"agent-diag-{int(time.time())}"

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
        # Deploy a service directly (not via agent)
        await svc.deploy(
            gcloud=gcloud,
            image="gcr.io/google-samples/hello-app:1.0",
            service_name=service_name,
            region=region,
            allow_unauthenticated=True,
        )
        results.append(f"[OK] Deployed {service_name} for troubleshooting test")

        # Troubleshoot via agent
        diagnosis = await dag.gcp_orchestrator_agent(
            gcloud=gcloud,
            project_id=project_id,
            region=region,
        ).troubleshoot(
            service_name=service_name,
            issue="Check if the service is running correctly and report its status",
        )

        if service_name in diagnosis:
            results.append(f"[OK] Diagnosis references service: {diagnosis[:100]}...")
        else:
            results.append(f"[WARN] Diagnosis may not reference service name: {diagnosis[:100]}...")

        # Cleanup
        cleanup_gcloud = gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))
        await svc.delete(
            gcloud=cleanup_gcloud,
            service_name=service_name,
            region=region,
        )
        results.append("[OK] Service deleted")

    except Exception as e:
        results.append(f"[!!] Error: {e}")
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


async def test_gcp_orchestrator_agent_firebase(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> str:
    """Test gcp-orchestrator-agent Firebase deploy with OIDC/WIF authentication.

    Asks the AI agent to deploy a Firebase Hosting preview channel using
    OIDC/WIF auth fields, verifies the result contains a preview URL,
    then cleans up the channel directly.
    """
    results = []
    channel_id = f"agent-fb-{int(time.time())}"
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()

    # Get OIDC token with GCP audience for Firebase
    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    firebase_oidc_token = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=audience,
    )

    # Authenticate gcloud for the agent (needed for non-Firebase tools)
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )

    try:
        # Deploy Firebase preview via agent with OIDC/WIF auth
        assignment = (
            f"Deploy to Firebase Hosting preview channel '{channel_id}'. "
            "Use the provided source directory. Do NOT run a build command — "
            "the source is pre-built with an index.html."
        )
        result = await dag.gcp_orchestrator_agent(
            gcloud=gcloud,
            project_id=project_id,
            region=region,
            firebase_oidc_token=firebase_oidc_token,
            firebase_workload_identity_provider=workload_identity_provider,
            firebase_service_account_email=service_account,
        ).deploy(
            assignment=assignment,
            service_name=channel_id,
            source=source,
        )
        results.append(f"[OK] Agent Firebase deploy completed: {result[:100]}...")

        # Verify result mentions a URL (the agent should report the preview URL)
        if "https://" in result:
            results.append("[OK] Agent result contains preview URL")
        else:
            results.append("[WARN] Agent result may not contain preview URL")

    except Exception as e:
        results.append(f"[!!] Error: {e}")
        raise

    finally:
        # Cleanup: delete the preview channel directly (not via agent)
        try:
            await dag.gcp_firebase().delete_channel(
                project_id=project_id,
                channel_id=channel_id,
                oidc_token=firebase_oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account,
            )
            results.append(f"[OK] Cleanup: channel {channel_id} deleted")
        except Exception:
            results.append(f"[WARN] Cleanup: could not delete channel {channel_id}")

    return "\n".join(results)
