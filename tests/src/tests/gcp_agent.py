"""Tests for goose (GCP agent) module.

Tests the AI agent's ability to deploy, troubleshoot, assist, review,
and upgrade services using unified OIDC authentication:
- Cloud Run deployment and verification
- Firebase Hosting preview deployment via OIDC/WIF
- Troubleshooting diagnostics
- Operations assistant
- Config review
- Service upgrade
"""

import time
import uuid

import dagger
from dagger import dag


def _gcp_auth_setup(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str,
) -> tuple[dagger.Secret, dagger.Container]:
    """Common GCP auth setup for tests. Returns (agent_oidc_token, verify_gcloud)."""
    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    agent_oidc_token = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=audience,
    )
    verify_gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )
    return agent_oidc_token, verify_gcloud


async def test_goose_deploy(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    developer_knowledge_api_key: dagger.Secret | None = None,
) -> str:
    """Test goose deploy with unified OIDC authentication.

    Passes raw OIDC credentials — the agent builds gcloud internally.
    Deploys a sample container via the AI agent, verifies the service
    exists and has a valid URL, then cleans up.
    """
    results = []
    service_name = f"goose-test-{int(time.time())}"

    agent_oidc_token, verify_gcloud = _gcp_auth_setup(
        workload_identity_provider, service_account, project_id,
        oidc_token, oidc_url, region,
    )

    svc = dag.gcp_cloud_run().service()

    try:
        assignment = (
            f"Deploy gcr.io/google-samples/hello-app:1.0 as service {service_name}, "
            "allow unauthenticated access, use scale-to-zero"
        )
        result = await dag.goose(
            oidc_token=agent_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
            project_id=project_id,
            region=region,
            developer_knowledge_api_key=developer_knowledge_api_key,
        ).deploy(
            assignment=assignment,
            service_name=service_name,
        )
        results.append(f"[OK] Agent deploy completed: {result[:100]}...")

        cache_busted = verify_gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))

        exists = await svc.exists(
            gcloud=cache_busted,
            service_name=service_name,
            region=region,
        )
        if not exists:
            raise RuntimeError(f"Service {service_name} not found after agent deploy")
        results.append("[OK] Service exists after deploy")

        url = await svc.get_url(
            gcloud=cache_busted,
            service_name=service_name,
            region=region,
        )
        if not url.startswith("https://"):
            raise RuntimeError(f"Invalid service URL: {url}")
        results.append(f"[OK] Service URL: {url}")

        await svc.delete(
            gcloud=cache_busted,
            service_name=service_name,
            region=region,
        )
        results.append("[OK] Service deleted")

    except Exception as e:
        results.append(f"[!!] Error: {e}")
        try:
            cleanup_gcloud = verify_gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))
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


async def test_goose_deploy_firebase(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> str:
    """Test goose Firebase deploy with unified OIDC authentication."""
    results = []
    channel_id = f"goose-fb-{int(time.time())}"
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()

    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    agent_oidc_token = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=audience,
    )

    try:
        assignment = (
            f"Deploy to Firebase Hosting preview channel '{channel_id}'. "
            "Use the provided source directory. Do NOT run a build command — "
            "the source is pre-built with an index.html."
        )
        result = await dag.goose(
            oidc_token=agent_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
            project_id=project_id,
            region=region,
        ).deploy(
            assignment=assignment,
            service_name=channel_id,
            source=source,
        )
        results.append(f"[OK] Agent Firebase deploy completed: {result[:100]}...")

        if "https://" in result:
            results.append("[OK] Agent result contains preview URL")
        else:
            results.append("[WARN] Agent result may not contain preview URL")

    except Exception as e:
        results.append(f"[!!] Error: {e}")
        raise

    finally:
        try:
            await dag.gcp_firebase().delete_channel(
                project_id=project_id,
                channel_id=channel_id,
                oidc_token=agent_oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account,
            )
            results.append(f"[OK] Cleanup: channel {channel_id} deleted")
        except Exception:
            results.append(f"[WARN] Cleanup: could not delete channel {channel_id}")

    return "\n".join(results)


