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
    def container(self) -> dagger.Container:
        """The container the MCP server runs in, with `python main.py` as its default command.

        Run it as a service with `server`, or start the server yourself on
        stdio (e.g. one request per exec). Calls to the engine go through
        Dagger-in-Dagger, which the 1.0 API enables by default.
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
        )

    @function
    def server(self) -> dagger.Service:
        """The MCP server as a Dagger service.

        Provides tools: learn_schema, run_query, learn_sdk, dagger_version.
        The server reaches the Dagger engine through Dagger-in-Dagger, which
        the 1.0 API enables for every service by default.
        """
        return self.container().as_service()
