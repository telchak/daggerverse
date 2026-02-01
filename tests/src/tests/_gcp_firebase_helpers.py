"""Internal helper functions for gcp-firebase tests.

These functions test individual Firebase components (Hosting, Firestore, Scripts)
with a given authentication method. They are used by the main test functions in
gcp_firebase.py.
"""

import time

import dagger
from dagger import dag

from .auth_utils import (
    AuthMethod,
    format_component_header,
    format_operation,
)


async def test_hosting_crud(
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
    # Firebase channel IDs only allow lowercase alphanumeric and dashes
    channel_id = f"test-{auth_method.value.replace('_', '-')}-{int(time.time())}"

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


async def test_firestore_crud(
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
    # Firestore database IDs only allow lowercase alphanumeric and dashes
    database_id = f"test-{auth_method.value.replace('_', '-')}-{int(time.time())}"
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


async def test_scripts(
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
