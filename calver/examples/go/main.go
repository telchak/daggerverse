// Example using CalVer module to version and publish container releases.
package main

import (
	"context"
	"dagger/calver-examples/internal/dagger"
	"fmt"
)

type CalverExamples struct{}

// Build, version, and publish container with auto-incremented CalVer tag.
//
// This example demonstrates:
//   - Auto-incrementing MICRO from git tags (v.2025.11.0 -> v.2025.11.1)
//   - Building a container
//   - Publishing with CalVer tag
//   - Tagging and pushing to git
func (m *CalverExamples) Release(
	ctx context.Context,
	// Source directory with git
	source *dagger.Directory,
	// +optional
	// +default="ghcr.io/myorg/myapp"
	registry string,
) (string, error) {
	// Generate auto-incremented version from git history
	version, err := dag.Calver().Generate(ctx, dagger.CalverGenerateOpts{
		Format: "v.YYYY.MM.MICRO",
		Source: source,
	})
	if err != nil {
		return "", err
	}

	// Build and publish container
	container := source.DockerBuild()
	ref, err := container.Publish(ctx, fmt.Sprintf("%s:%s", registry, version))
	if err != nil {
		return "", err
	}

	// Tag git commit
	_, err = dag.Container().
		From("alpine/git:latest").
		WithMountedDirectory("/repo", source).
		WithWorkdir("/repo").
		WithExec([]string{"git", "tag", version}).
		WithExec([]string{"git", "push", "origin", version}).
		Sync(ctx)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Released %s -> %s", version, ref), nil
}
