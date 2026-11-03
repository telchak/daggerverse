---
type: Decision
title: "Extract shared agent logic into _agent_base"
description: "Duplicated workspace, LLM, GitHub and routing code was moved into an included Python package so each agent is a thin wrapper."
tags: [decision, agent, refactoring]
generated: { by: claude-code/2.1.310, at: 2026-10-27T14:45:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: readme
    resource: https://github.com/telchak/daggerverse/blob/main/README.md
    title: "Repository README, Shared Agent Base"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
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
  - id: workspace
    resource: https://github.com/telchak/daggerverse/blob/main/dagger.toml
    title: "dagger.toml (workspace), agent scopes"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: goose-manifest
    resource: https://github.com/telchak/daggerverse/blob/main/goose/dagger-module.toml
    title: "goose/dagger-module.toml"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: goose-main
    resource: https://github.com/telchak/daggerverse/blob/main/goose/src/goose/main.py
    title: "goose/src/goose/main.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
  - id: sonar
    resource: https://sonarcloud.io/api/settings/values?component=telchak_daggerverse&keys=sonar.cpd.exclusions
    title: "SonarCloud project settings, sonar.cpd.exclusions"
    author: human:telchak
    last_modified: 2026-10-27T14:30:00Z
---

Each coding agent's `main.py` is ~350-550 lines that define only what is unique; the rest lives in
[agent-base](/agents/agent-base.md), shared through `include` plus an editable `uv`
path source (it is not a Dagger module, so it has no daggerverse version).[^readme] [^pyproject]

It was introduced on 2026-02-16 inside a SonarQube-driven refactor, i.e. to remove the
duplication the quality gate flagged across Angie and Monty.[^intro] Daggie (2026-02-24) and Speck
(2026-03-21) were born on it. [Goose](/agents/goose.md) was not migrated then, and was excluded
from Sonar copy-paste detection instead.

# Dagger 1.0 consequence

The package is still shipped through `include = ["../_agent_base"]`, now in each agent's
`dagger-module.toml`. That manifest is a runtime one (`[runtime] source =
"dagger.io/sdk/python/runtime@v1"`, `engineVersion = "v1.0.0-0"`) because the agents run on
`legacyRuntime`: `dag.current_node()` fails behind a static entrypoint.[^workspace] [^goose-manifest]

The migration also moved Goose onto it: Goose now includes `_agent_base` and imports its
`workspace`, `llm_helpers`, `mcp_stdio`, `github_tools` and `routing` modules, though its
`main.py` stays around 1300 lines.[^goose-main] Its `src/` is still in `sonar.cpd.exclusions`.[^sonar]

[^readme]: Repository README, Shared Agent Base
[^pyproject]: _agent_base/pyproject.toml
[^intro]: refactor(sonarqube): Refactor code base based on Sonarqube
[^workspace]: dagger.toml (workspace), agent scopes
[^goose-manifest]: goose/dagger-module.toml
[^goose-main]: goose/src/goose/main.py
[^sonar]: SonarCloud project settings, sonar.cpd.exclusions
