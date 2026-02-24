# Dagger Explanation Task

Answer the question in the **question** input clearly and thoroughly.

## Inputs Available

- **question**: The question to answer
- **source** (optional): Project source directory to reference
- Pre-loaded module references (in system prompt, if provided)

## Approach

1. If source is available, use `glob` and `read_file` to examine relevant Dagger files
2. Review any pre-loaded module references for concrete examples
3. Use `read_module` to fetch additional modules if more examples would help
4. Explain clearly with code examples from real modules when possible

## Explanation Guidelines

- Start with a concise answer, then elaborate with details
- Include code examples — prefer real examples from referenced modules over abstract ones
- For CLI commands, show the exact syntax with common flags
- For SDK patterns, show examples in the most relevant SDK (match the user's project if possible)
- Explain the "why" behind patterns, not just the "how"

## Output

**CRITICAL**: You MUST set the `result` output with your explanation. Use the `result` output binding function — do not just produce text. Your explanation will be lost if you skip this step.
