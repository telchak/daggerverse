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

## Dagger Module Checklist

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
