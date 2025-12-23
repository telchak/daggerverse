// Examples for using the gcp-auth Dagger module in Go.
package main

import (
	"context"
	"dagger/gcp-auth-examples/internal/dagger"
	"fmt"
)

type GcpAuthExamples struct{}

// Example: Verify service account credentials and get email
func (m *GcpAuthExamples) VerifyServiceAccount(ctx context.Context, credentials *dagger.Secret) (string, error) {
	email, err := dag.GcpAuth().VerifyCredentials(ctx, credentials)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("✓ Authenticated as: %s", email), nil
}

// Example: List GCP projects using authenticated gcloud container
func (m *GcpAuthExamples) ListGcpProjects(
	ctx context.Context,
	credentials *dagger.Secret,
	projectID string,
) (string, error) {
	gcloud := dag.GcpAuth().GcloudContainer(credentials, projectID)

	return gcloud.WithExec([]string{
		"gcloud", "projects", "list", "--limit=5",
	}).Stdout(ctx)
}

// Example: Use Application Default Credentials from host (local dev)
func (m *GcpAuthExamples) UseAdcLocally(ctx context.Context, projectID string) (string, error) {
	gcloud := dag.GcpAuth().GcloudContainerFromHost(projectID)

	account, err := gcloud.WithExec([]string{
		"gcloud", "config", "get", "account",
	}).Stdout(ctx)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Using ADC account: %s", account), nil
}

// Example: Extract project ID from service account credentials
func (m *GcpAuthExamples) GetProjectFromCredentials(
	ctx context.Context,
	credentials *dagger.Secret,
) (string, error) {
	projectID, err := dag.GcpAuth().GetProjectID(ctx, credentials)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("Project ID: %s", projectID), nil
}

// Example: Add GCP credentials to custom container
func (m *GcpAuthExamples) AddCredentialsToContainer(
	credentials *dagger.Secret,
) *dagger.Container {
	container := dag.Container().From("python:3.11-slim")

	return dag.GcpAuth().WithCredentials(container, credentials)
}

// Example: Create gcloud container with additional components
func (m *GcpAuthExamples) InstallGcloudComponents(
	ctx context.Context,
	credentials *dagger.Secret,
	projectID string,
) (string, error) {
	gcloud := dag.GcpAuth().GcloudContainer(
		credentials,
		projectID,
		dagger.GcpAuthGcloudContainerOpts{
			Components: []string{"kubectl", "gke-gcloud-auth-plugin"},
		},
	)

	return gcloud.WithExec([]string{
		"gcloud", "components", "list", "--only-local-state",
	}).Stdout(ctx)
}
