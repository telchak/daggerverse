---
type: Dagger Module
title: "gcp-firebase"
description: "Firebase Hosting build/deploy/preview channels, Firestore database management, and script runners with Firebase credentials."
resource: https://github.com/telchak/daggerverse/tree/main/gcp-firebase
tags: [module, gcp, firebase]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: main
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-firebase/src/gcp_firebase/main.py
    title: "gcp-firebase/src/gcp_firebase/main.py"
    author: human:telchak
    last_modified: 2026-02-21T16:38:26+01:00
  - id: module-readme
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-firebase/README.md
    title: "gcp-firebase/README.md"
    author: human:telchak
    last_modified: 2026-02-21T16:38:26+01:00
  - id: dagger-json
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-firebase/dagger.json
    title: "gcp-firebase/dagger.json"
    author: human:telchak
    last_modified: 2026-10-01T11:09:06+00:00
  - id: firestore
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-firebase/src/gcp_firebase/firestore.py
    title: "gcp-firebase/src/gcp_firebase/firestore.py"
    author: human:telchak
    last_modified: 2026-01-20T20:17:15+01:00
  - id: scripts
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-firebase/src/gcp_firebase/scripts.py
    title: "gcp-firebase/src/gcp_firebase/scripts.py"
    author: human:telchak
    last_modified: 2026-01-16T19:11:12+01:00
  - id: creds
    resource: https://github.com/telchak/daggerverse/blob/main/gcp-firebase/src/gcp_firebase/credentials.py
    title: "gcp-firebase/src/gcp_firebase/credentials.py"
    author: human:telchak
    last_modified: 2026-02-17T10:31:33+01:00
  - id: skip-build
    resource: https://github.com/telchak/daggerverse/commit/70334550e426dc443ffadd232c1f55f5d400ab82
    title: "fix(gcp-firebase): skip npm ci and build when build_command is empty"
    author: human:telchak
    last_modified: 2026-02-10T00:45:58+01:00
---

# Functions

Hosting, on the main class:[^main]

| Function | Notes |
|----------|-------|
| `build(source, build_command="npm run build", node_version, npm_cache)` | Returns the dist directory |
| `deploy(project_id, source, <auth>, build_command, node_version, skip_build, deploy_functions, force, npm_cache)` | |
| `deploy_preview(project_id, channel_id, source, <auth>, ..., expires)` | Returns the preview URL |
| `delete_channel(project_id, channel_id, <auth>, site, ...)` | |

`<auth>` is one of: `oidc_token` + `workload_identity_provider` (+ `service_account_email`),
`credentials` (SA JSON key), or `access_token`. An empty `build_command` (or `skip_build`)
skips `npm ci` and the build.[^skip-build]

Sub-objects:

- `firestore()` -> `Firestore`: `create`, `delete`, `update`, `describe`, `list`, `exists`
  (gcloud-container based).[^firestore]
- `scripts()` -> `FirebaseScripts`: `node`, `python`, `container`: run a script (or get a
  container) with Firebase credentials configured, e.g. for seeding Firestore.[^scripts]

# Self-contained auth

gcp-firebase does not depend on gcp-auth: it carries its own copy of the WIF credential
generator (`generate_wif_credentials_json`) which must stay in sync with
`gcp-auth/src/gcp_auth/oidc.py`.[^creds] The access token path is legacy and marked
"NOT RECOMMENDED" in tests.

# Tests and fixtures

`tests gcp-firebase` deploys a fixture app, creates and deletes a preview channel, and runs the
Firestore seed script under `tests/src/tests/fixtures/firestore-scripts` (installed with
`npm ci` from a committed lockfile).

[^main]: gcp-firebase/src/gcp_firebase/main.py
[^firestore]: gcp-firebase/src/gcp_firebase/firestore.py
[^scripts]: gcp-firebase/src/gcp_firebase/scripts.py
[^creds]: gcp-firebase/src/gcp_firebase/credentials.py
[^skip-build]: fix(gcp-firebase): skip npm ci and build when build_command is empty
