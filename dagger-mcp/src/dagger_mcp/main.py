"""MCP server for Dagger engine introspection."""

import dagger
from dagger import dag, function, object_type


@object_type
class DaggerMcp:
    """MCP server for Dagger engine introspection.

    Provides tools for learning the Dagger GraphQL schema, running queries,
    and getting SDK-specific guidance for Python, TypeScript, and Go.
    """

    @function
    def server(self) -> dagger.Service:
        """The MCP server as a Dagger service.

        Provides tools: learn_schema, run_query, learn_sdk, dagger_version.
        Requires privileged nesting to access the Dagger engine.
        """
        return (
            dag.container()
            .from_("python:3.13-slim")
            # TEMPORARY PIN. mcp 2.0.0 (released 2026-07-28) removed
            # mcp.server.fastmcp, which server/main.py imports. Unpinned, this
            # resolved to 2.0.0 and the server died at import — and because the
            # LLM then waits forever for a service that will never answer, the
            # failure surfaced as a 20-minute step timeout with no traceback.
            # Remove this pin once the server is ported to the 2.0 API.
            .with_exec(["pip", "install", "--no-cache-dir", "mcp<2", "httpx"])
            .with_directory(
                "/app",
                dag.current_module().source().directory("src/dagger_mcp/server"),
            )
            .with_workdir("/app")
            .with_default_args(["python", "main.py"])
            .as_service(experimental_privileged_nesting=True)
        )
