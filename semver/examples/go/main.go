// Examples for using the semver Dagger module in Go.
package main

import (
	"context"
	"dagger/semver-examples/internal/dagger"
	"fmt"
)

type SemverExamples struct{}

// Example: Calculate the next version based on conventional commits.
func (m *SemverExamples) CalculateNextVersion(
	ctx context.Context,
	// Git repository
	source *dagger.Directory,
) (string, error) {
	nextVersion, err := dag.Semver().Next(ctx, dagger.SemverNextOpts{Source: source})
	if err != nil {
		return "", err
	}

	current, err := dag.Semver().Current(ctx, dagger.SemverCurrentOpts{Source: source})
	if err != nil {
		return "", err
	}

	bump, err := dag.Semver().BumpType(ctx, dagger.SemverBumpTypeOpts{Source: source})
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Current: %s -> Next: %s (bump: %s)", current, nextVersion, bump), nil
}

// Example: Release a specific module in a monorepo.
func (m *SemverExamples) MonorepoRelease(
	ctx context.Context,
	// Git repository
	source *dagger.Directory,
	// Module name (tag prefix)
	moduleName string,
	// GitHub token
	githubToken *dagger.Secret,
) (string, error) {
	tagPrefix := moduleName + "/"

	result, err := dag.Semver().Release(ctx, dagger.SemverReleaseOpts{
		Source:      source,
		GithubToken: githubToken,
		TagPrefix:   tagPrefix,
	})
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Released %s: %s", moduleName, result), nil
}

// Example: Check what files changed since last release.
func (m *SemverExamples) CheckChanges(
	ctx context.Context,
	// Git repository
	source *dagger.Directory,
	// +optional
	tagPrefix string,
) (string, error) {
	changed, err := dag.Semver().ChangedPaths(ctx, dagger.SemverChangedPathsOpts{
		Source:    source,
		TagPrefix: tagPrefix,
	})
	if err != nil {
		return "", err
	}

	if changed == "" {
		return "No changes since last release", nil
	}

	return fmt.Sprintf("Changed files:\n%s", changed), nil
}
