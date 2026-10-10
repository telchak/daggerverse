---
type: Decision
title: "Bundle a lockfile-backed Angular fixture for module tests"
description: "The angular module test builds a small committed Angular 21 app with package-lock.json instead of cloning the RealWorld example."
tags: [decision, testing, angular, reproducibility]
generated: { by: claude-code/okf-bootstrap, at: 2026-10-10T23:30:00Z }
stale_after: 2027-04-10T00:00:00Z
sources:
  - id: fixture
    resource: https://github.com/telchak/daggerverse/commit/9c93521d9c9871f804e684bb3adf50903fffb76f
    title: "test(angular): use a bundled fixture with a lockfile instead of RealWorld"
    author: claude-code/session
    last_modified: 2026-10-10T14:03:13+00:00
  - id: pin
    resource: https://github.com/telchak/daggerverse/commit/528092b3ce1a5322600cdce09af3b1d43114de54
    title: "fix(angular): Pin angular-realworld-example-app to known good commit"
    author: human:telchak
    last_modified: 2026-03-22T19:24:59+01:00
---

The RealWorld commit pinned on 2026-03-22[^pin] only ships a `bun.lock`, so `npm ci` fell back to
`npm install`, resolving floating ranges against the live registry; npm began crashing with
"Cannot read properties of null (reading 'edgesOut')". On 2026-10-10 the module test switched to
`tests/src/tests/fixtures/angular-app` with a committed `package-lock.json`.[^fixture] Angie's agent
tests still use RealWorld.

General rule: tests must not depend on live dependency resolution; commit lockfiles.

[^fixture]: test(angular): use a bundled fixture with a lockfile instead of RealWorld
[^pin]: fix(angular): Pin angular-realworld-example-app to known good commit
