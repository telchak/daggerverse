"""Health Check Module - Simple, reusable container health checking."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class HealthCheck:
    """Container health checking using Dagger service bindings."""

    @function
    async def http(
        self,
        container: Annotated[dagger.Container, Doc("Container to check")],
        port: Annotated[int, Doc("Port number")] = 8080,
        path: Annotated[str, Doc("HTTP path")] = "/health",
        timeout: Annotated[int, Doc("Timeout in seconds")] = 60,
    ) -> dagger.Container:
        """HTTP health check using curl. Returns container if healthy."""
        service = container.with_exposed_port(port).as_service()

        await (
            dag.container()
            .from_("curlimages/curl:latest")
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
        port: Annotated[int, Doc("Port number")] = 8080,
        timeout: Annotated[int, Doc("Timeout in seconds")] = 60,
    ) -> dagger.Container:
        """TCP port check using netcat. Returns container if port is open."""
        service = container.with_exposed_port(port).as_service()

        await (
            dag.container()
            .from_("alpine:latest")
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
        port: Annotated[int, Doc("Port number")],
        endpoint: Annotated[str, Doc("HTTP endpoint (empty for TCP only)")] = "",
        timeout: Annotated[int, Doc("Timeout in seconds")] = 60,
    ) -> dagger.Container:
        """Generic readiness check. Uses HTTP if endpoint provided, TCP otherwise."""
        if endpoint:
            return await self.http(container, port, endpoint, timeout)
        return await self.tcp(container, port, timeout)
