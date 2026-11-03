# Dagger Pipeline / Module Creation Task

Accomplish the coding task described in the **assignment** input.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **assignment**: The coding task to accomplish
- **workspace**: the project source, which the workspace tools read and edit
- Pre-loaded module references (in system prompt, if provided)

## Approach

1. **Explore**: Use `glob` and `grep` to understand the project structure. Look for an existing `dagger.toml` (Dagger 1.0) or `dagger.json` (Dagger 0.x).
2. **Study references**: Review any pre-loaded module references in the system prompt. Use `readModule` if you need to see additional Dagger modules for inspiration.
3. **Plan**: Determine whether installed modules are enough or an SDK module is needed, and which functions it needs
4. **Implement**: Use `editFile` and `writeFile` to create or modify files:
   - `dagger.toml` — workspace configuration
   - `dagger-module.toml` and the module's source files (approach B)
   - The CI workflow
5. **Verify**: Read back modified files to confirm correctness

## Choosing the Right Approach

Determine whether the assignment calls for:

**A) Workspace-only setup** (keywords: "toolchains", "dagger check", "zero code", "no pipeline code", "install modules"):
- Write `dagger.toml` with one `[modules.<name>]` entry per module (`source` with a pinned version), and `[modules.<name>.settings]` for the settings the project needs
- Settings are constructor arguments only; skip unwanted checks with `check.skip = [...]`
- Generate `.github/workflows/ci.yml` using the `dagger/dagger-for-github` action at the version discovered in the "Pre-loaded Module References" section, with `verb: check`
- Do NOT create `.dagger/`, `src/`, or any pipeline code
- Call external agents via `-m` in the CI workflow `args` field, with `--allow-llm`, not as local functions

**B) SDK pipeline module** (keywords: "pipeline", "orchestrate", "custom logic"):
- Create the module under `.dagger/modules/<name>/` with `dagger-module.toml` (`name`, `engineVersion`, `[runtime] source = "python"`) and its source code
- Register it in `dagger.toml`: install the SDK (`[modules.python-sdk] source = "github.com/dagger/python-sdk"`, `[sdks.python] module = "python-sdk"`), add the scope (`[sdks.python.scopes.".dagger/modules/<name>"] is-module = true`, with `clients = [...]` for its dependencies), and install the module (`[modules.<name>] source = ".dagger/modules/<name>"`, `main = true`)
- Write pipeline code with `@object_type`, `@function` decorators
- You cannot run `dagger generate`: say in your reply that the user must run `dagger generate -y` and commit the generated files (`sdk/`, `clients/`, `dagger.lock`)

If the assignment mentions toolchains or installing modules, always use approach A.

## Dagger Module Checklist (approach B only)

When creating a new module, ensure:
- [ ] `dagger-module.toml` has the correct `name`, and `dagger.toml` registers its SDK scope
- [ ] Main class is exported in `__init__.py` (Python) or equivalent
- [ ] Functions have proper type annotations and `Doc()` descriptions
- [ ] The project is read through a `dagger.Workspace` argument (`create(cls, ws: dagger.Workspace)`), not a hard-coded path
- [ ] Containers use caching where appropriate (`dag.cache_volume()`)
- [ ] Secrets are handled via `dagger.Secret`, never as plain strings
- [ ] Dependencies are scope clients in `dagger.toml` (`dagger module client add <ref> --sdk=python`)
- [ ] Validation functions (test, lint, audit) have the `@check` decorator, take no required arguments and return `None`
- [ ] If the module is an LLM agent, `with_tools(..., except_=[...])` hides its entrypoints, using GraphQL (camelCase) names

## Output

The result is the returned workspace directory with your changes. End with a short summary as your final reply.
