/**
 * Examples for using the Angie (Angular Agent) Dagger module in TypeScript.
 *
 * Demonstrates local development and CI/CD use cases.
 */
import { dag, Directory, Secret, object, func } from "@dagger.io/dagger"

@object()
export class AngieExamples {
  // ========== LOCAL DEVELOPMENT ==========

  /**
   * Example: Use Angie as a local coding assistant.
   *
   * Run from your Angular project root:
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     assist --source=. --assignment="Add a search component with debounce"
   *
   * Export modified files back:
   *   dagger call -m ... assist --source=. --assignment="..." export --path=.
   */
  @func()
  async assistLocal(
    source: Directory,
    assignment: string = "Analyze this project and describe its architecture.",
  ): Promise<Directory> {
    return dag.angie({ source }).assist({ assignment })
  }

  /**
   * Example: Review your Angular code locally.
   *
   * Run from your Angular project root:
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     review --source=. --focus="performance and change detection"
   */
  @func()
  async reviewLocal(source: Directory, focus: string = ""): Promise<string> {
    return dag.angie({ source }).review({ focus })
  }

  /**
   * Example: Preview an Angular version upgrade (dry run).
   *
   * Run from your Angular project root:
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     upgrade --source=. --target-version=19 --dry-run
   */
  @func()
  async upgradeLocal(
    source: Directory,
    targetVersion: string,
  ): Promise<Directory> {
    return dag.angie({ source }).upgrade({ targetVersion, dryRun: true })
  }

  // ========== GITHUB INTEGRATION ==========

  /**
   * Example: Read a GitHub issue, implement it, and create a PR.
   *
   * In GitHub Actions (triggered by labeling an issue):
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     develop-github-issue \
   *     --github-token=env:GITHUB_TOKEN \
   *     --issue-id=42 \
   *     --repository="https://github.com/owner/repo" \
   *     --source=.
   */
  @func()
  async developGithubIssue(
    source: Directory,
    githubToken: Secret,
    issueId: number,
    repository: string,
  ): Promise<string> {
    return dag.angie({ source }).developGithubIssue({
      githubToken,
      issueId,
      repository,
    })
  }

  // ========== CI/CD PIPELINE ==========

  /**
   * Example: Review a PR diff in CI.
   *
   * In GitHub Actions:
   *   DIFF=$(git diff origin/main...HEAD)
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     review --source=. --diff="$DIFF" --focus="Angular best practices"
   */
  @func()
  async ciReviewPr(source: Directory, diff: string): Promise<string> {
    return dag.angie({ source }).review({
      diff,
      focus: "Angular best practices, type safety, and performance",
    })
  }

  /**
   * Example: Generate tests in CI for untested components.
   *
   * In your CI pipeline:
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     write-tests --source=. --target="src/app/features/auth/"
   */
  @func()
  async ciGenerateTests(
    source: Directory,
    target: string = "",
  ): Promise<Directory> {
    return dag.angie({ source }).writeTests({ target })
  }

  /**
   * Example: Build the project in CI and get diagnostics on failures.
   *
   * In your CI pipeline:
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     build --source=. --command="ng build --configuration production"
   */
  @func()
  async ciBuildAndFix(
    source: Directory,
    command: string = "ng build --configuration production",
  ): Promise<Directory> {
    return dag.angie({ source }).build({ command })
  }

  /**
   * Example: Run upgrade compatibility check in CI (dry run).
   *
   * Schedule as a periodic CI job to check upgrade readiness:
   *   dagger call -m github.com/telchak/daggerverse/angie \
   *     upgrade --source=. --target-version=20 --dry-run
   */
  @func()
  async ciUpgradeCheck(
    source: Directory,
    targetVersion: string,
  ): Promise<Directory> {
    return dag.angie({ source }).upgrade({ targetVersion, dryRun: true })
  }
}
