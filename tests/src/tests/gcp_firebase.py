"""Tests for gcp-firebase module.

Tests all authentication methods:
- OIDC (recommended): Workload Identity Federation via GitHub Actions
- Service Account: Direct JSON key file
- Access Token (legacy): Pre-fetched bearer token

Each auth method is tested with:
- Firebase Hosting (build, deploy_preview, delete_channel)
- Firestore CRUD (create, read, update, delete)
- Scripts (node execution)
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
    get_access_token_from_service_account,
)


# Fixtures path relative to module root
FIXTURES_PATH = "src/tests/fixtures/firestore-scripts"


async def _test_hosting_crud(
    project_id: str,
    source: dagger.Directory,
    auth_method: AuthMethod,
    oidc_token: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account_email: str | None = None,
    credentials: dagger.Secret | None = None,
    access_token: dagger.Secret | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Test Firebase Hosting operations with specified auth method.

    Returns:
        Tuple of (results list, operations dict for summary)
    """
    results = [format_component_header("Hosting")]
    ops = {}
    firebase = dag.gcp_firebase()
    channel_id = f"test-{auth_method.value}-{int(time.time())}"

    # Build (no auth required)
    dist = firebase.build(source=source)
    entries = await dist.entries()
    if len(entries) == 0:
        raise ValueError("Build produced no output files")
    results.append(format_operation("BUILD", "PASS", f"{len(entries)} files"))
    ops["H_BUILD"] = "PASS"

    try:
        # Deploy preview with the specified auth method
        if auth_method == AuthMethod.OIDC:
            preview_url = await firebase.deploy_preview(
                project_id=project_id,
                channel_id=channel_id,
                source=source,
                oidc_token=oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account_email,
            )
        elif auth_method == AuthMethod.SERVICE_ACCOUNT:
            preview_url = await firebase.deploy_preview(
                project_id=project_id,
                channel_id=channel_id,
                source=source,
                credentials=credentials,
            )
        elif auth_method == AuthMethod.ACCESS_TOKEN:
            preview_url = await firebase.deploy_preview(
                project_id=project_id,
                channel_id=channel_id,
                source=source,
                access_token=access_token,
            )
        else:
            raise ValueError(f"Unknown auth method: {auth_method}")

        if not preview_url.startswith("https://"):
            raise ValueError(f"Invalid preview URL: {preview_url}")
        results.append(format_operation("DEPLOY", "PASS", preview_url[:50] + "..."))
        ops["H_DEPLOY"] = "PASS"

        # Delete channel with the same auth method
        if auth_method == AuthMethod.OIDC:
            await firebase.delete_channel(
                project_id=project_id,
                channel_id=channel_id,
                oidc_token=oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account_email,
            )
        elif auth_method == AuthMethod.SERVICE_ACCOUNT:
            await firebase.delete_channel(
                project_id=project_id,
                channel_id=channel_id,
                credentials=credentials,
            )
        elif auth_method == AuthMethod.ACCESS_TOKEN:
            await firebase.delete_channel(
                project_id=project_id,
                channel_id=channel_id,
                access_token=access_token,
            )
        results.append(format_operation("DELETE", "PASS", channel_id))
        ops["H_DELETE"] = "PASS"

    except Exception as e:
        results.append(format_operation("ERROR", "FAIL", str(e)))
        # Cleanup attempt
        try:
            if auth_method == AuthMethod.OIDC:
                await firebase.delete_channel(
                    project_id=project_id,
                    channel_id=channel_id,
                    oidc_token=oidc_token,
                    workload_identity_provider=workload_identity_provider,
                    service_account_email=service_account_email,
                )
            elif auth_method == AuthMethod.SERVICE_ACCOUNT:
                await firebase.delete_channel(
                    project_id=project_id,
                    channel_id=channel_id,
                    credentials=credentials,
                )
            elif auth_method == AuthMethod.ACCESS_TOKEN:
                await firebase.delete_channel(
                    project_id=project_id,
                    channel_id=channel_id,
                    access_token=access_token,
                )
        except Exception:
            pass
        raise

    return results, ops


