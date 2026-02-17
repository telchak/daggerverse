"""Google Cloud Run deployment module for Dagger."""

import re
from typing import Annotated

import dagger
from dagger import Doc, function, object_type


# Validation patterns for GCP resource names
_CLOUD_RUN_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9-]{0,62}$')
_GCP_REGION_PATTERN = re.compile(r'^[a-z]+-[a-z]+\d+(-[a-z])?$')

# Container image URI pattern (supports gcr.io, artifact registry, docker hub, etc.)
_IMAGE_URI_PATTERN = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?'  # registry/image name start
    r'(/[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)*'  # path components
    r'(:[a-zA-Z0-9][a-zA-Z0-9._-]{0,127})?'  # optional tag
    r'(@sha256:[a-fA-F0-9]{64})?$'  # optional digest
)

# Timeout format pattern (e.g., "300s", "5m", "1h")
_TIMEOUT_PATTERN = re.compile(r'^\d+[smh]$')

# CPU format pattern (e.g., "1", "2", "0.5", "1000m")
_CPU_PATTERN = re.compile(r'^(\d+(\.\d+)?|\d+m)$')

# Memory format pattern (e.g., "512Mi", "1Gi", "2G")
_MEMORY_PATTERN = re.compile(r'^\d+(Mi|Gi|M|G|Ki|K)$')

# Environment variable format pattern (KEY=VALUE)
_ENV_VAR_PATTERN = re.compile(r'^[a-zA-Z_]\w*=.*$')

# Service account email pattern
_SERVICE_ACCOUNT_PATTERN = re.compile(
    r'^[a-zA-Z0-9-]+@[a-zA-Z0-9-]+\.iam\.gserviceaccount\.com$'
)

# Log filter pattern (only allow safe characters)
_LOG_FILTER_PATTERN = re.compile(r'^[a-zA-Z0-9._>=<:\s"\'()-]+$')


def _validate_cloud_run_name(name: str, field: str = "name") -> str:
    """Validate Cloud Run service/job name."""
    if not _CLOUD_RUN_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid {field}: '{name}'. Must be lowercase, start with a letter, "
            "contain only letters, numbers, and hyphens, and be 1-63 characters."
        )
    return name


def _validate_region(region: str) -> str:
    """Validate GCP region format."""
    if not _GCP_REGION_PATTERN.match(region):
        raise ValueError(f"Invalid GCP region format: '{region}'")
    return region


def _validate_image(image: str) -> str:
    """Validate container image URI format."""
    if not image:
        raise ValueError("Image URI cannot be empty")
    if len(image) > 500:
        raise ValueError("Image URI too long (max 500 characters)")
    if not _IMAGE_URI_PATTERN.match(image):
        raise ValueError(f"Invalid container image URI: '{image}'")
    return image


def _validate_timeout(timeout: str) -> str:
    """Validate timeout format (e.g., '300s', '5m', '1h')."""
    if not _TIMEOUT_PATTERN.match(timeout):
        raise ValueError(
            f"Invalid timeout format: '{timeout}'. "
            "Must be a number followed by s (seconds), m (minutes), or h (hours)."
        )
    return timeout


def _validate_cpu(cpu: str) -> str:
    """Validate CPU allocation format."""
    if not _CPU_PATTERN.match(cpu):
        raise ValueError(
            f"Invalid CPU format: '{cpu}'. "
            "Must be a number (e.g., '1', '0.5') or millicores (e.g., '1000m')."
        )
    return cpu


def _validate_memory(memory: str) -> str:
    """Validate memory allocation format."""
    if not _MEMORY_PATTERN.match(memory):
        raise ValueError(
            f"Invalid memory format: '{memory}'. "
            "Must be a number followed by Mi, Gi, M, G, Ki, or K (e.g., '512Mi', '1Gi')."
        )
    return memory


def _validate_env_vars(env_vars: list[str]) -> list[str]:
    """Validate environment variable format (KEY=VALUE)."""
    for env_var in env_vars:
        if not _ENV_VAR_PATTERN.match(env_var):
            raise ValueError(
                f"Invalid environment variable format: '{env_var}'. "
                "Must be KEY=VALUE where KEY starts with a letter or underscore."
            )
    return env_vars


def _validate_service_account(service_account: str) -> str:
    """Validate GCP service account email format."""
    if service_account and not _SERVICE_ACCOUNT_PATTERN.match(service_account):
        raise ValueError(
            f"Invalid service account email: '{service_account}'. "
            "Must be in format: name@project.iam.gserviceaccount.com"
        )
    return service_account


def _validate_log_filter(log_filter: str) -> str:
    """Validate log filter to prevent injection."""
    if log_filter and not _LOG_FILTER_PATTERN.match(log_filter):
        raise ValueError(
            f"Invalid log filter: '{log_filter}'. Contains unsafe characters."
        )
    return log_filter


