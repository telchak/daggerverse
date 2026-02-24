/**
 * Examples for using the Daggie (Dagger CI Agent) Dagger module in TypeScript.
 *
 * Demonstrates local development and CI/CD use cases.
 */
import { dag, Directory, Secret, object, func } from "@dagger.io/dagger"

@object()
export class DaggieExamples {
  // ========== LOCAL DEVELOPMENT ==========

  /**
   * Example: Use Daggie as a local coding assistant.
   */
  @func()
  async assistLocal(
    source: Directory,
    assignment: string = "Analyze this project and create a Dagger module for building it.",
  ): Promise<Directory> {
    return dag.daggie({ source }).assist({ assignment })
  }

  /**
   * Example: Ask Daggie to explain a Dagger concept.
   */
  @func()
  async explainConcept(
    question: string = "What is a Dagger module and how does dagger.json configure it?",
  ): Promise<string> {
    return dag.daggie().explain({ question })
  }

  /**
   * Example: Debug a Dagger pipeline error.
   */
  @func()
  async debugPipeline(
    source: Directory,
    errorOutput: string,
  ): Promise<Directory> {
    return dag.daggie({ source }).debug({ errorOutput })
  }

  /**
   * Example: Review Dagger module code.
   */
  @func()
  async reviewLocal(source: Directory, focus: string = ""): Promise<string> {
    return dag.daggie({ source }).review({ focus })
  }

  // ========== GITHUB INTEGRATION ==========

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
    return dag.daggie({ source }).developGithubIssue({
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
    return dag.daggie({ source }).review({
      diff,
      focus: "Dagger best practices, caching, and pipeline correctness",
    })
  }
}
