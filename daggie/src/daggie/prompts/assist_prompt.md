# Dagger Pipeline / Module Creation Task

Accomplish the coding task described in the **assignment** input.

## Inputs Available

- **assignment**: The coding task to accomplish
- **source**: Project source directory
- Pre-loaded module references (in system prompt, if provided)

## Approach

1. **Explore**: Use `glob` and `grep` to understand the project structure
2. **Study references**: Review any pre-loaded module references in the system prompt. Use `read_module` if you need to see additional Dagger modules for inspiration.
3. **Plan**: Determine what Dagger module structure and functions are needed
4. **Implement**: Use `edit_file` and `write_file` to create or modify files:
   - `dagger.json` — module configuration
   - Main source file with `@object_type`/`@function` decorators (Python) or equivalent
   - Any helper modules or utilities
5. **Verify**: Read back modified files to confirm correctness

## Choosing the Right Approach

Determine whether the assignment calls for:

**A) Toolchain-only setup** (keywords: "toolchains", "dagger check", "zero code", "no pipeline code"):
- Generate `dagger.json` with `toolchains` array only — NO `sdk`, `include`, or `dependencies` fields
- Set `engineVersion` from the reference modules' `dagger.json` (use the latest version seen)
- For monorepos: add `customizations` with `defaultPath` for EVERY `@check` function's `source` param on EVERY toolchain — including deploy modules with `scan` checks. Do NOT skip any toolchain.
- Generate `.github/workflows/ci.yml` using the `dagger/dagger-for-github` action at the version discovered in the "Pre-loaded Module References" section
- The action only accepts `version`, `verb`, and `args` fields — no other fields exist
- Use the `engineVersion` from `dagger.json` (without `v` prefix) as the `version` field
- Do NOT create `.dagger/`, `src/`, or any pipeline code
- Call external agents via `-m` in CI workflow `args` field, not as local functions

**B) SDK pipeline module** (keywords: "pipeline", "orchestrate", "custom logic"):
- Generate `.dagger/` module with `dagger.json` containing `sdk` and `dependencies`
- Write pipeline code with `@object_type`, `@function` decorators

If the assignment mentions toolchains, always use approach A.

## Dagger Module Checklist (approach B only)

When creating a new module, ensure:
- [ ] `dagger.json` has correct `name`, `sdk`, `engineVersion`
- [ ] Main class is exported in `__init__.py` (Python) or equivalent
- [ ] Functions have proper type annotations and `Doc()` descriptions
- [ ] Containers use caching where appropriate (`dag.cache_volume()`)
- [ ] Secrets are handled via `dagger.Secret`, never as plain strings
- [ ] Dependencies are declared in `dagger.json` if referencing other modules
- [ ] Validation functions (test, lint, audit) have `@check` decorator and `DefaultPath(".")` on source param for toolchain readiness
- [ ] If using `with_blocked_function` (LLM agents), only block functions that actually exist on the class

## Output

The result is the returned workspace directory with your changes. Write a summary to `result` if the output type supports it.
