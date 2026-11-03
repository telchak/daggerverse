# Dagger TypeScript SDK Guide

## GraphQL → TypeScript Translation

| GraphQL | TypeScript |
|---------|------------|
| `type MyModule` | `@object() class MyModule {}` |
| field/function | `@func()` decorator on method |
| `String` | `string` |
| `Int` | `number` |
| `Boolean` | `boolean` |
| `Float` | `number` |
| `[String!]!` | `string[]` |
| `String!` (required) | parameter without `?` |
| `String` (optional) | `param?: string` |
| `Container` | `Container` |
| `Directory` | `Directory` |
| `File` | `File` |
| `Secret` | `Secret` |
| `Service` | `Service` |

## Module Structure

```
my-module/
  dagger-module.toml   # name, engineVersion, [runtime] source = "typescript"
  package.json
  tsconfig.json        # maps @dagger.io/dagger to the generated sdk/
  sdk/                 # generated typed client — committed
  src/
    index.ts           # Main module class
```

The workspace's `dagger.toml` registers the module as a TypeScript SDK scope.
Run `dagger generate -y` after API or dependency changes and commit the
result. A Dagger 0.x module uses `dagger.json` instead; Dagger 1.0 still loads it.

## Key Patterns

```typescript
import { dag, object, func, check, Container, Directory, Workspace } from "@dagger.io/dagger"

@object()
class MyModule {
  source: Directory

  // ws is auto-populated from the current workspace
  constructor(ws: Workspace) {
    this.source = ws.directory("/")
  }

  @func()
  build(target: string = "release"): Container {
    return dag
      .container()
      .from("node:22-slim")
      .withDirectory("/app", this.source)
      .withWorkdir("/app")
      .withExec(["npm", "install"])
  }

  // A check takes no required arguments and returns nothing
  @check()
  @func()
  async test(): Promise<void> {
    await this.build().withExec(["npm", "test"]).sync()
  }
}
```

## Naming Convention

TypeScript uses camelCase for methods and arguments (matching GraphQL):
- `withExec`, `withDirectory`, `withWorkdir`
- `from` (not `from_` like Python)

## Services

```typescript
@func()
serve(): Service {
  return dag
    .container()
    .from("nginx:alpine")
    .withExposedPort(80)
    .asService()
}
```

## Caching

```typescript
const cache = dag.cacheVolume("npm-cache")
ctr = ctr.withMountedCache("/root/.npm", cache)
```
