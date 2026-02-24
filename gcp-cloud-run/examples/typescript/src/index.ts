/**
 * Examples for using the gcp-cloud-run Dagger module in TypeScript.
 */
import { dag, Container, object, func } from "@dagger.io/dagger"

@object()
export class GcpCloudRunExamples {
  /**
   * Example: Deploy a service to Cloud Run with scale-to-zero.
   */
  @func()
  async deployService(
    gcloud: Container,
    image: string,
    serviceName: string,
  ): Promise<string> {
    const cr = dag.gcpCloudRun()

    await cr.deployService(gcloud, image, serviceName, {
      minInstances: 0,
      maxInstances: 10,
      allowUnauthenticated: false,
    })

    const url = await cr.getServiceUrl(gcloud, serviceName)

    return `Deployed ${serviceName} at ${url}`
  }

  /**
   * Example: Deploy and execute a Cloud Run job.
   */
  @func()
  async deployAndRunJob(
    gcloud: Container,
    image: string,
    jobName: string,
  ): Promise<string> {
    const cr = dag.gcpCloudRun()

    await cr.deployJob(gcloud, image, jobName, {
      tasks: 1,
      timeout: "600s",
    })

    const result = await cr.executeJob(gcloud, jobName, {
      wait: true,
    })

    return `Job ${jobName} completed: ${result}`
  }
}
