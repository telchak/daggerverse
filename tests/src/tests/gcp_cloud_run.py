"""Tests for gcp-cloud-run module.

Tests all authentication methods via gcloud container:
- OIDC (recommended): Workload Identity Federation via GitHub Actions
- Service Account: Direct JSON key file
- Access Token (legacy): Pre-fetched bearer token

Each auth method tests the full CRUD cycle:
- CREATE: deploy service
- READ: exists, get_url, get_logs
- UPDATE: redeploy with env vars
- DELETE: remove service
"""

import time

import dagger
from dagger import dag

from .auth_utils import (
    AuthMethod,
    format_auth_header,
    format_component_header,
    format_operation,
    format_test_summary,
    warn_legacy_access_token,
)


async def _test_cloud_run_crud(
    gcloud: dagger.Container,
    auth_method: AuthMethod,
    region: str = "us-central1",
) -> tuple[list[str], dict[str, str]]:
    """Test Cloud Run CRUD operations with specified gcloud container.

    Returns:
        Tuple of (results list, operations dict for summary)
    """
    results = [format_component_header("Cloud Run Service")]
    ops = {}
    # Cloud Run names only allow lowercase alphanumeric and dashes
    service_name = f"test-{auth_method.value.replace('_', '-')}-{int(time.time())}"
    test_image = "gcr.io/google-samples/hello-app:1.0"

    svc = dag.gcp_cloud_run().service()

    try:
        # CREATE
        await svc.deploy(
            gcloud=gcloud,
            image=test_image,
            service_name=service_name,
            region=region,
            allow_unauthenticated=True,
        )
        results.append(format_operation("CREATE", "PASS", service_name))
        ops["CREATE"] = "PASS"

        # READ - check exists
        exists = await svc.exists(gcloud=gcloud, service_name=service_name, region=region)
        if not exists:
            raise Exception(f"Service {service_name} not found after deploy")
        results.append(format_operation("READ (exists)", "PASS"))
        ops["READ"] = "PASS"

        # READ - get URL
        url = await svc.get_url(gcloud=gcloud, service_name=service_name, region=region)
        if not url.startswith("https://"):
            raise Exception(f"Invalid URL: {url}")
        results.append(format_operation("READ (get_url)", "PASS", url))

        # UPDATE - redeploy with env var
        await svc.deploy(
            gcloud=gcloud,
            image=test_image,
            service_name=service_name,
            region=region,
            env_vars=["TEST_VAR=updated"],
        )
        results.append(format_operation("UPDATE", "PASS", "redeploy with env var"))
        ops["UPDATE"] = "PASS"

        # READ - get logs
        logs = await svc.get_logs(gcloud=gcloud, service_name=service_name, region=region, limit=10)
        results.append(format_operation("READ (get_logs)", "PASS", f"{len(logs)} chars"))

        # DELETE
        await svc.delete(gcloud=gcloud, service_name=service_name, region=region)
        results.append(format_operation("DELETE", "PASS"))
        ops["DELETE"] = "PASS"

    except Exception as e:
        results.append(format_operation("ERROR", "FAIL", str(e)))
        # Cleanup attempt
        try:
            await svc.delete(gcloud=gcloud, service_name=service_name, region=region)
        except Exception:
            pass
        raise

    return results, ops


async def test_gcp_cloud_run_oidc(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-cloud-run module with OIDC authentication (recommended).

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    results = [format_auth_header(AuthMethod.OIDC)]

    # Get gcloud container from OIDC
    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )

    crud_results, ops = await _test_cloud_run_crud(
        gcloud=gcloud,
        auth_method=AuthMethod.OIDC,
        region=region,
    )
    results.extend(crud_results)

    return "\n".join(results), ops


