---
type: Convention
title: "Cache busting for time-sensitive operations"
description: "Dagger caches every operation by its inputs, so token fetches, live MCP calls and similar must inject a unique env var to avoid returning stale results."
tags: [convention, dagger, caching, gotcha]
generated: { by: claude-code/2.1.310, at: 2026-10-24T22:00:00Z }
stale_after: 2027-04-24T00:00:00Z
sources:
  - id: bust
    resource: https://github.com/telchak/daggerverse/commit/c72c7ec505d08ee4f1e9481cacbdb46020dc6722
    title: "fix: add cache busting to prevent stale OIDC/access tokens"
    author: human:telchak
    last_modified: 2026-01-09T00:24:45+01:00
  - id: uuid
    resource: https://github.com/telchak/daggerverse/commit/0cd1ba0c6adabcfaa276c28c31025e9e0f1c11e3
    title: "feat: Deep code review and refactor (UUID cache busters)"
    author: human:telchak
    last_modified: 2026-01-20T20:07:30+01:00
  - id: oidc
    resource: https://github.com/telchak/daggerverse/blob/main/oidc-token/src/oidc_token/main.py
    title: "oidc-token/src/oidc_token/main.py"
    author: human:telchak
    last_modified: 2026-01-20T20:07:30+01:00
  - id: mcp-stdio
    resource: https://github.com/telchak/daggerverse/blob/main/_agent_base/src/agent_base/mcp_stdio.py
    title: "agent_base/mcp_stdio.py"
    author: human:telchak
    last_modified: 2026-10-24T22:00:00Z
---

Dagger's content-addressed cache returns the previous result whenever a `with_exec` has the same
inputs. For an OIDC token or `gcloud auth print-access-token`, that means an expired token.[^bust]

Pattern used in [oidc-token](/modules/oidc-token.md) and [gcp-auth](/modules/gcp-auth.md):[^oidc]

```python
cache_buster = str(uuid.uuid4())
token = await (
    container
    .with_env_variable("CACHE_BUSTER", cache_buster)
    .with_exec(["gcloud", "auth", "print-access-token"])
    .stdout()
)
```

The first version (2026-01-09) used `str(int(time.time()))`; it became `uuid.uuid4()` on
2026-01-20 so rapid sequential calls within one second still get fresh tokens.[^uuid] The agents'
MCP calls use the same idea: a server marked `live` (gcloud, pypi, dagger) gets a fresh
`DAGGER_AGENT_MCP_CALL` value per call.[^mcp-stdio] Apply the pattern to anything that must hit the
network every time (token minting, "latest" lookups). Dagger itself has other cache controls
(function cache policies, `dagger.lock` pins); see [Dagger platform](/dagger/platform.md).

[^bust]: fix: add cache busting to prevent stale OIDC/access tokens
[^uuid]: feat: Deep code review and refactor (UUID cache busters)
[^oidc]: oidc-token/src/oidc_token/main.py
[^mcp-stdio]: agent_base/mcp_stdio.py