def _validate_port(port: int, field: str = "port") -> int:
    """Validate port number is within valid range."""
    if port < 1 or port > 65535:
        raise ValueError(f"Invalid {field}: {port}. Must be between 1 and 65535.")
    return port


def _validate_positive_int(value: int, field: str) -> int:
    """Validate that an integer is non-negative."""
    if value < 0:
        raise ValueError(f"Invalid {field}: {value}. Must be non-negative.")
    return value


@object_type
class CloudRunService:
    """Cloud Run service operations."""

    @function
    async def deploy(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        image: Annotated[str, Doc("Container image URI")],
        service_name: Annotated[str, Doc("Service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        port: Annotated[int, Doc("Container port")] = 8080,
        cpu: Annotated[str, Doc("CPU allocation")] = "1",
        memory: Annotated[str, Doc("Memory allocation")] = "512Mi",
        min_instances: Annotated[int, Doc("Minimum instances")] = 0,
        max_instances: Annotated[int, Doc("Maximum instances")] = 10,
        concurrency: Annotated[int, Doc("Max concurrent requests")] = 80,
        timeout: Annotated[str, Doc("Request timeout")] = "300s",
        allow_unauthenticated: Annotated[bool, Doc("Allow public access")] = False,
        env_vars: Annotated[list[str], Doc("Environment variables (KEY=VALUE)")] = [],
        secrets: Annotated[list[str], Doc("Secrets (NAME=VERSION)")] = [],
        vpc_connector: Annotated[str, Doc("VPC connector")] = "",
        service_account: Annotated[str, Doc("Service account email")] = "",
        cpu_boost: Annotated[bool, Doc("Enable CPU boost during startup")] = False,
    ) -> str:
        """Deploy a Cloud Run service."""
        # Validate all inputs
        _validate_cloud_run_name(service_name, "service_name")
        _validate_region(region)
        _validate_image(image)
        _validate_port(port)
        _validate_cpu(cpu)
        _validate_memory(memory)
        _validate_positive_int(min_instances, "min_instances")
        _validate_positive_int(max_instances, "max_instances")
        _validate_positive_int(concurrency, "concurrency")
        _validate_timeout(timeout)
        _validate_env_vars(env_vars)
        _validate_service_account(service_account)

        cmd = [
            "gcloud", "run", "deploy", service_name,
            "--image", image, "--region", region, "--port", str(port),
            "--cpu", cpu, "--memory", memory,
            "--min-instances", str(min_instances), "--max-instances", str(max_instances),
            "--concurrency", str(concurrency), "--timeout", timeout, "--quiet",
        ]

        cmd.append("--allow-unauthenticated" if allow_unauthenticated else "--no-allow-unauthenticated")
        if env_vars:
            cmd.extend(["--set-env-vars", ",".join(env_vars)])
        if secrets:
            cmd.extend(["--set-secrets", ",".join(secrets)])
        if vpc_connector:
            cmd.extend(["--vpc-connector", vpc_connector])
        if service_account:
            cmd.extend(["--service-account", service_account])
        if cpu_boost:
            cmd.append("--cpu-boost")

        return await gcloud.with_exec(cmd).stdout()

    @function
    async def delete(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        service_name: Annotated[str, Doc("Service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Delete a Cloud Run service."""
        _validate_cloud_run_name(service_name, "service_name")
        _validate_region(region)

        return await gcloud.with_exec([
            "gcloud", "run", "services", "delete", service_name, "--region", region, "--quiet",
        ]).stdout()

    @function
    async def get_url(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        service_name: Annotated[str, Doc("Service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Get the URL of a deployed service."""
        _validate_cloud_run_name(service_name, "service_name")
        _validate_region(region)

        output = await gcloud.with_exec([
            "gcloud", "run", "services", "describe", service_name,
            "--region", region, "--format", "value(status.url)",
        ]).stdout()
        return output.strip()

    @function
    async def exists(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        service_name: Annotated[str, Doc("Service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> bool:
        """Check if a Cloud Run service exists."""
        # Validate inputs to prevent command injection
        _validate_cloud_run_name(service_name, "service_name")
        _validate_region(region)

        try:
            result = await gcloud.with_exec([
                "gcloud", "run", "services", "describe", service_name,
                "--region", region, "--format", "value(metadata.name)",
            ]).stdout()
            return bool(result.strip())
        except dagger.ExecError:
            return False

    @function
    async def get_logs(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        service_name: Annotated[str, Doc("Service name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        limit: Annotated[int, Doc("Maximum number of log entries")] = 50,
        log_filter: Annotated[str, Doc("Additional log filter (e.g., 'severity>=ERROR')")] = "",
    ) -> str:
        """Read logs from a Cloud Run service."""
        _validate_cloud_run_name(service_name, "service_name")
        _validate_region(region)
        _validate_positive_int(limit, "limit")
        _validate_log_filter(log_filter)

        cmd = [
            "gcloud", "run", "services", "logs", "read", service_name,
            "--region", region, "--limit", str(limit),
        ]
        if log_filter:
            cmd.extend(["--log-filter", log_filter])
        return await gcloud.with_exec(cmd).stdout()


@object_type
class CloudRunJob:
    """Cloud Run job operations."""

    @function
    async def deploy(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        image: Annotated[str, Doc("Container image URI")],
        job_name: Annotated[str, Doc("Job name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        cpu: Annotated[str, Doc("CPU allocation")] = "1",
        memory: Annotated[str, Doc("Memory allocation")] = "512Mi",
        max_retries: Annotated[int, Doc("Max retry attempts")] = 0,
        timeout: Annotated[str, Doc("Task timeout")] = "600s",
        parallelism: Annotated[int, Doc("Number of parallel tasks")] = 1,
        tasks: Annotated[int, Doc("Number of tasks to execute")] = 1,
        env_vars: Annotated[list[str], Doc("Environment variables (KEY=VALUE)")] = [],
        secrets: Annotated[list[str], Doc("Secrets (NAME=VERSION)")] = [],
        vpc_connector: Annotated[str, Doc("VPC connector")] = "",
        service_account: Annotated[str, Doc("Service account email")] = "",
        command: Annotated[list[str], Doc("Override container command")] = [],
        args: Annotated[list[str], Doc("Override container args")] = [],
    ) -> str:
        """Deploy a Cloud Run job."""
        # Validate all inputs
        _validate_cloud_run_name(job_name, "job_name")
        _validate_region(region)
        _validate_image(image)
        _validate_cpu(cpu)
        _validate_memory(memory)
        _validate_positive_int(max_retries, "max_retries")
        _validate_timeout(timeout)
        _validate_positive_int(parallelism, "parallelism")
        _validate_positive_int(tasks, "tasks")
        _validate_env_vars(env_vars)
        _validate_service_account(service_account)

        cmd = [
            "gcloud", "run", "jobs", "deploy", job_name,
            "--image", image, "--region", region, "--cpu", cpu, "--memory", memory,
            "--max-retries", str(max_retries), "--task-timeout", timeout,
            "--parallelism", str(parallelism), "--tasks", str(tasks), "--quiet",
        ]

        if env_vars:
            cmd.extend(["--set-env-vars", ",".join(env_vars)])
        if secrets:
            cmd.extend(["--set-secrets", ",".join(secrets)])
        if vpc_connector:
            cmd.extend(["--vpc-connector", vpc_connector])
        if service_account:
            cmd.extend(["--service-account", service_account])
        if command:
            cmd.extend(["--command", ",".join(command)])
        if args:
            cmd.extend(["--args", ",".join(args)])

        return await gcloud.with_exec(cmd).stdout()

    @function
    async def execute(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        job_name: Annotated[str, Doc("Job name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        wait: Annotated[bool, Doc("Wait for execution to complete")] = True,
    ) -> str:
        """Execute a Cloud Run job."""
        _validate_cloud_run_name(job_name, "job_name")
        _validate_region(region)

        cmd = ["gcloud", "run", "jobs", "execute", job_name, "--region", region, "--quiet"]
        if wait:
            cmd.append("--wait")
        return await gcloud.with_exec(cmd).stdout()

    @function
    async def delete(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        job_name: Annotated[str, Doc("Job name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
    ) -> str:
        """Delete a Cloud Run job."""
        _validate_cloud_run_name(job_name, "job_name")
        _validate_region(region)

        return await gcloud.with_exec([
            "gcloud", "run", "jobs", "delete", job_name, "--region", region, "--quiet",
        ]).stdout()

    @function
    async def get_logs(
        self,
        gcloud: Annotated[dagger.Container, Doc("Authenticated gcloud container")],
        job_name: Annotated[str, Doc("Job name")],
        region: Annotated[str, Doc("GCP region")] = "us-central1",
        limit: Annotated[int, Doc("Maximum number of log entries")] = 50,
        log_filter: Annotated[str, Doc("Additional log filter (e.g., 'severity>=ERROR')")] = "",
    ) -> str:
        """Read logs from a Cloud Run job."""
        _validate_cloud_run_name(job_name, "job_name")
        _validate_region(region)
        _validate_positive_int(limit, "limit")
        _validate_log_filter(log_filter)

        cmd = [
            "gcloud", "run", "jobs", "logs", "read", job_name,
            "--region", region, "--limit", str(limit),
        ]
        if log_filter:
            cmd.extend(["--log-filter", log_filter])
        return await gcloud.with_exec(cmd).stdout()


@object_type
class GcpCloudRun:
    """Google Cloud Run deployment utilities."""

    @function
    def service(self) -> CloudRunService:
        """Access Cloud Run service operations."""
        return CloudRunService()

    @function
    def job(self) -> CloudRunJob:
        """Access Cloud Run job operations."""
        return CloudRunJob()
