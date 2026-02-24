// Examples for using the Monty (Python Agent) Dagger module in Go.
//
// Demonstrates local development and CI/CD use cases.
package main

import (
	"context"
	"dagger/monty-examples/internal/dagger"
)

type MontyExamples struct{}

// Example: Use Monty as a local coding assistant.
func (m *MontyExamples) AssistLocal(
	// Python project source directory
	source *dagger.Directory,
	// +optional
	// +default="Analyze this project and describe its architecture."
	assignment string,
) *dagger.Directory {
	return dag.Monty(dagger.MontyOpts{Source: source}).Assist(dagger.MontyAssistOpts{
		Assignment: assignment,
	})
}

// Example: Review your Python code locally.
func (m *MontyExamples) ReviewLocal(
	ctx context.Context,
	// Python project source directory
	source *dagger.Directory,
	// +optional
	focus string,
) (string, error) {
	return dag.Monty(dagger.MontyOpts{Source: source}).Review(ctx, dagger.MontyReviewOpts{
		Focus: focus,
	})
}

// Example: Read a GitHub issue, implement it, and create a PR.
func (m *MontyExamples) DevelopGithubIssue(
	ctx context.Context,
	// Python project source directory
	source *dagger.Directory,
	// GitHub token with repo + PR permissions
	githubToken *dagger.Secret,
	// GitHub issue number
	issueId int,
	// GitHub repository URL
	repository string,
) (string, error) {
	return dag.Monty(dagger.MontyOpts{Source: source}).DevelopGithubIssue(ctx, dagger.MontyDevelopGithubIssueOpts{
		GithubToken: githubToken,
		IssueId:     issueId,
		Repository:  repository,
	})
}

// Example: Review a PR diff in CI.
func (m *MontyExamples) CiReviewPr(
	ctx context.Context,
	// Python project source directory
	source *dagger.Directory,
	// Git diff from the PR
	diff string,
) (string, error) {
	return dag.Monty(dagger.MontyOpts{Source: source}).Review(ctx, dagger.MontyReviewOpts{
		Diff:  diff,
		Focus: "Python best practices, type safety, and performance",
	})
}