async def test_gcp_cloud_run_service_account(
    credentials: dagger.Secret,
    project_id: str,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-cloud-run module with service account JSON key.

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    results = [format_auth_header(AuthMethod.SERVICE_ACCOUNT)]

    # Get gcloud container from service account key
    gcloud = dag.gcp_auth().gcloud_container(
        credentials=credentials,
        project_id=project_id,
        region=region,
    )

    crud_results, ops = await _test_cloud_run_crud(
        gcloud=gcloud,
        auth_method=AuthMethod.SERVICE_ACCOUNT,
        region=region,
    )
    results.extend(crud_results)

    return "\n".join(results), ops


async def test_gcp_cloud_run_access_token(
    project_id: str,
    credentials: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account: str | None = None,
    oidc_token: dagger.Secret | None = None,
    oidc_url: dagger.Secret | None = None,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-cloud-run module with access token (LEGACY - NOT RECOMMENDED).

    Note: Cloud Run operations use gcloud CLI which works best with ADC.
    Access token authentication is less reliable for gcloud operations.

    If credentials (SA key) are provided, uses SA-based gcloud container.
    Otherwise, uses OIDC-based gcloud container.

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    warn_legacy_access_token()
    results = [format_auth_header(AuthMethod.ACCESS_TOKEN)]
    ops = {}

    # Cloud Run uses gcloud CLI which requires ADC credentials, not raw access tokens
    results.append("  NOTE: gcloud CLI requires ADC credentials, not raw access tokens")

    if credentials:
        results.append("  Using SA-based gcloud container for this test")
        gcloud = dag.gcp_auth().gcloud_container(
            credentials=credentials,
            project_id=project_id,
            region=region,
        )
    elif oidc_token and oidc_url and workload_identity_provider:
        results.append("  Using OIDC-based gcloud container for this test")
        gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
            region=region,
        )
    else:
        results.append(format_operation("ALL", "SKIP", "No credentials provided"))
        ops = {"CREATE": "SKIP", "READ": "SKIP", "UPDATE": "SKIP", "DELETE": "SKIP"}
        return "\n".join(results), ops

    crud_results, ops = await _test_cloud_run_crud(
        gcloud=gcloud,
        auth_method=AuthMethod.ACCESS_TOKEN,
        region=region,
    )
    results.extend(crud_results)

    return "\n".join(results), ops


async def test_gcp_cloud_run(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    credentials: dagger.Secret | None = None,
) -> str:
    """Run all gcp-cloud-run module tests with available auth methods.

    Args:
        workload_identity_provider: GCP WIF provider resource name
        service_account: Service account email
        project_id: GCP project ID
        oidc_token: ACTIONS_ID_TOKEN_REQUEST_TOKEN
        oidc_url: ACTIONS_ID_TOKEN_REQUEST_URL
        region: GCP region
        credentials: Optional service account JSON key for SA tests
    """
    all_results = []
    summary_data = {}

    # Always test OIDC (available in GitHub Actions)
    oidc_result, oidc_ops = await test_gcp_cloud_run_oidc(
        workload_identity_provider=workload_identity_provider,
        service_account=service_account,
        project_id=project_id,
        oidc_token=oidc_token,
        oidc_url=oidc_url,
        region=region,
    )
    all_results.append(oidc_result)
    summary_data["OIDC"] = oidc_ops

    # Test service account if credentials provided
    if credentials:
        sa_result, sa_ops = await test_gcp_cloud_run_service_account(
            credentials=credentials,
            project_id=project_id,
            region=region,
        )
        all_results.append(sa_result)
        summary_data["SERVICE_ACCOUNT"] = sa_ops
    else:
        all_results.append(
            f"{format_auth_header(AuthMethod.SERVICE_ACCOUNT)}\n"
            f"{format_operation('ALL', 'SKIP', 'No service account credentials provided')}"
        )
        summary_data["SERVICE_ACCOUNT"] = {"CREATE": "SKIP", "READ": "SKIP", "UPDATE": "SKIP", "DELETE": "SKIP"}

    # Test access token (legacy) - with note about limitations
    token_result, token_ops = await test_gcp_cloud_run_access_token(
        project_id=project_id,
        credentials=credentials,
        workload_identity_provider=workload_identity_provider,
        service_account=service_account,
        oidc_token=oidc_token,
        oidc_url=oidc_url,
        region=region,
    )
    all_results.append(token_result)
    summary_data["ACCESS_TOKEN"] = token_ops

    # Add summary table
    all_results.append(format_test_summary(summary_data))

    return "\n\n".join(all_results)
