/**
 * Examples for using the gcp-firebase Dagger module in TypeScript.
 *
 * Demonstrates the three authentication approaches:
 * - Option A: Service Account Credentials (JSON key file)
 * - Option B: OIDC Token with Workload Identity Federation (recommended for CI/CD)
 * - Option C: Legacy Access Token (deprecated)
 */
import { dag, Directory, Secret, object, func } from "@dagger.io/dagger"

const defaultBuildCmd = "npm run build"

@object()
export class GcpFirebaseExamples {
  /**
   * Example: Deploy using service account JSON credentials.
   */
  @func()
  async deployWithServiceAccount(
    source: Directory,
    credentials: Secret,
    projectId: string,
  ): Promise<string> {
    return dag.gcpFirebase().deploy(projectId, {
      source,
      credentials,
      buildCommand: defaultBuildCmd,
      deployFunctions: true,
    })
  }

  /**
   * Example: Deploy using OIDC token with Workload Identity Federation.
   */
  @func()
  async deployWithOidcToken(
    source: Directory,
    oidcToken: Secret,
    workloadIdentityProvider: string,
    projectId: string,
    serviceAccountEmail: string = "",
  ): Promise<string> {
    return dag.gcpFirebase().deploy(projectId, {
      source,
      oidcToken,
      workloadIdentityProvider,
      serviceAccountEmail,
      buildCommand: defaultBuildCmd,
      deployFunctions: true,
    })
  }

  /**
   * Example: Deploy using a pre-fetched access token (deprecated).
   */
  @func()
  async deployWithAccessToken(
    source: Directory,
    accessToken: Secret,
    projectId: string,
  ): Promise<string> {
    return dag.gcpFirebase().deploy(projectId, {
      source,
      accessToken,
      buildCommand: defaultBuildCmd,
      deployFunctions: true,
    })
  }
}
