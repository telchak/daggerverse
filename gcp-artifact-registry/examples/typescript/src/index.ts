/**
 * Examples for using the gcp-artifact-registry Dagger module in TypeScript.
 */
import { dag, Container, Directory, File, object, func } from "@dagger.io/dagger"

@object()
export class GcpArtifactRegistryExamples {
  /**
   * Example: Build and publish a container to Artifact Registry.
   */
  @func()
  async publishContainer(
    source: Directory,
    gcloud: Container,
    projectId: string,
    repository: string,
    imageName: string,
    tag: string = "latest",
  ): Promise<string> {
    const container = source.dockerBuild()

    const imageRef = await dag.gcpArtifactRegistry().publish(
      container,
      projectId,
      repository,
      imageName,
      { tag, gcloud },
    )

    return `Published: ${imageRef}`
  }

  /**
   * Example: Build and publish using local Docker config credentials.
   */
  @func()
  async publishContainerWithDockerConfig(
    source: Directory,
    dockerConfig: File,
    projectId: string,
    repository: string,
    imageName: string,
    tag: string = "latest",
  ): Promise<string> {
    const container = source.dockerBuild()

    const imageRef = await dag.gcpArtifactRegistry().publish(
      container,
      projectId,
      repository,
      imageName,
      { tag, dockerConfig },
    )

    return `Published: ${imageRef}`
  }

  /**
   * Example: List all images in an Artifact Registry repository.
   */
  @func()
  async listRepositoryImages(
    gcloud: Container,
    projectId: string,
    repository: string,
  ): Promise<string> {
    return dag.gcpArtifactRegistry().listImages(gcloud, projectId, repository)
  }
}
