"""Health Check Module - Simple, reusable container health checking."""

import re
from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


# Default container images
_CURL_IMAGE = "curlimages/curl:latest"
_ALPINE_IMAGE = "alpine:latest"

# Default port for HTTP services
_DEFAULT_PORT = 8080

# Default timeout for health checks (seconds)
_DEFAULT_TIMEOUT = 60

# Validation pattern for HTTP paths (must start with /, only safe URL characters)
_HTTP_PATH_PATTERN = re.compile(r'^/[a-zA-Z0-9._~:/?#\[\]@!$&\'()*+,;=-]*$')

# Port range constants
_MIN_PORT = 1
_MAX_PORT = 65535

# Timeout range constants (in seconds)
_MIN_TIMEOUT = 1
_MAX_TIMEOUT = 3600  # 1 hour max


def _validate_http_path(path: str) -> str:
    """Validate HTTP path to prevent shell injection."""
    if not path.startswith("/"):
        raise ValueError(f"Invalid HTTP path: '{path}'. Must start with '/'")
    if not _HTTP_PATH_PATTERN.match(path):
        raise ValueError(f"Invalid HTTP path: '{path}'. Contains unsafe characters.")
    return path


def _validate_port(port: int) -> int:
    """Validate port number is within valid range."""
    if not isinstance(port, int):
        raise ValueError(f"Port must be an integer, got {type(port).__name__}")
    if port < _MIN_PORT or port > _MAX_PORT:
        raise ValueError(
            f"Invalid port: {port}. Must be between {_MIN_PORT} and {_MAX_PORT}."
        )
    return port


def _validate_timeout(timeout: int) -> int:
    """Validate timeout is within reasonable range to prevent resource exhaustion."""
    if not isinstance(timeout, int):
        raise ValueError(f"Timeout must be an integer, got {type(timeout).__name__}")
    if timeout < _MIN_TIMEOUT or timeout > _MAX_TIMEOUT:
        raise ValueError(
            f"Invalid timeout: {timeout}. Must be between {_MIN_TIMEOUT} and {_MAX_TIMEOUT} seconds."
        )
    return timeout


@object_type
class HealthCheck:
    """Container health checking using Dagger service bindings."""

    @function
    async def http(
        self,
        container: Annotated[dagger.Container, Doc("Container to check")],
        port: Annotated[int, Doc("Port number (1-65535)")] = _DEFAULT_PORT,
        path: Annotated[str, Doc("HTTP path")] = "/health",
        timeout: Annotated[int, Doc("Timeout in seconds (1-3600)")] = _DEFAULT_TIMEOUT,
    ) -> dagger.Container:
        """HTTP health check using curl. Returns container if healthy."""
        # Validate inputs to prevent injection and resource exhaustion
        _validate_port(port)
        _validate_timeout(timeout)
        _validate_http_path(path)

        service = container.with_exposed_port(port).as_service()

        await (
            dag.container()
            .from_(_CURL_IMAGE)
            .with_service_binding("svc", service)
            .with_exec([
                "sh",
                "-c",
                f"timeout {timeout} sh -c 'until curl -sf http://svc:{port}{path}; do sleep 2; done'",
            ])
            .sync()
        )

        return container

    @function
    async def tcp(
        self,
        container: Annotated[dagger.Container, Doc("Container to check")],
        port: Annotated[int, Doc("Port number (1-65535)")] = _DEFAULT_PORT,
        timeout: Annotated[int, Doc("Timeout in seconds (1-3600)")] = _DEFAULT_TIMEOUT,
    ) -> dagger.Container:
        """TCP port check using netcat. Returns container if port is open."""
        # Validate inputs to prevent resource exhaustion
        _validate_port(port)
        _validate_timeout(timeout)

        service = container.with_exposed_port(port).as_service()

        await (
            dag.container()
            .from_(_ALPINE_IMAGE)
            .with_exec(["apk", "add", "--no-cache", "busybox-extras"])
            .with_service_binding("svc", service)
            .with_exec([
                "sh",
                "-c",
                f"timeout {timeout} sh -c 'until nc -zv svc {port} 2>&1; do sleep 2; done'",
            ])
            .sync()
        )

        return container

    @function
    async def exec(
        self,
        container: Annotated[dagger.Container, Doc("Container to check")],
        command: Annotated[list[str], Doc("Command to execute")],
    ) -> dagger.Container:
        """Execute command in container for health check. Returns container if command succeeds."""
        await container.with_exec(command).sync()
        return container

    @function
    async def ready(
        self,
        container: Annotated[dagger.Container, Doc("Container to check")],
        port: Annotated[int, Doc("Port number (1-65535)")],
        endpoint: Annotated[str, Doc("HTTP endpoint (empty for TCP only)")] = "",
        timeout: Annotated[int, Doc("Timeout in seconds (1-3600)")] = _DEFAULT_TIMEOUT,
    ) -> dagger.Container:
        """Generic readiness check. Uses HTTP if endpoint provided, TCP otherwise."""
        # Validation happens in the delegated methods (http/tcp)
        if endpoint:
            # Validation happens in self.http()
            return await self.http(container, port, endpoint, timeout)
        return await self.tcp(container, port, timeout)
