# Health Check - Dagger Module

Container health checking utilities using HTTP, TCP, and exec probes.

## Installation

```bash
# Install into your workspace (dagger.toml)
dagger module install github.com/telchak/daggerverse/health-check@<version>

# Or add it as a dependency of your own module, from the module's directory
dagger module client add github.com/telchak/daggerverse/health-check@<version> --sdk=python
```

## Functions

| Function | Description |
|----------|-------------|
| `http` | HTTP health check using curl |
| `tcp` | TCP port check using netcat |
| `exec` | Health check by executing command |
| `ready` | Generic readiness check (HTTP or TCP) |

## Usage

### HTTP Health Check

```bash
dagger api call health-check http \
  --container=FROM_BUILD \
  --port=8080 \
  --path=/health \
  --timeout=60
```

### Python Example

```python
from dagger import dag

# HTTP check
healthy = await dag.health_check().http(
    container=my_container,
    port=8080,
    path="/health",
)

# TCP check
healthy = await dag.health_check().tcp(
    container=my_container,
    port=6379,
)

# Generic ready check
healthy = await dag.health_check().ready(
    container=my_container,
    port=8080,
    endpoint="/health",  # Empty for TCP only
)
```

## License

Apache 2.0
