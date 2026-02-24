// Examples for using the Angie (Angular Agent) Dagger module in Go.
//
// Demonstrates local development and CI/CD use cases.
package main

import (
	"context"
	"dagger/angie-examples/internal/dagger"
)

type AngieExamples struct{}

// Example: Use Angie as a local coding assistant.
func (m *AngieExamples) AssistLocal(
	// Angular project source directory
	source *dagger.Directory,
	// +optional
	// +default="Analyze this project and describe its architecture."
	assignment string,
) *dagger.Directory {
	return dag.Angie(dagger.AngieOpts{Source: source}).Assist(dagger.AngieAssistOpts{
		Assignment: assignment,
	})
}

// Example: Review your Angular code locally.
func (m *AngieExamples) ReviewLocal(
	ctx context.Context,
	// Angular project source directory
	source *dagger.Directory,
	// +optional
	focus string,
) (string, error) {
	return dag.Angie(dagger.AngieOpts{Source: source}).Review(ctx, dagger.AngieReviewOpts{
		Focus: focus,
	})
}

// Example: Read a GitHub issue, implement it, and create a PR.
func (m *AngieExamples) DevelopGithubIssue(
	ctx context.Context,
	// Angular project source directory
	source *dagger.Directory,
	// GitHub token with repo + PR permissions
	githubToken *dagger.Secret,
	// GitHub issue number
	issueId int,
	// GitHub repository URL
	repository string,
) (string, error) {
	return dag.Angie(dagger.AngieOpts{Source: source}).DevelopGithubIssue(ctx, dagger.AngieDevelopGithubIssueOpts{
		GithubToken: githubToken,
		IssueId:     issueId,
		Repository:  repository,
	})
}

// Example: Review a PR diff in CI.
func (m *AngieExamples) CiReviewPr(
	ctx context.Context,
	// Angular project source directory
	source *dagger.Directory,
	// Git diff from the PR
	diff string,
) (string, error) {
	return dag.Angie(dagger.AngieOpts{Source: source}).Review(ctx, dagger.AngieReviewOpts{
		Diff:  diff,
		Focus: "Angular best practices, type safety, and performance",
	})
}
