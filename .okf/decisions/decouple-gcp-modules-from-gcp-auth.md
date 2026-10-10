---
type: Decision
title: "GCP service modules accept pre-authenticated inputs"
description: "gcp-artifact-registry, gcp-cloud-run, gcp-vertex-ai and gcp-firebase take a gcloud container or token instead of depending on gcp-auth."
tags: [decision, gcp, auth, composability]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: decouple
    resource: https://github.com/telchak/daggerverse/commit/4a609bd383a11d7234e4f18dde149fe6f22779d7
    title: "refactor: decouple GCP modules from gcp-auth dependency"
    author: human:telchak
    last_modified: 2026-01-04T16:57:00+01:00
---

# Decision (2026-01-04)

Remove the `gcp-auth` dependency from the GCP service modules. They accept:[^decouple]

- `gcloud: dagger.Container`: artifact-registry, cloud-run, vertex-ai, firebase.firestore
- `access_token: dagger.Secret` (and later OIDC/SA options): firebase hosting

# Why

Composability: the caller authenticates once with [gcp-auth](/modules/gcp-auth.md) and passes
the same container to several modules; modules stay small and independently versioned.

# Consequence

[gcp-firebase](/modules/gcp-firebase.md) re-grew its own auth options and duplicates the WIF
credential generator; [Goose](/agents/goose.md) is where auth is resolved for agents.

[^decouple]: refactor: decouple GCP modules from gcp-auth dependency
