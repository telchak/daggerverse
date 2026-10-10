# Infrastructure

CI, releases, tests module, Renovate and SonarCloud.

* [CI pipeline (ci.yml)](ci-pipeline.md) - The single GitHub Actions workflow: discover modules and agents, validate, test each in a parallel matrix on self-hosted Dagger runners, then release.
* [Release process (per-module semver tags)](release-process.md) - On every push to main, each module changed since its last tag gets a new <module>/vX.Y.Z tag computed by the repo's own semver module.
* [Renovate configuration](renovate.md) - Renovate keeps the Dagger engine version in sync across dagger.json, CI and README, groups it, and never bumps uv_build.
* [SonarCloud quality gate](sonarcloud.md) - SonarCloud analyses the repo (Python 3.13); copy-paste detection is disabled for agents, tests and examples, and missing lockfiles lower the security rating.
* [tests (centralized test module)](tests-module.md) - The tests/ Dagger module that exercises every module's public API exactly as a user would, one function per module or agent entrypoint.
