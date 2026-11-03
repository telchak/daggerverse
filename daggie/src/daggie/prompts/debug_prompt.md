# Dagger Pipeline Debug Task

Diagnose and fix the pipeline error described in the **error_output** input.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **error_output**: The pipeline error output (stderr/stdout from `dagger api call`, `dagger check` or CI)
- **workspace**: the project source, which the workspace tools read and edit
- Pre-loaded module references (in system prompt, if provided)

## Approach

1. **Analyze error** (0 tool calls): Read the error output carefully. Identify:
   - Which function or container step failed
   - The specific error message and type
   - File paths and line numbers mentioned
2. **Read source** (2-4 tool calls): Use `readFile` to examine the failing code, `dagger-module.toml` and `dagger.toml` (or `dagger.json` for a Dagger 0.x project)
3. **Identify root cause**: Common Dagger pipeline errors include:
   - Missing module clients (dependencies) in the `dagger.toml` scope
   - Generated code that is missing or stale after a change
   - Container `with_exec` command failures (wrong base image, missing packages)
   - Type errors (wrong annotations, missing `Annotated`, incorrect return types)
   - Missing `__init__.py` export of the main class
   - Cache volume naming conflicts
   - Secret handling errors (trying to read secret values directly)
   - Service binding issues (wrong ports, container not running)
   - `include` path errors for shared packages
4. **Fix** (1-3 tool calls): Use `editFile` or `writeFile` to apply targeted fixes
5. **Verify**: Read back modified files to confirm the fix

## Common Fixes

- **"generated file ... is missing; run `dagger generate`"** or a stale `uv.lock`: the module's generated code (`sdk/`, `clients/`) must be regenerated and committed — tell the user to run `dagger generate -y`
- **"module requires dagger vX, but you have vY"**: the module's `engineVersion` is newer than the CLI; upgrade the CLI or lower `engineVersion`
- **"workspace arguments are not inherited by module runtime calls"**: a module function called another module's function that takes a `Workspace`; pass one explicitly (e.g. `directory.as_workspace()`)
- **"check X must return Void"**: a `@check` function returns a value; make it return `None` and raise on failure
- **"no current function call"** from `dag.current_node()`: the module runs on a generated entrypoint; set `legacyRuntime = true` in its `dagger.toml` scope settings and regenerate
- **"cannot apply changes: no workspace bound"**: an LLM tool returned a `Changeset` but the LLM has no workspace; add `.with_workspace(...)`
- **unknown field errors in `dagger.toml`**: Dagger 1.0 rejects unknown fields; fix the typo
- **a root module no longer found by `dagger api call`**: a module at the repository root must be loaded with `-m .`
- **"function not found"**: Verify `@function` decorator and proper type annotations
- **"container exec failed"**: Check base image, installed packages, and command syntax
- **"secret required"**: Use `dagger.Secret` type instead of `str` for sensitive values
- **LLM access denied** for a remote module: pass `--allow-llm=<module ref>` (or `all`)

## Output

The result is the returned workspace directory with fixes applied. End with a short summary of the root cause and the fix as your final reply.
