"""Examples for using the dagger-mcp Dagger module."""

import dagger
from dagger import dag, function, object_type


@object_type
class DaggerMcpExamples:
    """Usage examples for the dagger-mcp module.

    Demonstrates how to wire the MCP server into AI agent pipelines.
    """

    @function
    def get_mcp_service(self) -> dagger.Service:
        """Example: Get the MCP server as a Dagger service.

        The service can be passed to any LLM that supports MCP:
          dagger call get-mcp-service
        """
        return dag.dagger_mcp().server()

    @function
    async def agent_with_schema_introspection(self) -> str:
        """Example: Build an LLM agent with Dagger schema introspection.

        The agent can use learn_schema, run_query, learn_sdk, and
        dagger_version tools to explore the Dagger API.

          dagger call agent-with-schema-introspection
        """
        llm = (
            dag.llm()
            .with_mcp_server("dagger", dag.dagger_mcp().server())
            .with_prompt(
                "Use the dagger_version tool to get the engine version, "
                "then use learn_schema to introspect the 'Query' type. "
                "Summarize what top-level fields are available."
            )
        )
        return await llm.last_reply()

    @function
    async def agent_with_sdk_knowledge(self) -> str:
        """Example: Ask an LLM for SDK-specific Dagger code.

        The agent uses learn_sdk to get translation guidance, then
        generates SDK-specific code from the schema.

          dagger call agent-with-sdk-knowledge
        """
        llm = (
            dag.llm()
            .with_mcp_server("dagger", dag.dagger_mcp().server())
            .with_prompt(
                "Use learn_sdk to get Python SDK guidance. Then use "
                "learn_schema to look up the 'Container' type. Write "
                "a short Python Dagger module that builds an Alpine "
                "container and runs 'echo hello'."
            )
        )
        return await llm.last_reply()
