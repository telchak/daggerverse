/**
 * Examples for using the semver Dagger module in TypeScript.
 */
import { dag, Directory, Secret, object, func } from "@dagger.io/dagger"

@object()
export class SemverExamples {
  /**
   * Example: Calculate the next version based on conventional commits.
   */
  @func()
  async calculateNextVersion(source: Directory): Promise<string> {
    const nextVersion = await dag.semver().next({ source })
    const current = await dag.semver().current({ source })
    const bump = await dag.semver().bumpType({ source })

    return `Current: ${current} -> Next: ${nextVersion} (bump: ${bump})`
  }

  /**
   * Example: Release a specific module in a monorepo.
   */
  @func()
  async monorepoRelease(
    source: Directory,
    moduleName: string,
    githubToken: Secret,
  ): Promise<string> {
    const tagPrefix = `${moduleName}/`

    const result = await dag.semver().release({
      source,
      githubToken,
      tagPrefix,
    })

    return `Released ${moduleName}: ${result}`
  }

  /**
   * Example: Check what files changed since last release.
   */
  @func()
  async checkChanges(
    source: Directory,
    tagPrefix: string = "",
  ): Promise<string> {
    const changed = await dag.semver().changedPaths({
      source,
      tagPrefix,
    })

    if (!changed) {
      return "No changes since last release"
    }

    return `Changed files:\n${changed}`
  }
}
