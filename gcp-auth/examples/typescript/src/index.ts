/**
 * Examples for using the gcp-auth Dagger module in TypeScript.
 */
import { dag, Container, Secret, object, func } from "@dagger.io/dagger"

@object()
export class GcpAuthExamples {
  /**
   * Example: Verify service account credentials and get email
   */
  @func()
  async verifyServiceAccount(credentials: Secret): Promise<string> {
    const email = await dag.gcpAuth().verifyCredentials(credentials)
    return `✓ Authenticated as: ${email}`
  }

  /**
   * Example: List GCP projects using authenticated gcloud container
   */
  @func()
  async listGcpProjects(
    credentials: Secret,
    projectId: string,
  ): Promise<string> {
    const gcloud = dag.gcpAuth().gcloudContainer(credentials, projectId)

    return gcloud
      .withExec(["gcloud", "projects", "list", "--limit=5"])
      .stdout()
  }

  /**
   * Example: Use Application Default Credentials from host (local dev)
   */
  @func()
  async useAdcLocally(projectId: string): Promise<string> {
    const gcloud = dag.gcpAuth().gcloudContainerFromHost(projectId)

    const account = await gcloud
      .withExec(["gcloud", "config", "get", "account"])
      .stdout()

    return `Using ADC account: ${account.trim()}`
  }

  /**
   * Example: Extract project ID from service account credentials
   */
  @func()
  async getProjectFromCredentials(credentials: Secret): Promise<string> {
    const projectId = await dag.gcpAuth().getProjectId(credentials)
    return `Project ID: ${projectId}`
  }

  /**
   * Example: Add GCP credentials to custom container
   */
  @func()
  addCredentialsToContainer(credentials: Secret): Container {
    const container = dag.container().from("python:3.11-slim")

    return dag.gcpAuth().withCredentials(container, credentials)
  }

  /**
   * Example: Create gcloud container with additional components
   */
  @func()
  async installGcloudComponents(
    credentials: Secret,
    projectId: string,
  ): Promise<string> {
    const gcloud = dag.gcpAuth().gcloudContainer(credentials, projectId, {
      components: ["kubectl", "gke-gcloud-auth-plugin"],
    })

    return gcloud
      .withExec(["gcloud", "components", "list", "--only-local-state"])
      .stdout()
  }
}