async def _test_firestore_crud(
    gcloud: dagger.Container,
    auth_method: AuthMethod,
    region: str = "europe-west9",
) -> tuple[list[str], dict[str, str]]:
    """Test Firestore CRUD operations with specified gcloud container.

    Returns:
        Tuple of (results list, operations dict for summary)
    """
    results = [format_component_header("Firestore")]
    ops = {}
    database_id = f"test-{auth_method.value}-{int(time.time())}"
    firestore = dag.gcp_firebase().firestore()

    try:
        # CREATE
        await firestore.create(gcloud=gcloud, database_id=database_id, location=region)
        results.append(format_operation("CREATE", "PASS", database_id))
        ops["F_CREATE"] = "PASS"

        # READ - exists
        exists = await firestore.exists(gcloud=gcloud, database_id=database_id)
        if not exists:
            raise Exception(f"Database {database_id} not found after create")
        results.append(format_operation("READ (exists)", "PASS"))

        # READ - describe
        description = await firestore.describe(gcloud=gcloud, database_id=database_id)
        if database_id not in description:
            raise Exception(f"Database {database_id} not in describe output")
        results.append(format_operation("READ (describe)", "PASS"))

        # READ - list
        db_list = await firestore.list_(gcloud=gcloud)
        if database_id not in db_list:
            raise Exception(f"Database {database_id} not in list output")
        results.append(format_operation("READ (list)", "PASS"))
        ops["F_READ"] = "PASS"

        # UPDATE - enable then disable delete protection
        await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=True)
        results.append(format_operation("UPDATE (enable)", "PASS"))

        await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
        results.append(format_operation("UPDATE (disable)", "PASS"))
        ops["F_UPDATE"] = "PASS"

        # DELETE
        await firestore.delete(gcloud=gcloud, database_id=database_id)
        results.append(format_operation("DELETE", "PASS"))
        ops["F_DELETE"] = "PASS"

    except Exception as e:
        results.append(format_operation("ERROR", "FAIL", str(e)))
        # Cleanup attempt
        try:
            await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
            await firestore.delete(gcloud=gcloud, database_id=database_id)
        except Exception:
            pass
        raise

    return results, ops


