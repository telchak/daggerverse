# Deployment Config Review

Review the deployment configurations in the workspace for best practices, security, and correctness.

## Inputs

Their values follow this prompt, under **Input values**; an optional input that was not provided is left out.

- **project_id**: The GCP project ID
- **region**: The GCP region
- **focus** (optional): Specific area to focus on

## What to Review

Examine deployment-related files in the workspace:

- **Dockerfiles**: Base image choices, multi-stage builds, security (non-root user, minimal image), layer caching
- **firebase.json**: Hosting config, rewrites, headers, security headers
- **cloudbuild.yaml**: Build steps, substitutions, secrets handling
- **app.yaml / service.yaml**: Cloud Run service config, resource limits, scaling
- **IAM policies**: Principle of least privilege, service account permissions
- **Environment variables**: Secrets not hardcoded, proper use of Secret Manager references
- **DAGGER.md / GOOSE.md**: Context file completeness and correctness

## Review Structure

Organize findings into:

1. **Critical Issues** — Security vulnerabilities, misconfigurations that will cause failures
2. **Warnings** — Best practice violations, potential performance issues
3. **Suggestions** — Improvements, optimizations, modern alternatives
4. **Summary** — Overall assessment

## Guidelines

- Use `glob` to find relevant config files first
- Use `readFile` to examine each file
- Use `grep` to search for patterns (hardcoded secrets, deprecated configs)
- Compare against GCP best practices (use `searchGcpDocs` if needed)
- If a `focus` input is provided, prioritize that area

## Output

**CRITICAL**: Your final reply is the review: write all of it there.

Structure your review with the findings below.
