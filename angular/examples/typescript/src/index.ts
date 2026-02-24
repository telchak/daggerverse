/**
 * Examples for using the angular Dagger module in TypeScript.
 */
import { dag, Directory, object, func } from "@dagger.io/dagger"

const exampleRepo =
  "https://github.com/realworld-apps/angular-realworld-example-app.git"

@object()
export class AngularExamples {
  /**
   * Example: Build an Angular project for production.
   */
  @func()
  async buildProject(source?: Directory): Promise<string> {
    if (!source) {
      source = dag.git(exampleRepo).branch("main").tree()
    }

    const dist = await dag.angular().build(source, {
      configuration: "production",
    })
    const entries = await dist.entries()

    return `Build succeeded: ${entries.length} files in dist/`
  }

  /**
   * Example: Lint an Angular project.
   */
  @func()
  async lintProject(source?: Directory): Promise<string> {
    if (!source) {
      source = dag.git(exampleRepo).branch("main").tree()
    }

    const output = await dag.angular().lint(source)
    return `Lint output:\n${output}`
  }

  /**
   * Example: Install dependencies and verify node_modules.
   */
  @func()
  async installDeps(source?: Directory): Promise<string> {
    if (!source) {
      source = dag.git(exampleRepo).branch("main").tree()
    }

    const result = dag.angular().install(source)
    const entries = await result.entries()
    const hasModules = entries.includes("node_modules")

    return `Install succeeded: node_modules=${hasModules}, ${entries.length} entries`
  }
}
