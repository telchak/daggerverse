/**
 * Examples for using the Monty (Python Agent) Dagger module in TypeScript.
 *
 * Demonstrates local development and CI/CD use cases.
 */
import { dag, Directory, Secret, object, func } from "@dagger.io/dagger"

@object()
export class MontyExamples {
  // ========== LOCAL DEVELOPMENT ==========

  /**
   * Example: Use Monty as a local coding assistant.
   */
  @func()
  async assistLocal(
    source: Directory,
    assignment: string = "Analyze this project and describe its architecture.",
  ): Promise<Directory> {
    return dag.monty({ source }).assist({ assignment })
  }

  /**
   * Example: Review your Python code locally.
   */
  @func()
  async reviewLocal(source: Directory, focus: string = ""): Promise<string> {
    return dag.monty({ source }).review({ focus })
  }

  /**
   * Example: Read a GitHub issue, implement it, and create a PR.
   */
  @func()
  async developGithubIssue(
    source: Directory,
    githubToken: Secret,
    issueId: number,
    repository: string,
  ): Promise<string> {
    return dag.monty({ source }).developGithubIssue({
      githubToken,
      issueId,
      repository,
    })
  }

  // ========== CI/CD PIPELINE ==========

  /**
   * Example: Review a PR diff in CI.
   */
  @func()
  async ciReviewPr(source: Directory, diff: string): Promise<string> {
    return dag.monty({ source }).review({
      diff,
      focus: "Python best practices, type safety, and performance",
    })
  }
}
