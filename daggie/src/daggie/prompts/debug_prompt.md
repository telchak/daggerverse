# Dagger Pipeline Debug Task

Diagnose and fix the pipeline error described in the **error_output** input.

## Inputs Available

- **error_output**: The pipeline error output (stderr/stdout from `dagger call` or CI)
- **source**: Project source directory with the broken module
- Pre-loaded module references (in system prompt, if provided)

## Approach

1. **Analyze error** (0 tool calls): Read the error output carefully. Identify:
   - Which function or container step failed
   - The specific error message and type
   - File paths and line numbers mentioned
2. **Read source** (2-4 tool calls): Use `read_file` to examine the failing code and `dagger.json`
3. **Identify root cause**: Common Dagger pipeline errors include:
   - Missing dependencies in `dagger.json`
   - Wrong `engineVersion` or SDK version mismatches
   - Container `with_exec` command failures (wrong base image, missing packages)
   - Type errors (wrong annotations, missing `Annotated`, incorrect return types)
   - Missing `__init__.py` export of the main class
   - Cache volume naming conflicts
   - Secret handling errors (trying to read secret values directly)
   - Service binding issues (wrong ports, container not running)
   - `include` path errors for shared packages
4. **Fix** (1-3 tool calls): Use `edit_file` or `write_file` to apply targeted fixes
5. **Verify**: Read back modified files to confirm the fix

## Common Fixes

- **"module not found"**: Check `dagger.json` dependencies and `include` paths
- **"class not exported"**: Ensure `__init__.py` imports and exports the main class
- **"function not found"**: Verify `@function` decorator and proper type annotations
- **"container exec failed"**: Check base image, installed packages, and command syntax
- **"secret required"**: Use `dagger.Secret` type instead of `str` for sensitive values

## Output

The result is the returned workspace directory with fixes applied.
