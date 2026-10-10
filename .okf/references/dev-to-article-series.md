---
type: Article Series
title: "CI/CD in the Era of AI and Platform Engineering: A Deep Dive into Dagger CI"
description: "The maintainer's four-part dev.to series on Dagger CI, platform engineering and AI agents, which this repository's modules and agents illustrate."
tags: [reference, article, platform-engineering, ai]
status: draft
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-01-10T00:00:00Z
sources:
  - id: part1
    resource: https://dev.to/sami_chibani/cicd-in-the-era-of-ai-and-platform-engineering-a-deep-dive-into-dagger-ci-part-1-58pi
    title: "Part 1: pipelines as real code"
    author: human:telchak
  - id: part2
    resource: https://dev.to/sami_chibani/cicd-in-the-era-of-ai-and-platform-engineering-a-deep-dive-into-dagger-ci-part-2-3e75
    title: "Part 2: decoupling pipelines from infrastructure"
    author: human:telchak
  - id: part3
    resource: https://dev.to/sami_chibani/cicd-in-the-era-of-ai-and-platform-engineering-a-deep-dive-into-dagger-ci-part-3-9ge
    title: "Part 3: a private module library for AcmeCorp"
    author: human:telchak
  - id: part4
    resource: https://dev.to/sami_chibani/cicd-in-the-era-of-ai-and-platform-engineering-a-deep-dive-into-dagger-ci-part-4-4323
    title: "Part 4: the AI-native stack"
    author: human:telchak
  - id: linkedin
    resource: https://www.linkedin.com/in/sami-chibani/
    title: "Sami Chibani on LinkedIn"
    author: human:telchak
---

# The series

By Sami Chibani (`telchak`), the maintainer of this repository. It presents Dagger as the way to
bring pipelines into an Internal Developer Platform.[^linkedin]

| Part | Theme (as summarized in Part 4) |
|------|------|
| 1 | Building pipelines as real code[^part1] |
| 2 | Decoupling pipelines from their infrastructure[^part2] |
| 3 | Building a private module library for a fictional company, AcmeCorp[^part3] |
| 4 | The AI-native stack: Dagger's `LLM()` primitive, agents defined like any pipeline function, Daggie generating toolchain configuration, and agents (Monty, Angie) called from CI only when something fails[^part4] |

# How it maps to this repo

- Part 1: every module here is a typed Dagger function library; see [Dagger platform](/dagger/platform.md).
- Part 2: native OIDC, `env:` secrets and portable CI wiring; see
  [native OIDC](/decisions/native-oidc-instead-of-google-github-actions-auth.md) and
  [CI pipeline](/infrastructure/ci-pipeline.md).
- Part 3: this repo is the public counterpart of such a library; toolchains are the zero-code
  consumption path, see [checks and toolchains](/dagger/checks-and-toolchains.md).
- Part 4: [agents](/agents/index.md), [Daggie](/agents/daggie.md),
  [AI on failure only](/decisions/ai-on-failure-only.md).

# Status

**Draft.** The articles could not be read when this concept was written (dev.to was blocked by
the authoring environment's network policy); the table comes from search-result summaries. Read
the articles and expand this concept (key arguments, diagrams, recommended practices), then
add a `verified` entry.

[^part1]: Part 1: pipelines as real code
[^part2]: Part 2: decoupling pipelines from infrastructure
[^part3]: Part 3: a private module library for AcmeCorp
[^part4]: Part 4: the AI-native stack
[^linkedin]: Sami Chibani on LinkedIn
