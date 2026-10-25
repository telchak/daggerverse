# Infrastructure

CI, releases, tests module, Renovate and SonarCloud.

* [CI pipeline (ci.yml)](ci-pipeline.md) - The single GitHub Actions workflow: discover modules and agents, validate them, check the committed generated code, test each in a parallel matrix on self-hosted Dagger runners, then release.
* [Release process (per-module semver tags)](release-process.md) - On every push to main, each module changed since its last tag gets a new <module>/vX.Y.Z tag computed by the repo's own semver module; a feat! migration commit takes every module to v1.0.0 for Dagger 1.0.
* [Renovate configuration](renovate.md) - Renovate bumps the Dagger version in CI (DAGGER_VERSION, runner labels), the README badge and the dagger-for-github snippets as one group read from Git tags, skips the generated code, and never bumps uv_build.
* [SonarCloud quality gate](sonarcloud.md) - SonarCloud analyses the repo (Python 3.13) without the vendored tooling and the generated Dagger 1.0 code (sdk/, clients/); copy-paste detection is disabled for agents, tests and examples, and missing lockfiles lower the security rating.
* [tests (centralized test module)](tests-module.md) - The tests/ Dagger module that exercises every module's public API exactly as a user would: one function per module or agent entrypoint, plus checks wrapping the credential-free tests.
