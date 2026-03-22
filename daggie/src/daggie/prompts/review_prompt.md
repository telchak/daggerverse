# Dagger Module Code Review Task

Review the Dagger module source code for quality, best practices, and potential issues.

## Inputs Available

- **source**: Project source directory
- **diff** (optional): Git diff or PR diff to focus the review on
- **focus** (optional): Specific area to focus on
- Pre-loaded module references (in system prompt, if provided)

## Review Criteria

### Module Structure
- `dagger.json` correctness: name, engineVersion, sdk, dependencies, include paths
- Proper class export in `__init__.py`
- Clean separation of concerns between functions

### Function Signatures
- Proper type annotations (`Annotated[type, Doc("...")]`)
- Meaningful `Doc()` descriptions for all parameters
- Appropriate return types (`dagger.Directory`, `dagger.Container`, `str`, etc.)
- Sensible defaults for optional parameters

### Caching
- `dag.cache_volume()` used for package managers (npm, pip, go mod, maven)
- `.with_mounted_cache()` on appropriate paths
- Cache volume names are descriptive and unique

### Container Patterns
- Base images are specific (not `latest` tags in production)
- `with_exec` commands are correct and minimal
- Multi-stage builds where appropriate
- Environment variables set correctly

### Error Handling
- `expect=dagger.ExecExpect.ANY` used when exit codes need checking
- Graceful handling of optional inputs
- Clear error messages for validation failures

### Security
- Secrets use `dagger.Secret` type, never plain strings
- No secret values logged or exposed in stdout
- Minimal container permissions

### SDK Patterns
- Follows idiomatic patterns for the SDK language
- Proper async/await usage (Python)
- Correct decorator usage (`@object_type`, `@function`)
- If using `with_blocked_function` (LLM agents): verify every blocked function name actually exists as a method on the class — blocking a non-existent function causes a hard runtime error

### Toolchain Readiness
- Validation functions (test, lint, audit) should have `@check` decorator for `dagger check` discoverability
- Source parameters on check functions should use `DefaultPath(".")` for zero-config toolchain consumption
- Check if the module could serve as a toolchain (installed via `dagger toolchain install` with no SDK code)

## Approach

1. If a **diff** is provided, focus the review on those changes
2. If a **focus** is provided, prioritize that area
3. Otherwise, review `dagger.json`, main source file, and key helpers
4. Use `glob` to find relevant files, `read_file` to examine them

## Output

**CRITICAL**: You MUST set the `result` output with your review. Use the `result` output binding function — do not just produce text. Your review will be lost if you skip this step.

Structure your review as follows:

### Issues (must fix)
- List critical issues that should be fixed

### Suggestions (should consider)
- List improvements that would benefit the module

### Positive
- Note good patterns and practices found

### Summary
- Overall assessment and priority recommendations
