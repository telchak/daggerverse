# Coding Assistant Task

Accomplish the coding task described in the **assignment** input.

## Inputs Available

- **assignment**: The coding task to accomplish
- **source**: Angular project source directory

## Approach

1. **Explore**: Use `glob` and `grep` to understand the project structure and find relevant files
2. **Read**: Use `read_file` to examine existing code, understand patterns and conventions
3. **Plan**: Determine what changes are needed
4. **Implement**: Use `edit_file` and `write_file` to make changes
5. **Verify**: Read back modified files to confirm correctness

## Angular MCP Tools

Use the Angular MCP tools when you need to:
- Look up Angular API documentation or usage examples
- Check best practices for a specific pattern
- Understand migration paths for deprecated features

## Output

Write a summary of what you did to the `result` output. Include:
- Files modified or created
- Key changes made
- Any decisions or trade-offs
