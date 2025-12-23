/**
 * Examples for using the health-check Dagger module in TypeScript.
 */
import { dag, Container, object, func } from "@dagger.io/dagger"

@object()
export class HealthCheckExamples {
  /**
   * Example: Health check an HTTP service (nginx)
   */
  @func()
  async checkHttpService(): Promise<string> {
    const nginx = dag.container().from("nginx:alpine")

    // Check if nginx is healthy on port 80
    await dag.healthCheck().http(nginx, { port: 80, path: "/" })

    return "✓ Nginx is healthy and responding on port 80"
  }

  /**
   * Example: Check if a TCP port is accepting connections (Redis)
   */
  @func()
  async checkTcpPort(): Promise<string> {
    const redis = dag.container().from("redis:alpine")

    // Check if Redis port 6379 is open
    await dag.healthCheck().tcp(redis, { port: 6379 })

    return "✓ Redis port 6379 is open and accepting connections"
  }

  /**
   * Example: Check a custom health endpoint with timeout
   */
  @func()
  async checkWithCustomEndpoint(): Promise<string> {
    // Simulate an API service
    const api = dag
      .container()
      .from("python:3.11-slim")
      .withExec(["pip", "install", "flask"])
      .withNewFile(
        "/app.py",
        'from flask import Flask\napp = Flask(__name__)\n@app.route("/api/health")\ndef health(): return "OK"\nif __name__ == "__main__": app.run(host="0.0.0.0", port=5000)',
      )
      .withExec(["python", "/app.py"], { useEntrypoint: true })

    // Check custom health endpoint
    await dag.healthCheck().http(api, {
      port: 5000,
      path: "/api/health",
      timeout: 30,
    })

    return "✓ API service health endpoint is responding"
  }

  /**
   * Example: Health check using a command execution
   */
  @func()
  async checkWithExec(): Promise<string> {
    const postgres = dag
      .container()
      .from("postgres:alpine")
      .withEnvVariable("POSTGRES_PASSWORD", "secret")

    // Check PostgreSQL using pg_isready command
    await dag.healthCheck().exec(postgres, ["pg_isready", "-U", "postgres"])

    return "✓ PostgreSQL is ready to accept connections"
  }

  /**
   * Example: Use the ready() convenience method
   */
  @func()
  async useReadyHelper(): Promise<string> {
    // HTTP check (with endpoint)
    const nginx = dag.container().from("nginx:alpine")
    await dag.healthCheck().ready(nginx, 80, { endpoint: "/", timeout: 30 })

    // TCP check (without endpoint)
    const redis = dag.container().from("redis:alpine")
    await dag.healthCheck().ready(redis, 6379, { timeout: 30 })

    return "✓ Both services passed readiness checks"
  }

  /**
   * Example: Chain health check with other container operations
   */
  @func()
  async chainWithOtherOperations(): Promise<string> {
    // Start a service, check it's healthy, then use it
    const api = dag
      .container()
      .from("nginx:alpine")
      .withNewFile("/usr/share/nginx/html/index.html", "Hello!")

    // Health check returns the original container, so you can chain operations
    const healthy = await dag.healthCheck().http(api, { port: 80 })

    const result = await healthy
      .withExec(["cat", "/usr/share/nginx/html/index.html"])
      .stdout()

    return `✓ Service is healthy. Content: ${result.trim()}`
  }
}
