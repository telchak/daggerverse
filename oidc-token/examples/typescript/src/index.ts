/**
 * Examples for using the oidc-token Dagger module in TypeScript.
 */
import { dag, Secret, object, func } from "@dagger.io/dagger"

@object()
export class OidcTokenExamples {
  /**
   * Example: Fetch GitHub Actions OIDC token for GCP authentication.
   *
   * Use this in a GitHub Actions workflow with `id-token: write` permission
   * to get a token for authenticating with GCP via Workload Identity Federation.
   */
  @func()
  githubOidcToGcp(
    requestToken: Secret,
    requestUrl: Secret,
    workloadIdentityProvider: string,
  ): Secret {
    return dag.oidcToken().githubToken(requestToken, requestUrl, {
      audience: workloadIdentityProvider,
    })
  }

  /**
   * Example: Pass through GitLab CI OIDC token.
   *
   * GitLab provides the JWT directly as an environment variable.
   * Configure `id_tokens` in your .gitlab-ci.yml to use this.
   */
  @func()
  gitlabOidcPassthrough(ciJobJwt: Secret): Secret {
    return dag.oidcToken().gitlabToken(ciJobJwt)
  }

  /**
   * Example: Decode and display OIDC token claims for debugging.
   *
   * Useful for troubleshooting Workload Identity Federation issues
   * by inspecting the token's issuer, subject, and audience claims.
   */
  @func()
  async debugTokenClaims(token: Secret): Promise<string> {
    return dag.oidcToken().tokenClaims(token)
  }
}
