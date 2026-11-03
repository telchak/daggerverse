# Dagger Module Code Review Task

Review the Dagger module source code for quality, best practices, and potential issues.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **workspace**: the project source, which the workspace tools read and edit
- **diff** (optional): Git diff or PR diff to focus the review on
- **focus** (optional): Specific area to focus on
- Pre-loaded module references (in system prompt, if provided)

## Review Criteria

### Module Structure
- `dagger-module.toml` correctness: name, `[entrypoint]` or `[runtime]`, include paths (or `dagger.json` for a Dagger 0.x module)
- `dagger.toml` registers the module's SDK scope and its clients (dependencies); generated code (`sdk/`, `clients/`) is committed
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
- `expect=dagger.ReturnType.ANY` used when exit codes need checking
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
- LLM agents: `with_tools(dag.current_node(), except_=[...])` hides the entrypoints, using GraphQL (camelCase) names — a snake_case name hides nothing; `.loop()` runs before `last_reply()` or `workspace()`

### Workspace Readiness
- Validation functions (test, lint, audit) should have the `@check` decorator for `dagger check` discoverability, take no required arguments, and return `None`
- The module should read the user's project through a `dagger.Workspace` (in `create`), so it works when installed into a workspace (`dagger module install`) with no SDK code
- Workspace-level configuration belongs on the constructor, so it can be set with `[modules.<name>.settings]`

## Approach

1. If a **diff** is provided, focus the review on those changes
2. If a **focus** is provided, prioritize that area
3. Otherwise, review `dagger-module.toml` (or `dagger.json`), `dagger.toml`, the main source file, and key helpers
4. Use `glob` to find relevant files, `readFile` to examine them

## Output

**CRITICAL**: Your final reply is the review: write all of it there.

Structure your review as follows:

### Issues (must fix)
- List critical issues that should be fixed

### Suggestions (should consider)
- List improvements that would benefit the module

### Positive
- Note good patterns and practices found

### Summary
- Overall assessment and priority recommendations
