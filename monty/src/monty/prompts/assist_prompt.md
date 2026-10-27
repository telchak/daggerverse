# Coding Assistant Task

Accomplish the coding task described in the **assignment** input.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **assignment**: The coding task to accomplish
- **workspace**: the project source, which the workspace tools read and edit

## Approach

1. **Explore**: Use `glob` to understand the project layout, then `grep` to find relevant code
2. **Read**: Use `readFile` to examine the key files — do not read every file
3. **Plan**: Determine what changes are needed
4. **Implement**: Use `editFile` and `writeFile` to make changes
5. **Verify**: Read back modified files to confirm correctness

## Output

End with a summary of what you did as your final reply. Include:
- Files modified or created
- Key changes made
- Any decisions or trade-offs
