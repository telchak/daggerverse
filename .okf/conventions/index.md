# Conventions

How code, commits and modules are written here, and known doc drift.

* [Cache busting for time-sensitive operations](cache-busting.md) - Dagger caches every operation by its inputs, so token fetches, live MCP calls and similar must inject a unique env var to avoid returning stale results.
* [Conventional Commits](conventional-commits.md) - Commit messages follow Conventional Commits with the module as scope, because the release job derives version bumps from them.
* [Documentation drift](documentation-drift.md) - Places where README.md, module READMEs or examples disagree with the code as of 2026-10-24; check the code before trusting them.
* [Module anatomy and required files](module-anatomy.md) - The files every daggerverse module must have on Dagger 1.0, what each is for, and which ones are generated (and committed) rather than written by hand.
* [Python SDK conventions in this repo](python-sdk.md) - How modules are written with the Dagger Python SDK here: Annotated + Doc on every argument, async functions, dag.* calls through generated clients, workspace arguments and checks, secrets, ReturnType.ANY on exec, cache volumes.
