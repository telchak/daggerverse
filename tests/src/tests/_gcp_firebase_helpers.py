"""Internal helper functions for gcp-firebase tests.

These functions test individual Firebase components (Hosting, Firestore, Scripts)
with a given authentication method. They are used by the main test functions in
gcp_firebase.py.
"""

import time
import uuid

import dagger
from dagger import dag

from .auth_utils import (
    AuthMethod,
    format_component_header,
    format_operation,
)


def _auth_kwargs(
    auth_method: AuthMethod,
    oidc_token: dagger.Secret | None = None,
    workload_identity_provider: str | None = None,
    service_account_email: str | None = None,
    credentials: dagger.Secret | None = None,
    access_token: dagger.Secret | None = None,
) -> dict:
    """Build auth keyword arguments for a Firebase operation based on auth method."""
    if auth_method == AuthMethod.OIDC:
        return {
            "oidc_token": oidc_token,
            "workload_identity_provider": workload_identity_provider,
            "service_account_email": service_account_email,
        }
    elif auth_method == AuthMethod.SERVICE_ACCOUNT:
        return {"credentials": credentials}
    elif auth_method == AuthMethod.ACCESS_TOKEN:
        return {"access_token": access_token}
    else:
        raise ValueError(f"Unknown auth method: {auth_method}")


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
    channel_id = f"test-{auth_method.value.replace('_', '-')}-{int(time.time())}"
    auth_kw = _auth_kwargs(
        auth_method, oidc_token, workload_identity_provider,
        service_account_email, credentials, access_token,
    )

    # Build (no auth required)
    dist = firebase.build(source=source)
    entries = await dist.entries()
    if len(entries) == 0:
        raise ValueError("Build produced no output files")
    results.append(format_operation("BUILD", "PASS", f"{len(entries)} files"))
    ops["H_BUILD"] = "PASS"

    pre_built_source = source.with_directory("dist", dist)

    try:
        preview_url = await firebase.deploy_preview(
            project_id=project_id,
            channel_id=channel_id,
            source=pre_built_source,
            skip_build=True,
            **auth_kw,
        )

        if not preview_url.startswith("https://"):
            raise ValueError(f"Invalid preview URL: {preview_url}")
        results.append(format_operation("DEPLOY", "PASS", preview_url[:50] + "..."))
        ops["H_DEPLOY"] = "PASS"

        await firebase.delete_channel(
            project_id=project_id, channel_id=channel_id, **auth_kw,
        )
        results.append(format_operation("DELETE", "PASS", channel_id))
        ops["H_DELETE"] = "PASS"

    except Exception as e:
        results.append(format_operation("ERROR", "FAIL", str(e)))
        try:
            await firebase.delete_channel(
                project_id=project_id, channel_id=channel_id, **auth_kw,
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
            raise RuntimeError(f"Database {database_id} not found after create")
        results.append(format_operation("READ (exists)", "PASS"))

        # READ - describe
        description = await firestore.describe(gcloud=gcloud, database_id=database_id)
        if database_id not in description:
            raise RuntimeError(f"Database {database_id} not in describe output")
        results.append(format_operation("READ (describe)", "PASS"))

        # READ - list (retry for GCP eventual consistency — list index
        # can lag behind describe/get after a recent create).
        # Each attempt must bust Dagger's content-addressed cache by
        # varying the gcloud container, otherwise we re-read the same result.
        for attempt in range(6):
            cache_busted = gcloud.with_env_variable("_CACHE_BUST", str(uuid.uuid4()))
            db_list = await firestore.list_(gcloud=cache_busted)
            if database_id in db_list:
                break
            time.sleep(5)
        else:
            raise RuntimeError(f"Database {database_id} not in list output")
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

    auth_kw = _auth_kwargs(
        auth_method, oidc_token, workload_identity_provider,
        service_account_email, credentials,
    )

    try:
        node_output = await scripts.node(
            source=scripts_source,
            script="seed-data.ts",
            project_id=project_id,
            working_dir=".",
            install_command="npm install",
            env=[f"FIRESTORE_DATABASE_ID={database_id}"],
            **auth_kw,
        )

        if '"status":"success"' not in node_output:
            raise RuntimeError(f"Node script failed: {node_output}")
        results.append(format_operation("NODE", "PASS", "script executed"))
        ops["S_NODE"] = "PASS"

        container = scripts.container(
            source=scripts_source,
            base_image="alpine:latest",
            project_id=project_id,
            **auth_kw,
        )
        gac_check = await container.with_exec(["sh", "-c", "echo $GOOGLE_APPLICATION_CREDENTIALS"]).stdout()
        if "/run/secrets/gcp-credentials.json" not in gac_check:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set correctly")
        results.append(format_operation("CONTAINER", "PASS", "credentials configured"))
        ops["S_CONTAINER"] = "PASS"

    except Exception as e:
        results.append(format_operation("ERROR", "FAIL", str(e)))
        raise

    return results, ops
