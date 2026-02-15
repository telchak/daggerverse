# Coding Assistant Task

Accomplish the coding task described in the **assignment** input.

## Inputs Available

- **assignment**: The coding task to accomplish
- **source**: Python project source directory

## Approach

1. **Explore**: Use `glob` to understand the project layout, then `grep` to find relevant code
2. **Read**: Use `read_file` to examine the key files — do not read every file
3. **Plan**: Determine what changes are needed
4. **Implement**: Use `edit_file` and `write_file` to make changes
5. **Verify**: Read back modified files to confirm correctness

## Output

Write a summary of what you did to the `result` output. Include:
- Files modified or created
- Key changes made
- Any decisions or trade-offs
