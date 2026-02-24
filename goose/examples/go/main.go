// Examples for using the Goose (GCP Agent) Dagger module in Go.
package main

import (
	"context"
	"dagger/goose-examples/internal/dagger"
)

type GooseExamples struct{}

// Example: Deploy a public hello-world service to Cloud Run.
func (m *GooseExamples) DeployCloudRunService(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// GCP project ID
	projectId string,
	// Service name
	serviceName string,
	// +optional
	// +default="us-central1"
	region string,
) (string, error) {
	return dag.Goose(dagger.GooseOpts{
		Gcloud:    gcloud,
		ProjectId: projectId,
		Region:    region,
	}).Deploy(ctx, dagger.GooseDeployOpts{
		Assignment:  "Deploy gcr.io/google-samples/hello-app:1.0 as a public service with allow unauthenticated access",
		ServiceName: serviceName,
	})
}

// Example: Troubleshoot a Cloud Run service returning errors.
func (m *GooseExamples) TroubleshootService(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// Service name to troubleshoot
	serviceName string,
	// GCP project ID
	projectId string,
	// +optional
	// +default="us-central1"
	region string,
) (string, error) {
	return dag.Goose(dagger.GooseOpts{
		Gcloud:    gcloud,
		ProjectId: projectId,
		Region:    region,
	}).Troubleshoot(ctx, serviceName, dagger.GooseTroubleshootOpts{
		Issue: "Service is returning 503 errors and seems to be crashing on startup",
	})
}

// Example: List all Cloud Run services and report their status.
func (m *GooseExamples) AssistListServices(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// GCP project ID
	projectId string,
	// +optional
	// +default="us-central1"
	region string,
) (string, error) {
	return dag.Goose(dagger.GooseOpts{
		Gcloud:    gcloud,
		ProjectId: projectId,
		Region:    region,
	}).Assist(ctx, dagger.GooseAssistOpts{
		Assignment: "List all Cloud Run services and report their status",
	})
}

// Example: Review deployment configs for best practices.
func (m *GooseExamples) ReviewConfigs(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// GCP project ID
	projectId string,
	// Source directory with deployment configs
	source *dagger.Directory,
	// +optional
	// +default="us-central1"
	region string,
) (string, error) {
	return dag.Goose(dagger.GooseOpts{
		Gcloud:    gcloud,
		ProjectId: projectId,
		Region:    region,
	}).Review(ctx, dagger.GooseReviewOpts{
		Source: source,
		Focus:  "security and performance",
	})
}