async def test_goose_troubleshoot(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    developer_knowledge_api_key: dagger.Secret | None = None,
) -> str:
    """Test goose troubleshoot with unified OIDC authentication."""
    results = []
    service_name = f"goose-diag-{int(time.time())}"

    agent_oidc_token, gcloud = _gcp_auth_setup(
        workload_identity_provider, service_account, project_id,
        oidc_token, oidc_url, region,
    )

    svc = dag.gcp_cloud_run().service()

    try:
        await svc.deploy(
            gcloud=gcloud,
            image="gcr.io/google-samples/hello-app:1.0",
            service_name=service_name,
            region=region,
            allow_unauthenticated=True,
        )
        results.append(f"[OK] Deployed {service_name} for troubleshooting test")

        diagnosis = await dag.goose(
            oidc_token=agent_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
            project_id=project_id,
            region=region,
            developer_knowledge_api_key=developer_knowledge_api_key,
        ).troubleshoot(
            service_name=service_name,
            issue="Check if the service is running correctly and report its status",
        )

        if service_name in diagnosis:
            results.append(f"[OK] Diagnosis references service: {diagnosis[:100]}...")
        else:
            results.append(f"[WARN] Diagnosis may not reference service name: {diagnosis[:100]}...")

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


async def test_goose_assist(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    developer_knowledge_api_key: dagger.Secret | None = None,
) -> str:
    """Test goose assist — ask the agent to list Cloud Run services."""
    agent_oidc_token, _ = _gcp_auth_setup(
        workload_identity_provider, service_account, project_id,
        oidc_token, oidc_url, region,
    )

    result = await dag.goose(
        oidc_token=agent_oidc_token,
        workload_identity_provider=workload_identity_provider,
        service_account_email=service_account,
        project_id=project_id,
        region=region,
        developer_knowledge_api_key=developer_knowledge_api_key,
    ).assist(
        assignment="List all Cloud Run services in the project and report their status",
    )

    if result and len(result) > 10:
        return f"[OK] Assist returned response: {result[:100]}..."
    return f"[WARN] Assist returned short response: {result}"


async def test_goose_review(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    developer_knowledge_api_key: dagger.Secret | None = None,
) -> str:
    """Test goose review — review a sample project's deployment configs."""
    agent_oidc_token, _ = _gcp_auth_setup(
        workload_identity_provider, service_account, project_id,
        oidc_token, oidc_url, region,
    )

    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()

    result = await dag.goose(
        oidc_token=agent_oidc_token,
        workload_identity_provider=workload_identity_provider,
        service_account_email=service_account,
        project_id=project_id,
        region=region,
        developer_knowledge_api_key=developer_knowledge_api_key,
    ).review(
        source=source,
        focus="firebase configuration",
    )

    if result and len(result) > 10:
        return f"[OK] Review returned response: {result[:100]}..."
    return f"[WARN] Review returned short response: {result}"


async def test_goose_upgrade(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    developer_knowledge_api_key: dagger.Secret | None = None,
) -> str:
    """Test goose upgrade (dry run) — analyze an upgrade without applying."""
    service_name = f"goose-upg-{int(time.time())}"

    agent_oidc_token, gcloud = _gcp_auth_setup(
        workload_identity_provider, service_account, project_id,
        oidc_token, oidc_url, region,
    )

    svc = dag.gcp_cloud_run().service()

    try:
        await svc.deploy(
            gcloud=gcloud,
            image="gcr.io/google-samples/hello-app:1.0",
            service_name=service_name,
            region=region,
            allow_unauthenticated=True,
        )

        result = await dag.goose(
            oidc_token=agent_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
            project_id=project_id,
            region=region,
            developer_knowledge_api_key=developer_knowledge_api_key,
        ).upgrade(
            service_name=service_name,
            target_version="gcr.io/google-samples/hello-app:2.0",
            dry_run=True,
        )

        cleanup_gcloud = gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))
        await svc.delete(
            gcloud=cleanup_gcloud,
            service_name=service_name,
            region=region,
        )

        if result and len(result) > 10:
            return f"[OK] Upgrade dry-run returned response: {result[:100]}..."
        return f"[WARN] Upgrade dry-run returned short response: {result}"

    except Exception:
        try:
            cleanup_gcloud = gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))
            await svc.delete(
                gcloud=cleanup_gcloud,
                service_name=service_name,
                region=region,
            )
        except Exception:
            pass
        raise
