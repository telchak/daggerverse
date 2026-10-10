---
type: Convention
title: "Cache busting for time-sensitive operations"
description: "Dagger caches every operation by its inputs, so token fetches and similar must inject a changing env var to avoid returning stale results."
tags: [convention, dagger, caching, gotcha]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: bust
    resource: https://github.com/telchak/daggerverse/commit/c72c7ec505d08ee4f1e9481cacbdb46020dc6722
    title: "fix: add cache busting to prevent stale OIDC/access tokens"
    author: human:telchak
    last_modified: 2026-01-09T00:24:45+01:00
  - id: auth-utils
    resource: https://github.com/telchak/daggerverse/blob/main/tests/src/tests/auth_utils.py
    title: "tests/src/tests/auth_utils.py"
    author: human:telchak
    last_modified: 2026-02-12T18:58:50+01:00
---

Dagger's content-addressed cache returns the previous result whenever a `with_exec` has the same
inputs. For an OIDC token or `gcloud auth print-access-token`, that means an expired token.

Pattern used in [oidc-token](/modules/oidc-token.md) and [gcp-auth](/modules/gcp-auth.md):[^bust]

```python
cache_buster = str(int(time.time()))
token = await (
    container
    .with_env_variable("CACHE_BUSTER", cache_buster)
    .with_exec(["gcloud", "auth", "print-access-token"])
    .stdout()
)
```

The tests use `uuid.uuid4()` instead, so rapid sequential calls within one second still get
fresh tokens.[^auth-utils] Apply the same pattern to anything that must hit the network every time
(token minting, "latest" lookups). Dagger itself has newer cache controls (function cache
policies, workspace lockfiles); see [Dagger platform](/dagger/platform.md).

[^bust]: fix: add cache busting to prevent stale OIDC/access tokens
[^auth-utils]: tests/src/tests/auth_utils.py
