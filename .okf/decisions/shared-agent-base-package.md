---
type: Decision
title: "Extract shared agent logic into _agent_base"
description: "Duplicated workspace, LLM, GitHub and routing code was moved into an included Python package so each agent is a thin wrapper."
tags: [decision, agent, refactoring]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Shared Agent Base"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: pyproject
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/pyproject.toml
    title: "_agent_base/pyproject.toml"
    author: human:telchak
    last_modified: 2026-02-17T10:31:33+01:00
  - id: intro
    resource: https://github.com/telchak/daggerverse/commit/e78c82cad0fccd3b04605b380e548ecb9620b3f3
    title: "refactor(sonarqube): Refactor code base based on Sonarqube"
    author: human:telchak
    last_modified: 2026-02-17T10:31:33+01:00
---

Each agent's `main.py` is ~350-550 lines that define only what is unique; the rest lives in
[agent-base](/agents/agent-base.md), shared through `dagger.json` `include` plus an editable `uv`
path source (it is not a Dagger module, so it has no daggerverse version).[^readme] [^pyproject]

It was introduced on 2026-02-16 inside a SonarQube-driven refactor, i.e. to remove the
duplication the quality gate flagged across Angie and Monty.[^intro] Daggie (2026-02-24) and Speck
(2026-03-21) were born on it. [Goose](/agents/goose.md) was never migrated, and remains excluded
from Sonar copy-paste detection instead.

[^readme]: Repository README, Shared Agent Base
[^pyproject]: _agent_base/pyproject.toml
[^intro]: refactor(sonarqube): Refactor code base based on Sonarqube
