# Health Check - Dagger Module

Container health checking utilities using HTTP, TCP, and exec probes.

## Installation

```bash
dagger install github.com/YOUR_ORG/daggerverse/health-check
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
dagger call http \
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
