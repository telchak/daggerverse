// Examples for using the python-build Dagger module in Go.
package main

import (
	"context"
	"dagger/python-build-examples/internal/dagger"
	"fmt"
)

const exampleRepo = "https://github.com/nsidnev/fastapi-realworld-example-app.git"

type PythonBuildExamples struct{}

// Example: Build a Python project.
func (m *PythonBuildExamples) BuildProject(
	ctx context.Context,
	// +optional
	source *dagger.Directory,
) (string, error) {
	if source == nil {
		source = dag.Git(exampleRepo).Branch("master").Tree()
	}

	result, err := dag.PythonBuild().Build(ctx, source)
	if err != nil {
		return "", err
	}

	entries, err := result.Entries(ctx)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Build succeeded: %d entries", len(entries)), nil
}

// Example: Lint a Python project with ruff.
func (m *PythonBuildExamples) LintProject(
	ctx context.Context,
	// +optional
	source *dagger.Directory,
) (string, error) {
	if source == nil {
		source = dag.Git(exampleRepo).Branch("master").Tree()
	}

	output, err := dag.PythonBuild().Lint(ctx, source, dagger.PythonBuildLintOpts{
		Tool: "ruff",
	})
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Lint output:\n%s", output), nil
}

// Example: Install dependencies.
func (m *PythonBuildExamples) InstallDeps(
	ctx context.Context,
	// +optional
	source *dagger.Directory,
) (string, error) {
	if source == nil {
		source = dag.Git(exampleRepo).Branch("master").Tree()
	}

	result, err := dag.PythonBuild().Install(ctx, source)
	if err != nil {
		return "", err
	}

	entries, err := result.Entries(ctx)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Install succeeded: %d entries", len(entries)), nil
}
