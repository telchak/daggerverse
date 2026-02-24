// Examples for using the gcp-artifact-registry Dagger module in Go.
package main

import (
	"context"
	"dagger/gcp-artifact-registry-examples/internal/dagger"
	"fmt"
)

type GcpArtifactRegistryExamples struct{}

// Example: Build and publish a container to Artifact Registry.
func (m *GcpArtifactRegistryExamples) PublishContainer(
	ctx context.Context,
	// Source directory with Dockerfile
	source *dagger.Directory,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// GCP project ID
	projectID string,
	// Repository name
	repository string,
	// Image name
	imageName string,
	// +optional
	// +default="latest"
	tag string,
) (string, error) {
	container := source.DockerBuild()

	imageRef, err := dag.GcpArtifactRegistry().Publish(
		ctx,
		container,
		projectID,
		repository,
		imageName,
		dagger.GcpArtifactRegistryPublishOpts{
			Tag:    tag,
			Gcloud: gcloud,
		},
	)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Published: %s", imageRef), nil
}

// Example: List all images in an Artifact Registry repository.
func (m *GcpArtifactRegistryExamples) ListRepositoryImages(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// GCP project ID
	projectID string,
	// Repository name
	repository string,
) (string, error) {
	return dag.GcpArtifactRegistry().ListImages(ctx, gcloud, projectID, repository)
}
