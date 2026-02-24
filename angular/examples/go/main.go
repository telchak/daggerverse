// Examples for using the angular Dagger module in Go.
package main

import (
	"context"
	"dagger/angular-examples/internal/dagger"
	"fmt"
)

const exampleRepo = "https://github.com/realworld-apps/angular-realworld-example-app.git"

type AngularExamples struct{}

// Example: Build an Angular project for production.
func (m *AngularExamples) BuildProject(
	ctx context.Context,
	// +optional
	source *dagger.Directory,
) (string, error) {
	if source == nil {
		source = dag.Git(exampleRepo).Branch("main").Tree()
	}

	dist, err := dag.Angular().Build(ctx, source, dagger.AngularBuildOpts{
		Configuration: "production",
	})
	if err != nil {
		return "", err
	}

	entries, err := dist.Entries(ctx)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Build succeeded: %d files in dist/", len(entries)), nil
}

// Example: Lint an Angular project.
func (m *AngularExamples) LintProject(
	ctx context.Context,
	// +optional
	source *dagger.Directory,
) (string, error) {
	if source == nil {
		source = dag.Git(exampleRepo).Branch("main").Tree()
	}

	output, err := dag.Angular().Lint(ctx, source)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Lint output:\n%s", output), nil
}

// Example: Install dependencies and verify node_modules.
func (m *AngularExamples) InstallDeps(
	ctx context.Context,
	// +optional
	source *dagger.Directory,
) (string, error) {
	if source == nil {
		source = dag.Git(exampleRepo).Branch("main").Tree()
	}

	result := dag.Angular().Install(source)
	entries, err := result.Entries(ctx)
	if err != nil {
		return "", err
	}

	hasModules := false
	for _, e := range entries {
		if e == "node_modules" {
			hasModules = true
			break
		}
	}

	return fmt.Sprintf("Install succeeded: node_modules=%v, %d entries", hasModules, len(entries)), nil
}
