"""Authentication utilities for multi-auth testing.

Provides standardized formatting and helpers for testing GCP modules
with different credential types:
- OIDC (recommended): Workload Identity Federation via GitHub Actions
- Service Account: Direct JSON key file
- Access Token (legacy): Pre-fetched bearer token
"""

import sys
import warnings
from enum import Enum

import dagger
from dagger import dag


class AuthMethod(Enum):
    """Supported authentication methods for GCP modules."""

    OIDC = "oidc"
    SERVICE_ACCOUNT = "service_account"
    ACCESS_TOKEN = "access_token"


def warn_legacy_access_token() -> None:
    """Emit deprecation warning for access token authentication.

    Uses both warnings.warn() for programmatic handling and stderr for visibility,
    since DeprecationWarning is hidden by default in Python.
    """
    message = (
        "\n"
        "=" * 70 + "\n"
        "WARNING: Access Token authentication is LEGACY and NOT RECOMMENDED.\n"
        "\n"
        "This authentication method:\n"
        "- Uses short-lived tokens that expire quickly\n"
        "- Requires external token refresh mechanisms\n"
        "- May be deprecated by GCP in the future\n"
        "\n"
        "Recommended alternatives:\n"
        "- OIDC + Workload Identity Federation (for CI/CD pipelines)\n"
        "- Service Account JSON key (for local development)\n"
        "=" * 70
    )

    # Emit warning for programmatic handling
    warnings.warn(message, DeprecationWarning, stacklevel=2)

    # Also print to stderr for visibility (DeprecationWarning is hidden by default)
    print(message, file=sys.stderr)


async def get_access_token_from_service_account(
    credentials: dagger.Secret,
    project_id: str,
    region: str = "us-central1",
) -> dagger.Secret:
    """Generate an access token from a service account JSON key.

    This uses the service account key to authenticate with gcloud,
    then extracts an access token for APIs that accept Bearer tokens.
    """
    import uuid

    gcloud = dag.gcp_auth().gcloud_container(
        credentials=credentials,
        project_id=project_id,
        region=region,
    )

    # Use UUID to bust cache - ensures fresh token even with rapid sequential calls
    cache_buster = str(uuid.uuid4())
    token_output = await (
        gcloud
        .with_env_variable("CACHE_BUSTER", cache_buster)
        .with_exec(["gcloud", "auth", "print-access-token"])
        .stdout()
    )
    return dag.set_secret("gcp_access_token_from_sa", token_output.strip())


def format_auth_header(auth_method: AuthMethod) -> str:
    """Format a header for test output indicating the auth method."""
    method_name = auth_method.value.upper().replace("_", " ")
    if auth_method == AuthMethod.ACCESS_TOKEN:
        return f"{'=' * 50}\n  {method_name} (LEGACY - NOT RECOMMENDED)\n{'=' * 50}"
    elif auth_method == AuthMethod.OIDC:
        return f"{'=' * 50}\n  {method_name} (RECOMMENDED)\n{'=' * 50}"
    else:
        return f"{'=' * 50}\n  {method_name}\n{'=' * 50}"


def format_operation(operation: str, status: str, details: str = "") -> str:
    """Format a single operation result consistently.

    Args:
        operation: The operation name (e.g., "CREATE", "READ", "UPDATE", "DELETE")
        status: "PASS", "FAIL", or "SKIP"
        details: Optional details about the result
    """
    status_icon = {"PASS": "[OK]", "FAIL": "[!!]", "SKIP": "[--]"}.get(status, "[??]")
    if details:
        return f"  {status_icon} {operation}: {details}"
    return f"  {status_icon} {operation}"


def format_component_header(component: str) -> str:
    """Format a component/feature header (e.g., 'Hosting', 'Firestore')."""
    return f"\n  [{component}]"


def format_test_summary(results: dict[str, dict[str, str]]) -> str:
    """Format a summary table of test results by auth method.

    Args:
        results: Dict of {auth_method: {operation: status}}

    Example:
        results = {
            "OIDC": {"CREATE": "PASS", "READ": "PASS", "DELETE": "PASS"},
            "SERVICE_ACCOUNT": {"CREATE": "PASS", "READ": "PASS", "DELETE": "PASS"},
            "ACCESS_TOKEN": {"CREATE": "SKIP", "READ": "SKIP", "DELETE": "SKIP"},
        }
    """
    if not results:
        return ""

    # Get all unique operations
    all_ops = set()
    for ops in results.values():
        all_ops.update(ops.keys())
    operations = sorted(all_ops)

    # Build header
    lines = ["\n" + "=" * 60, "  SUMMARY", "=" * 60]

    # Column widths
    auth_width = max(len(auth) for auth in results.keys()) + 2
    op_width = 8

    # Header row
    header = f"  {'Auth Method':<{auth_width}}"
    for op in operations:
        header += f" | {op[:op_width]:<{op_width}}"
    lines.append(header)
    lines.append("  " + "-" * (auth_width + (op_width + 3) * len(operations)))

    # Data rows
    for auth, ops in results.items():
        row = f"  {auth:<{auth_width}}"
        for op in operations:
            status = ops.get(op, "N/A")
            icon = {"PASS": "OK", "FAIL": "!!", "SKIP": "--"}.get(status, "??")
            row += f" | {icon:^{op_width}}"
        lines.append(row)

    return "\n".join(lines)
