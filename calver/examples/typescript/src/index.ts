/**
 * Example using CalVer module to version and publish container releases.
 */
import { dag, Directory, object, func } from "@dagger.io/dagger"

@object()
export class CalverExamples {
  /**
   * Build, version, and publish container with auto-incremented CalVer tag.
   *
   * This example demonstrates:
   * - Auto-incrementing MICRO from git tags (v.2025.11.0 -> v.2025.11.1)
   * - Building a container
   * - Publishing with CalVer tag
   * - Tagging and pushing to git
   */
  @func()
  async release(
    source: Directory,
    registry: string = "ghcr.io/myorg/myapp",
  ): Promise<string> {
    // Generate auto-incremented version from git history
    const version = await dag.calver().generate({
      format: "v.YYYY.MM.MICRO",
      source,
    })

    // Build and publish container
    const container = source.dockerBuild()
    const ref = await container.publish(`${registry}:${version}`)

    // Tag git commit
    await dag
      .container()
      .from("alpine/git:latest")
      .withMountedDirectory("/repo", source)
      .withWorkdir("/repo")
      .withExec(["git", "tag", version])
      .withExec(["git", "push", "origin", version])
      .sync()

    return `Released ${version} -> ${ref}`
  }
}
