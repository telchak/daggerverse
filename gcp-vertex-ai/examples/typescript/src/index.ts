/**
 * Examples for using the gcp-vertex-ai Dagger module in TypeScript.
 */
import { dag, Container, object, func } from "@dagger.io/dagger"

@object()
export class GcpVertexAiExamples {
  /**
   * Example: Deploy a containerized ML model to Vertex AI.
   */
  @func()
  async deployMlModel(
    gcloud: Container,
    imageUri: string,
    modelName: string,
    endpointName: string,
  ): Promise<string> {
    const result = await dag.gcpVertexAi().deployModel(
      gcloud,
      imageUri,
      modelName,
      endpointName,
      {
        machineType: "n1-standard-4",
        acceleratorType: "NVIDIA_TESLA_T4",
        acceleratorCount: 1,
        minReplicas: 1,
        maxReplicas: 3,
      },
    )

    return `Deployed model: ${result}`
  }

  /**
   * Example: List all deployed models and endpoints.
   */
  @func()
  async listDeployedModels(gcloud: Container): Promise<string> {
    const vai = dag.gcpVertexAi()

    const models = await vai.listModels(gcloud)
    const endpoints = await vai.listEndpoints(gcloud)

    return `Models:\n${models}\n\nEndpoints:\n${endpoints}`
  }
}
