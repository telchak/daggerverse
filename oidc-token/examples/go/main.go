// Examples for using the oidc-token Dagger module in Go.
package main

import (
	"context"
	"dagger/oidc-token-examples/internal/dagger"
)

type OidcTokenExamples struct{}

// Example: Fetch GitHub Actions OIDC token for GCP authentication.
//
// Use this in a GitHub Actions workflow with `id-token: write` permission
// to get a token for authenticating with GCP via Workload Identity Federation.
func (m *OidcTokenExamples) GithubOidcToGcp(
	// ACTIONS_ID_TOKEN_REQUEST_TOKEN
	requestToken *dagger.Secret,
	// ACTIONS_ID_TOKEN_REQUEST_URL
	requestUrl *dagger.Secret,
	// GCP WIF provider resource name
	workloadIdentityProvider string,
) *dagger.Secret {
	return dag.OidcToken().GithubToken(requestToken, requestUrl, dagger.OidcTokenGithubTokenOpts{
		Audience: workloadIdentityProvider,
	})
}

// Example: Pass through GitLab CI OIDC token.
//
// GitLab provides the JWT directly as an environment variable.
// Configure `id_tokens` in your .gitlab-ci.yml to use this.
func (m *OidcTokenExamples) GitlabOidcPassthrough(
	// CI_JOB_JWT_V2 from GitLab CI
	ciJobJwt *dagger.Secret,
) *dagger.Secret {
	return dag.OidcToken().GitlabToken(ciJobJwt)
}

// Example: Decode and display OIDC token claims for debugging.
//
// Useful for troubleshooting Workload Identity Federation issues
// by inspecting the token's issuer, subject, and audience claims.
func (m *OidcTokenExamples) DebugTokenClaims(
	ctx context.Context,
	// OIDC JWT token to inspect
	token *dagger.Secret,
) (string, error) {
	return dag.OidcToken().TokenClaims(ctx, token)
}
