/**
 * Examples for using the dagger-mcp Dagger module in TypeScript.
 *
 * Demonstrates how to wire the MCP server into AI agent pipelines.
 */
import { dag, Service, object, func } from "@dagger.io/dagger"

@object()
export class DaggerMcpExamples {
  /**
   * Example: Get the MCP server as a Dagger service.
   */
  @func()
  getMcpService(): Service {
    return dag.daggerMcp().server()
  }

  /**
   * Example: Build an LLM agent with Dagger schema introspection.
   */
  @func()
  async agentWithSchemaIntrospection(): Promise<string> {
    const llm = dag
      .llm()
      .withMcpServer("dagger", dag.daggerMcp().server())
      .withPrompt(
        "Use the dagger_version tool to get the engine version, " +
          "then use learn_schema to introspect the 'Query' type. " +
          "Summarize what top-level fields are available.",
      )
    return llm.lastReply()
  }

  /**
   * Example: Ask an LLM for SDK-specific Dagger code.
   */
  @func()
  async agentWithSdkKnowledge(): Promise<string> {
    const llm = dag
      .llm()
      .withMcpServer("dagger", dag.daggerMcp().server())
      .withPrompt(
        "Use learn_sdk to get Python SDK guidance. Then use " +
          "learn_schema to look up the 'Container' type. Write " +
          "a short Python Dagger module that builds an Alpine " +
          "container and runs 'echo hello'.",
      )
    return llm.lastReply()
  }
}
