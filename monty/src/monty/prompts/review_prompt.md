# Code Review Task

Review the Python project source code for quality, best practices, and potential issues.

## Inputs Available

- **source**: Python project source directory
- **diff** (optional): Git diff or PR diff to focus the review on
- **focus** (optional): Specific area to focus on (e.g. "performance", "security", "type safety")

## Review Criteria

### Python Patterns
- Type hints usage and consistency
- Dataclass / Pydantic model patterns
- Async/await usage and concurrency patterns
- Error handling (specific exceptions vs bare except)
- Context manager usage for resources

### Code Quality
- PEP 8 compliance and naming conventions
- Code duplication and DRY violations
- Function/method complexity and length
- Import organization and circular imports
- Proper use of `__all__` for public APIs

### Performance
- Unnecessary list comprehensions (use generators for large data)
- N+1 query patterns in ORM code
- Inefficient string concatenation in loops
- Missing caching for expensive operations
- Proper use of `__slots__` where appropriate

### Security
- SQL injection risks (raw queries vs parameterized)
- Command injection via `subprocess` or `os.system`
- Hardcoded secrets or credentials
- Insecure deserialization (pickle, yaml.load)
- Path traversal vulnerabilities

### Testing
- Test coverage for modules and functions
- Proper test isolation and mocking
- Fixture usage and test organization
- Edge case and error path coverage

## Approach

1. If a **diff** is provided, focus the review **only** on those changes
2. If a **focus** is provided, prioritize that area
3. Otherwise, review the project structure and key files (entry points, models, routes, config)

**Budget: 10 tool calls.** Start with `glob`, read 3-5 key files, then write your review.

## Output

Write a structured review to the `result` output:

### Issues (must fix)
- List critical issues that should be fixed

### Suggestions (should consider)
- List improvements that would benefit the codebase

### Positive
- Note good patterns and practices found

### Summary
- Overall assessment and priority recommendations
