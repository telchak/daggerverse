"""Tests for health-check module."""

from dagger import dag


async def test_health_check() -> str:
    """Run health-check module tests."""
    results = []
    hc = dag.health_check()

    # Test HTTP check with nginx
    nginx = dag.container().from_("nginx:alpine")
    await hc.http(nginx, port=80, path="/")
    results.append("PASS: HTTP check with nginx")

    # Test TCP check with redis
    redis = dag.container().from_("redis:alpine")
    await hc.tcp(redis, port=6379)
    results.append("PASS: TCP check with redis")

    # Test exec check
    alpine = dag.container().from_("alpine:latest")
    await hc.exec(alpine, command=["echo", "healthy"])
    results.append("PASS: Exec check")

    return "\n".join(results)
