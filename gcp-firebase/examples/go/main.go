// Examples for using the gcp-firebase Dagger module in Go.
//
// Demonstrates the three authentication approaches:
//   - Option A: Service Account Credentials (JSON key file)
//   - Option B: OIDC Token with Workload Identity Federation (recommended for CI/CD)
//   - Option C: Legacy Access Token (deprecated)
package main

import (
	"context"
	"dagger/gcp-firebase-examples/internal/dagger"
)

const defaultBuildCmd = "npm run build"

type GcpFirebaseExamples struct{}

// Example: Deploy using service account JSON credentials.
func (m *GcpFirebaseExamples) DeployWithServiceAccount(
	ctx context.Context,
	// Source directory with firebase.json
	source *dagger.Directory,
	// GCP service account credentials JSON
	credentials *dagger.Secret,
	// Firebase project ID
	projectID string,
) (string, error) {
	return dag.GcpFirebase().Deploy(ctx, projectID, dagger.GcpFirebaseDeployOpts{
		Source:          source,
		Credentials:     credentials,
		BuildCommand:    defaultBuildCmd,
		DeployFunctions: true,
	})
}

// Example: Deploy using OIDC token with Workload Identity Federation.
func (m *GcpFirebaseExamples) DeployWithOidcToken(
	ctx context.Context,
	// Source directory with firebase.json
	source *dagger.Directory,
	// OIDC JWT token from CI provider
	oidcToken *dagger.Secret,
	// GCP Workload Identity Federation provider
	workloadIdentityProvider string,
	// Firebase project ID
	projectID string,
	// +optional
	serviceAccountEmail string,
) (string, error) {
	return dag.GcpFirebase().Deploy(ctx, projectID, dagger.GcpFirebaseDeployOpts{
		Source:                   source,
		OidcToken:               oidcToken,
		WorkloadIdentityProvider: workloadIdentityProvider,
		ServiceAccountEmail:     serviceAccountEmail,
		BuildCommand:            defaultBuildCmd,
		DeployFunctions:         true,
	})
}

// Example: Deploy using a pre-fetched access token (deprecated).
func (m *GcpFirebaseExamples) DeployWithAccessToken(
	ctx context.Context,
	// Source directory with firebase.json
	source *dagger.Directory,
	// GCP access token (deprecated)
	accessToken *dagger.Secret,
	// Firebase project ID
	projectID string,
) (string, error) {
	return dag.GcpFirebase().Deploy(ctx, projectID, dagger.GcpFirebaseDeployOpts{
		Source:          source,
		AccessToken:     accessToken,
		BuildCommand:    defaultBuildCmd,
		DeployFunctions: true,
	})
}
