/**
 * Examples for using the Goose (GCP Agent) Dagger module in TypeScript.
 */
import { dag, Container, Directory, Secret, object, func } from "@dagger.io/dagger"

@object()
export class GooseExamples {
  /**
   * Example: Deploy a public hello-world service to Cloud Run.
   */
  @func()
  async deployCloudRunService(
    gcloud: Container,
    projectId: string,
    serviceName: string,
    region: string = "us-central1",
  ): Promise<string> {
    return dag
      .goose({ gcloud, projectId, region })
      .deploy({
        assignment:
          "Deploy gcr.io/google-samples/hello-app:1.0 as a public service with allow unauthenticated access",
        serviceName,
      })
  }

  /**
   * Example: Deploy a web app to Firebase Hosting.
   */
  @func()
  async deployFirebaseHosting(
    gcloud: Container,
    credentials: Secret,
    projectId: string,
    source: Directory,
    region: string = "us-central1",
  ): Promise<string> {
    return dag
      .goose({ gcloud, projectId, region, credentials })
      .deploy({
        assignment: "Deploy to Firebase Hosting",
        serviceName: "firebase-site",
        source,
      })
  }

  /**
   * Example: Troubleshoot a Cloud Run service returning errors.
   */
  @func()
  async troubleshootService(
    gcloud: Container,
    serviceName: string,
    projectId: string,
    region: string = "us-central1",
  ): Promise<string> {
    return dag
      .goose({ gcloud, projectId, region })
      .troubleshoot(serviceName, {
        issue:
          "Service is returning 503 errors and seems to be crashing on startup",
      })
  }

  /**
   * Example: List all Cloud Run services and report their status.
   */
  @func()
  async assistListServices(
    gcloud: Container,
    projectId: string,
    region: string = "us-central1",
  ): Promise<string> {
    return dag
      .goose({ gcloud, projectId, region })
      .assist({
        assignment: "List all Cloud Run services and report their status",
      })
  }

  /**
   * Example: Review deployment configs for best practices.
   */
  @func()
  async reviewConfigs(
    gcloud: Container,
    projectId: string,
    source: Directory,
    region: string = "us-central1",
  ): Promise<string> {
    return dag
      .goose({ gcloud, projectId, region })
      .review({
        source,
        focus: "security and performance",
      })
  }
}
