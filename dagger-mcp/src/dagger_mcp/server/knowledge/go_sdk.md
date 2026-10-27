# Dagger Go SDK Guide

## GraphQL → Go Translation

| GraphQL | Go |
|---------|-----|
| `type MyModule` | `type MyModule struct {}` |
| field/function | Method with pointer receiver `(m *MyModule)` |
| `String` | `string` |
| `Int` | `int` |
| `Boolean` | `bool` |
| `Float` | `float64` |
| `[String!]!` | `[]string` |
| `String!` (required) | parameter without `Optional` |
| `String` (optional) | `Optional[string]` |
| `Container` | `*dagger.Container` |
| `Directory` | `*dagger.Directory` |
| `File` | `*dagger.File` |
| `Secret` | `*dagger.Secret` |
| `Service` | `*dagger.Service` |

## Module Structure

```
my-module/
  dagger-module.toml   # name, engineVersion, [runtime] source = "go"
  go.mod
  go.sum
  main.go              # Main module struct and methods
  dagger.gen.go        # generated — committed
  internal/dagger/     # generated typed client — committed
```

The workspace's `dagger.toml` registers the module as a Go SDK scope. Run
`dagger generate -y` after API or dependency changes and commit the result.
A Dagger 0.x module uses `dagger.json` instead; Dagger 1.0 still loads it.

## Key Patterns

```go
package main

import (
    "dagger/my-module/internal/dagger"
)

type MyModule struct{}

func (m *MyModule) Build(
    ctx context.Context,
    source *dagger.Directory,
    // +optional
    // +default="release"
    target string,
) *dagger.Container {
    return dag.Container().
        From("golang:1.23").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"go", "build", "-o", "app"})
}
```

## Naming Convention

Go uses PascalCase for exported methods and arguments:
- `WithExec`, `WithDirectory`, `WithWorkdir`
- `From` (not `from_` like Python)

## Comments as Docs

Go uses `// +optional` and `// +default=` comments for argument metadata:

```go
// +optional
// +default="main"
branch string,
```

## Constructor

```go
func New(
    // The current workspace, auto-populated by Dagger.
    ws *dagger.Workspace,
) *MyModule {
    return &MyModule{Source: ws.Directory("/")}
}
```

## Checks

```go
// Lint the project. A check returns only an error.
//
// +check
func (m *MyModule) Lint(ctx context.Context) error {
    _, err := dag.Container().
        From("golangci/golangci-lint:latest").
        WithDirectory("/src", m.Source).
        WithWorkdir("/src").
        WithExec([]string{"golangci-lint", "run"}).
        Sync(ctx)
    return err
}
```

## Services

```go
func (m *MyModule) Serve() *dagger.Service {
    return dag.Container().
        From("nginx:alpine").
        WithExposedPort(80).
        AsService()
}
```

## Caching

```go
cache := dag.CacheVolume("go-cache")
ctr = ctr.WithMountedCache("/root/.cache/go-build", cache)
```
