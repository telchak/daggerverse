// Examples for using the dagger-mcp Dagger module in Go.
package main

import (
	"context"
	"dagger/dagger-mcp-examples/internal/dagger"
)

type DaggerMcpExamples struct{}

// Example: Get the MCP server as a Dagger service.
func (m *DaggerMcpExamples) GetMcpService() *dagger.Service {
	return dag.DaggerMcp().Server()
}

// Example: Build an LLM agent with Dagger schema introspection.
func (m *DaggerMcpExamples) AgentWithSchemaIntrospection(ctx context.Context) (string, error) {
	llm := dag.Llm().
		WithMcpServer("dagger", dag.DaggerMcp().Server()).
		WithPrompt(
			"Use the dagger_version tool to get the engine version, " +
				"then use learn_schema to introspect the 'Query' type. " +
				"Summarize what top-level fields are available.",
		)
	return llm.LastReply(ctx)
}

// Example: Ask an LLM for SDK-specific Dagger code.
func (m *DaggerMcpExamples) AgentWithSdkKnowledge(ctx context.Context) (string, error) {
	llm := dag.Llm().
		WithMcpServer("dagger", dag.DaggerMcp().Server()).
		WithPrompt(
			"Use learn_sdk to get Python SDK guidance. Then use " +
				"learn_schema to look up the 'Container' type. Write " +
				"a short Python Dagger module that builds an Alpine " +
				"container and runs 'echo hello'.",
		)
	return llm.LastReply(ctx)
}
