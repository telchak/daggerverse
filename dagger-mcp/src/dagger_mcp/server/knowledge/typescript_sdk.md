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
  dagger.json         # {"name": "my-module", "sdk": {"source": "typescript"}, "engineVersion": "v0.19.11"}
  package.json
  tsconfig.json
  dagger/src/
    index.ts           # Main module class
```

## Key Patterns

```typescript
import { dag, object, func, Directory, Container } from "@dagger.io/dagger"

@object()
class MyModule {
  @func()
  async build(source: Directory, target: string = "release"): Promise<Container> {
    return dag
      .container()
      .from("node:22-slim")
      .withDirectory("/app", source)
      .withWorkdir("/app")
      .withExec(["npm", "install"])
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