async def _test_scripts(
    project_id: str,
    scripts_source: dagger.Directory,
    database_id: str,
    auth_method: AuthMethod,
    oidc_token: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account_email: str | None = None,
    credentials: dagger.Secret | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Test Firebase Scripts operations with specified auth method.

    Returns:
        Tuple of (results list, operations dict for summary)
    """
    results = [format_component_header("Scripts")]
    ops = {}
    scripts = dag.gcp_firebase().scripts()

    # Note: Access token is not supported for scripts (needs ADC file)
    if auth_method == AuthMethod.ACCESS_TOKEN:
        results.append(format_operation("ALL", "SKIP", "Access token not supported (needs ADC)"))
        ops["S_NODE"] = "SKIP"
        ops["S_CONTAINER"] = "SKIP"
        return results, ops

    try:
        if auth_method == AuthMethod.OIDC:
            node_output = await scripts.node(
                source=scripts_source,
                script="seed-data.ts",
                oidc_token=oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account_email,
                project_id=project_id,
                working_dir=".",
                install_command="npm install",
                env=[f"FIRESTORE_DATABASE_ID={database_id}"],
            )
        elif auth_method == AuthMethod.SERVICE_ACCOUNT:
            node_output = await scripts.node(
                source=scripts_source,
                script="seed-data.ts",
                credentials=credentials,
                project_id=project_id,
                working_dir=".",
                install_command="npm install",
                env=[f"FIRESTORE_DATABASE_ID={database_id}"],
            )
        else:
            raise ValueError(f"Unknown auth method: {auth_method}")

        if '"status":"success"' not in node_output:
            raise Exception(f"Node script failed: {node_output}")
        results.append(format_operation("NODE", "PASS", "script executed"))
        ops["S_NODE"] = "PASS"

        # Verify container credentials are configured correctly
        if auth_method == AuthMethod.OIDC:
            container = scripts.container(
                source=scripts_source,
                base_image="alpine:latest",
                oidc_token=oidc_token,
                workload_identity_provider=workload_identity_provider,
                service_account_email=service_account_email,
                project_id=project_id,
            )
            gac_check = await container.with_exec(["sh", "-c", "echo $GOOGLE_APPLICATION_CREDENTIALS"]).stdout()
            if "/tmp/gcp-credentials.json" not in gac_check:
                raise Exception("GOOGLE_APPLICATION_CREDENTIALS not set correctly")
            results.append(format_operation("CONTAINER", "PASS", "credentials configured"))
            ops["S_CONTAINER"] = "PASS"
        elif auth_method == AuthMethod.SERVICE_ACCOUNT:
            container = scripts.container(
                source=scripts_source,
                base_image="alpine:latest",
                credentials=credentials,
                project_id=project_id,
            )
            gac_check = await container.with_exec(["sh", "-c", "echo $GOOGLE_APPLICATION_CREDENTIALS"]).stdout()
            if "/tmp/gcp-credentials.json" not in gac_check:
                raise Exception("GOOGLE_APPLICATION_CREDENTIALS not set correctly")
            results.append(format_operation("CONTAINER", "PASS", "credentials configured"))
            ops["S_CONTAINER"] = "PASS"

    except Exception as e:
        results.append(format_operation("ERROR", "FAIL", str(e)))
        raise

    return results, ops


async def test_gcp_firebase_oidc(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "europe-west9",
) -> tuple[str, dict[str, str]]:
    """Test gcp-firebase module with OIDC authentication (recommended).

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    results = [format_auth_header(AuthMethod.OIDC)]
    ops = {}

    # Get OIDC token with GCP audience
    audience = f"//iam.googleapis.com/{workload_identity_provider}"
    firebase_oidc_token = dag.oidc_token().github_token(
        request_token=oidc_token,
        request_url=oidc_url,
        audience=audience,
    )

    # Get gcloud container for Firestore operations
    gcloud = dag.gcp_auth().gcloud_container_from_oidc_token(
        oidc_token=firebase_oidc_token,
        workload_identity_provider=workload_identity_provider,
        project_id=project_id,
        service_account_email=service_account,
        region=region,
    )

    # Source directories
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()
    scripts_source = dag.current_module().source().directory(FIXTURES_PATH)

    # Test Hosting
    hosting_results, hosting_ops = await _test_hosting_crud(
        project_id=project_id,
        source=source,
        auth_method=AuthMethod.OIDC,
        oidc_token=firebase_oidc_token,
        workload_identity_provider=workload_identity_provider,
        service_account_email=service_account,
    )
    results.extend(hosting_results)
    ops.update(hosting_ops)

    # Test Firestore
    firestore_results, firestore_ops = await _test_firestore_crud(
        gcloud=gcloud,
        auth_method=AuthMethod.OIDC,
        region=region,
    )
    results.extend(firestore_results)
    ops.update(firestore_ops)

    # Test Scripts (create temp database for script test)
    database_id = f"script-test-{int(time.time())}"
    firestore = dag.gcp_firebase().firestore()
    try:
        await firestore.create(gcloud=gcloud, database_id=database_id, location=region)
        scripts_results, scripts_ops = await _test_scripts(
            project_id=project_id,
            scripts_source=scripts_source,
            database_id=database_id,
            auth_method=AuthMethod.OIDC,
            oidc_token=firebase_oidc_token,
            workload_identity_provider=workload_identity_provider,
            service_account_email=service_account,
        )
        results.extend(scripts_results)
        ops.update(scripts_ops)
    finally:
        try:
            await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
            await firestore.delete(gcloud=gcloud, database_id=database_id)
        except Exception:
            pass

    return "\n".join(results), ops


async def test_gcp_firebase_service_account(
    credentials: dagger.Secret,
    project_id: str,
    region: str = "europe-west9",
) -> tuple[str, dict[str, str]]:
    """Test gcp-firebase module with service account JSON key.

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    results = [format_auth_header(AuthMethod.SERVICE_ACCOUNT)]
    ops = {}

    # Get gcloud container for Firestore operations
    gcloud = dag.gcp_auth().gcloud_container(
        credentials=credentials,
        project_id=project_id,
        region=region,
    )

    # Source directories
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()
    scripts_source = dag.current_module().source().directory(FIXTURES_PATH)

    # Test Hosting
    hosting_results, hosting_ops = await _test_hosting_crud(
        project_id=project_id,
        source=source,
        auth_method=AuthMethod.SERVICE_ACCOUNT,
        credentials=credentials,
    )
    results.extend(hosting_results)
    ops.update(hosting_ops)

    # Test Firestore
    firestore_results, firestore_ops = await _test_firestore_crud(
        gcloud=gcloud,
        auth_method=AuthMethod.SERVICE_ACCOUNT,
        region=region,
    )
    results.extend(firestore_results)
    ops.update(firestore_ops)

    # Test Scripts (create temp database for script test)
    database_id = f"script-test-{int(time.time())}"
    firestore = dag.gcp_firebase().firestore()
    try:
        await firestore.create(gcloud=gcloud, database_id=database_id, location=region)
        scripts_results, scripts_ops = await _test_scripts(
            project_id=project_id,
            scripts_source=scripts_source,
            database_id=database_id,
            auth_method=AuthMethod.SERVICE_ACCOUNT,
            credentials=credentials,
        )
        results.extend(scripts_results)
        ops.update(scripts_ops)
    finally:
        try:
            await firestore.update(gcloud=gcloud, database_id=database_id, delete_protection=False)
            await firestore.delete(gcloud=gcloud, database_id=database_id)
        except Exception:
            pass

    return "\n".join(results), ops


async def test_gcp_firebase_access_token(
    project_id: str,
    credentials: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account: str | None = None,
    oidc_token: dagger.Secret | None = None,
    oidc_url: dagger.Secret | None = None,
    region: str = "europe-west9",
) -> tuple[str, dict[str, str]]:
    """Test gcp-firebase module with access token (LEGACY - NOT RECOMMENDED).

    If credentials (SA key) are provided, generates token from SA key.
    Otherwise, generates token from OIDC credentials.

    Returns:
        Tuple of (formatted results string, operations dict for summary)
    """
    warn_legacy_access_token()
    results = [format_auth_header(AuthMethod.ACCESS_TOKEN)]
    ops = {}

    # Generate access token from Service Account key (if provided)
    if credentials:
        results.append("  NOTE: access_token from Service Account Key")
        access_token = await get_access_token_from_service_account(
            credentials=credentials,
            project_id=project_id,
            region=region,
        )
    elif oidc_token and oidc_url and workload_identity_provider:
        results.append("  NOTE: access_token from OIDC")
        # Generate access token from OIDC (for testing legacy method)
        # Note: Cross-module calls returning Secret don't need await
        access_token = dag.gcp_auth().access_token_from_github_actions(
            workload_identity_provider=workload_identity_provider,
            project_id=project_id,
            oidc_request_token=oidc_token,
            oidc_request_url=oidc_url,
            service_account_email=service_account,
        )
    else:
        results.append(format_operation("ALL", "SKIP", "No credentials provided"))
        ops = {
            "H_BUILD": "SKIP", "H_DEPLOY": "SKIP", "H_DELETE": "SKIP",
            "F_CREATE": "SKIP", "F_READ": "SKIP", "F_UPDATE": "SKIP", "F_DELETE": "SKIP",
            "S_NODE": "SKIP", "S_CONTAINER": "SKIP",
        }
        return "\n".join(results), ops

    # Source directory
    source = dag.git("https://github.com/telchak/firebase-dagger-template.git").branch("main").tree()

    # Test Hosting only (access token not supported for scripts)
    hosting_results, hosting_ops = await _test_hosting_crud(
        project_id=project_id,
        source=source,
        auth_method=AuthMethod.ACCESS_TOKEN,
        access_token=access_token,
    )
    results.extend(hosting_results)
    ops.update(hosting_ops)

    # Test Firestore (uses gcloud container, not access token directly)
    # Note: We test Firestore with gcloud from OIDC since access token flow
    # doesn't apply to gcloud CLI operations
    results.append(format_component_header("Firestore"))
    results.append(format_operation("ALL", "SKIP", "Firestore uses gcloud (tested via OIDC)"))
    ops["F_CREATE"] = "SKIP"
    ops["F_READ"] = "SKIP"
    ops["F_UPDATE"] = "SKIP"
    ops["F_DELETE"] = "SKIP"

    # Scripts don't support access token
    scripts_results, scripts_ops = await _test_scripts(
        project_id=project_id,
        scripts_source=dag.current_module().source().directory(FIXTURES_PATH),
        database_id="dummy",  # Not used since access token is skipped
        auth_method=AuthMethod.ACCESS_TOKEN,
    )
    results.extend(scripts_results)
    ops.update(scripts_ops)

    return "\n".join(results), ops


async def test_gcp_firebase(
    workload_identity_provider: str,
    service_account: str,
    project_id: str,
    oidc_token: dagger.Secret,
    oidc_url: dagger.Secret,
    region: str = "europe-west9",
    credentials: dagger.Secret | None = None,
) -> str:
    """Run all gcp-firebase module tests with available auth methods.

    Args:
        workload_identity_provider: GCP WIF provider resource name
        service_account: Service account email
        project_id: GCP project ID
        oidc_token: ACTIONS_ID_TOKEN_REQUEST_TOKEN
        oidc_url: ACTIONS_ID_TOKEN_REQUEST_URL
        region: GCP region for Firestore
        credentials: Optional service account JSON key for SA tests
    """
    all_results = []
    summary_data = {}

    # Always test OIDC (available in GitHub Actions)
    oidc_result, oidc_ops = await test_gcp_firebase_oidc(
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
        sa_result, sa_ops = await test_gcp_firebase_service_account(
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
        summary_data["SERVICE_ACCOUNT"] = {
            "H_BUILD": "SKIP", "H_DEPLOY": "SKIP", "H_DELETE": "SKIP",
            "F_CREATE": "SKIP", "F_READ": "SKIP", "F_UPDATE": "SKIP", "F_DELETE": "SKIP",
            "S_NODE": "SKIP", "S_CONTAINER": "SKIP",
        }

    # Test access token (legacy)
    token_result, token_ops = await test_gcp_firebase_access_token(
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
