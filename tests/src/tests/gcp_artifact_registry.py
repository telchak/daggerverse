"""Tests for gcp-artifact-registry module.

Tests all authentication methods via gcloud container:
- OIDC (recommended): Workload Identity Federation via GitHub Actions
- Service Account: Direct JSON key file
- Access Token (legacy): Pre-fetched bearer token

Tests include:
- get_image_uri (no auth required)
- list_images (requires auth)
"""

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


async def _test_artifact_registry_operations(
    gcloud: dagger.Container,
    auth_method: AuthMethod,
    project_id: str,
    repository: str,
    region: str = "us-central1",
) -> tuple[list[str], dict[str, str]]:
    """Test Artifact Registry operations with specified gcloud container.

    Returns:
        Tuple of (results list, operations dict for summary)
    """
    results = [format_component_header("Artifact Registry")]
    ops = {}
    ar = dag.gcp_artifact_registry()

    # Test get_image_uri (no credentials needed - just formatting)
    uri = await ar.get_image_uri(
        project_id="test-project",
        repository="test-repo",
        image_name="test-image",
        tag="v1.0.0",
    )
    expected = "us-central1-docker.pkg.dev/test-project/test-repo/test-image:v1.0.0"
    if uri != expected:
        raise ValueError(f"Expected {expected}, got {uri}")
    results.append(format_operation("GET_URI", "PASS", uri))
    ops["GET_URI"] = "PASS"

    # Test list_images (requires auth)
    await ar.list_images(
        gcloud=gcloud,
        project_id=project_id,
        repository=repository,
        region=region,
    )
    results.append(format_operation("LIST", "PASS", repository))
    ops["LIST"] = "PASS"

    return results, ops


async def test_gcp_artifact_registry_oidc(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    repository: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-artifact-registry module with OIDC authentication (recommended)."""
    results = [format_auth_header(AuthMethod.OIDC)]

    gcloud = dag.gcp_auth().gcloud_container_from_github_actions(
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        oidc_request_token=oidc_token,
        oidc_request_url=oidc_url,
        service_account_email=service_account,
        region=region,
    )

    op_results, ops = await _test_artifact_registry_operations(
        gcloud=gcloud,
        auth_method=AuthMethod.OIDC,
        project_id=project_id,
        repository=repository,
        region=region,
    )
    results.extend(op_results)

    return "\n".join(results), ops


async def test_gcp_artifact_registry_service_account(
    credentials: dagger.Secret,
    project_id: str,
    repository: str,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-artifact-registry module with service account JSON key."""
    results = [format_auth_header(AuthMethod.SERVICE_ACCOUNT)]

    gcloud = dag.gcp_auth().gcloud_container(
        credentials=credentials,
        project_id=project_id,
        region=region,
    )

    op_results, ops = await _test_artifact_registry_operations(
        gcloud=gcloud,
        auth_method=AuthMethod.SERVICE_ACCOUNT,
        project_id=project_id,
        repository=repository,
        region=region,
    )
    results.extend(op_results)

    return "\n".join(results), ops


async def test_gcp_artifact_registry_access_token(
    project_id: str,
    repository: str,
    credentials: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account: str | None = None,
    oidc_token: dagger.Secret | None = None,
    oidc_url: dagger.Secret | None = None,
    region: str = "us-central1",
) -> tuple[str, dict[str, str]]:
    """Test gcp-artifact-registry module with access token (LEGACY - NOT RECOMMENDED).

    If credentials (SA key) are provided, uses SA-based gcloud container.
    Otherwise, uses OIDC-based gcloud container.
    """
    warn_legacy_access_token()
    results = [format_auth_header(AuthMethod.ACCESS_TOKEN)]
    ops = {}

    # Note: gcloud CLI works better with ADC
    results.append("  NOTE: gcloud CLI requires ADC credentials")

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
        ops = {"GET_URI": "SKIP", "LIST": "SKIP"}
        return "\n".join(results), ops

    op_results, ops = await _test_artifact_registry_operations(
        gcloud=gcloud,
        auth_method=AuthMethod.ACCESS_TOKEN,
        project_id=project_id,
        repository=repository,
        region=region,
    )
    results.extend(op_results)

    return "\n".join(results), ops


async def test_gcp_artifact_registry(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    repository: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "us-central1",
    credentials: dagger.Secret | None = None,
) -> str:
    """Run all gcp-artifact-registry module tests with available auth methods.

    Args:
        workload_identity_provider: GCP WIF provider resource name
        service_account: Service account email
        project_id: GCP project ID
        repository: Artifact Registry repository name
        oidc_token: ACTIONS_ID_TOKEN_REQUEST_TOKEN
        oidc_url: ACTIONS_ID_TOKEN_REQUEST_URL
        region: GCP region
        credentials: Optional service account JSON key for SA tests
    """
    all_results = []
    summary_data = {}

    # Always test OIDC
    oidc_result, oidc_ops = await test_gcp_artifact_registry_oidc(
        workload_identity_provider=workload_identity_provider,
        service_account=service_account,
        project_id=project_id,
        repository=repository,
        oidc_token=oidc_token,
        oidc_url=oidc_url,
        region=region,
    )
    all_results.append(oidc_result)
    summary_data["OIDC"] = oidc_ops

    # Test service account if credentials provided
    if credentials:
        sa_result, sa_ops = await test_gcp_artifact_registry_service_account(
            credentials=credentials,
            project_id=project_id,
            repository=repository,
            region=region,
        )
        all_results.append(sa_result)
        summary_data["SERVICE_ACCOUNT"] = sa_ops
    else:
        all_results.append(
            f"{format_auth_header(AuthMethod.SERVICE_ACCOUNT)}\n"
            f"{format_operation('ALL', 'SKIP', 'No service account credentials provided')}"
        )
        summary_data["SERVICE_ACCOUNT"] = {"GET_URI": "SKIP", "LIST": "SKIP"}

    # Test access token (legacy)
    token_result, token_ops = await test_gcp_artifact_registry_access_token(
        project_id=project_id,
        repository=repository,
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
