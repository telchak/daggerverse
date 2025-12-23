"""Examples for using the health-check Dagger module."""

from typing import Annotated

import dagger
from dagger import Doc, dag, function, object_type


@object_type
class HealthCheckExamples:
    """Usage examples for health-check module."""

    @function
    async def check_http_service(self) -> str:
        """Example: Health check an HTTP service (nginx)."""
        nginx = dag.container().from_("nginx:alpine")

        # Check if nginx is healthy on port 80
        healthy = await dag.health_check().http(nginx, port=80, path="/")

        return "✓ Nginx is healthy and responding on port 80"

    @function
    async def check_tcp_port(self) -> str:
        """Example: Check if a TCP port is accepting connections (Redis)."""
        redis = dag.container().from_("redis:alpine")

        # Check if Redis port 6379 is open
        healthy = await dag.health_check().tcp(redis, port=6379)

        return "✓ Redis port 6379 is open and accepting connections"

    @function
    async def check_with_custom_endpoint(self) -> str:
        """Example: Check a custom health endpoint with timeout."""
        # Simulate an API service
        api = (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "flask"])
            .with_new_file(
                "/app.py",
                contents='from flask import Flask\napp = Flask(__name__)\n@app.route("/api/health")\ndef health(): return "OK"\nif __name__ == "__main__": app.run(host="0.0.0.0", port=5000)',
            )
            .with_exec(["python", "/app.py"], use_entrypoint=True)
        )

        # Check custom health endpoint
        healthy = await dag.health_check().http(
            api, port=5000, path="/api/health", timeout=30
        )

        return "✓ API service health endpoint is responding"

    @function
    async def check_with_exec(self) -> str:
        """Example: Health check using a command execution."""
        postgres = dag.container().from_("postgres:alpine").with_env_variable(
            "POSTGRES_PASSWORD", "secret"
        )

        # Check PostgreSQL using pg_isready command
        healthy = await dag.health_check().exec(
            postgres, command=["pg_isready", "-U", "postgres"]
        )

        return "✓ PostgreSQL is ready to accept connections"

    @function
    async def use_ready_helper(self) -> str:
        """Example: Use the ready() convenience method."""
        # HTTP check (with endpoint)
        nginx = dag.container().from_("nginx:alpine")
        healthy_http = await dag.health_check().ready(
            nginx, port=80, endpoint="/", timeout=30
        )

        # TCP check (without endpoint)
        redis = dag.container().from_("redis:alpine")
        healthy_tcp = await dag.health_check().ready(redis, port=6379, timeout=30)

        return "✓ Both services passed readiness checks"

    @function
    async def chain_with_other_operations(self) -> str:
        """Example: Chain health check with other container operations."""
        # Start a service, check it's healthy, then use it
        api = (
            dag.container()
            .from_("nginx:alpine")
            .with_new_file("/usr/share/nginx/html/index.html", contents="Hello!")
        )

        # Health check returns the original container, so you can chain operations
        result = await (
            dag.health_check()
            .http(api, port=80)
            .with_exec(["cat", "/usr/share/nginx/html/index.html"])
            .stdout()
        )

        return f"✓ Service is healthy. Content: {result.strip()}"
