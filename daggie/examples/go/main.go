// Examples for using the Daggie (Dagger CI Agent) Dagger module in Go.
//
// Demonstrates local development and CI/CD use cases.
package main

import (
	"context"
	"dagger/daggie-examples/internal/dagger"
)

type DaggieExamples struct{}

// Example: Use Daggie as a local coding assistant.
func (m *DaggieExamples) AssistLocal(
	// Project source directory
	source *dagger.Directory,
	// +optional
	// +default="Analyze this project and create a Dagger module for building it."
	assignment string,
) *dagger.Directory {
	return dag.Daggie(dagger.DaggieOpts{Source: source}).Assist(dagger.DaggieAssistOpts{
		Assignment: assignment,
	})
}

// Example: Ask Daggie to explain a Dagger concept.
func (m *DaggieExamples) ExplainConcept(
	ctx context.Context,
	// +optional
	// +default="What is a Dagger module and how does dagger.json configure it?"
	question string,
) (string, error) {
	return dag.Daggie().Explain(ctx, dagger.DaggieExplainOpts{
		Question: question,
	})
}

// Example: Debug a Dagger pipeline error.
func (m *DaggieExamples) DebugPipeline(
	// Project source with the broken module
	source *dagger.Directory,
	// Pipeline error output
	errorOutput string,
) *dagger.Directory {
	return dag.Daggie(dagger.DaggieOpts{Source: source}).Debug(dagger.DaggieDebugOpts{
		ErrorOutput: errorOutput,
	})
}

// Example: Review Dagger module code.
func (m *DaggieExamples) ReviewLocal(
	ctx context.Context,
	// Project source directory
	source *dagger.Directory,
	// +optional
	focus string,
) (string, error) {
	return dag.Daggie(dagger.DaggieOpts{Source: source}).Review(ctx, dagger.DaggieReviewOpts{
		Focus: focus,
	})
}

// Example: Read a GitHub issue, implement it, and create a PR.
func (m *DaggieExamples) DevelopGithubIssue(
	ctx context.Context,
	// Project source directory
	source *dagger.Directory,
	// GitHub token with repo + PR permissions
	githubToken *dagger.Secret,
	// GitHub issue number
	issueId int,
	// GitHub repository URL
	repository string,
) (string, error) {
	return dag.Daggie(dagger.DaggieOpts{Source: source}).DevelopGithubIssue(ctx, dagger.DaggieDevelopGithubIssueOpts{
		GithubToken: githubToken,
		IssueId:     issueId,
		Repository:  repository,
	})
}

// Example: Review a PR diff in CI.
func (m *DaggieExamples) CiReviewPr(
	ctx context.Context,
	// Project source directory
	source *dagger.Directory,
	// Git diff from the PR
	diff string,
) (string, error) {
	return dag.Daggie(dagger.DaggieOpts{Source: source}).Review(ctx, dagger.DaggieReviewOpts{
		Diff:  diff,
		Focus: "Dagger best practices, caching, and pipeline correctness",
	})
}
