/**
 * Examples for using the python-build Dagger module in TypeScript.
 */
import { dag, Directory, object, func } from "@dagger.io/dagger"

const exampleRepo =
  "https://github.com/nsidnev/fastapi-realworld-example-app.git"

@object()
export class PythonBuildExamples {
  /**
   * Example: Build a Python project.
   */
  @func()
  async buildProject(source?: Directory): Promise<string> {
    if (!source) {
      source = dag.git(exampleRepo).branch("master").tree()
    }

    const result = await dag.pythonBuild().build(source)
    const entries = await result.entries()

    return `Build succeeded: ${entries.length} entries`
  }

  /**
   * Example: Lint a Python project with ruff.
   */
  @func()
  async lintProject(source?: Directory): Promise<string> {
    if (!source) {
      source = dag.git(exampleRepo).branch("master").tree()
    }

    const output = await dag.pythonBuild().lint(source, { tool: "ruff" })
    return `Lint output:\n${output}`
  }

  /**
   * Example: Install dependencies.
   */
  @func()
  async installDeps(source?: Directory): Promise<string> {
    if (!source) {
      source = dag.git(exampleRepo).branch("master").tree()
    }

    const result = await dag.pythonBuild().install(source)
    const entries = await result.entries()

    return `Install succeeded: ${entries.length} entries`
  }
}
