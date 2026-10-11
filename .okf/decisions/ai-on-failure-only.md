---
type: Decision
title: "AI agents run only when deterministic checks fail"
description: "The normal CI path is deterministic Dagger checks; coding agents are invoked from the workflow only on failure, to suggest fixes."
tags: [decision, agent, ci, self-healing]
status: draft
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: part4
    resource: https://dev.to/sami_chibani/cicd-in-the-era-of-ai-and-platform-engineering-a-deep-dive-into-dagger-ci-part-4-4323
    title: "CI/CD in the Era of AI and Platform Engineering, Part 4 (dev.to)"
    author: human:telchak
  - id: daggie-system
    resource: https://github.com/telchak/daggerverse/blob/main/daggie/src/daggie/prompts/system_prompt.md
    title: "Daggie system prompt, workflow structure"
    author: human:telchak
    last_modified: 2026-03-26T01:30:22+01:00
---

In the article series' AI-native part, Monty and Angie are called from the CI workflow only when
something fails, while deterministic checks handle the normal path.[^part4] Daggie's generated
workflows follow the same shape: a `dagger check` step, then
`suggest-github-fix` under `if: failure() && github.event_name == 'pull_request'`.[^daggie-system]

Why: deterministic checks are cheap, cached and reproducible; LLM calls are slow, costly and
non-deterministic, so they are spent only where a human would otherwise have to diagnose.

This concept is drafted from a search-result summary of the article, not its full text (dev.to
was unreachable from the authoring environment). Verify against the article.

[^part4]: CI/CD in the Era of AI and Platform Engineering, Part 4 (dev.to)
[^daggie-system]: Daggie system prompt, workflow structure
