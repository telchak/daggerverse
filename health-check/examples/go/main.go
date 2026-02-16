// Examples for using the health-check Dagger module in Go.
package main

import (
	"context"
	"dagger/health-check-examples/internal/dagger"
)

const nginxImage = "nginx:alpine"

type HealthCheckExamples struct{}

// Example: Health check an HTTP service (nginx)
func (m *HealthCheckExamples) CheckHttpService(ctx context.Context) (string, error) {
	nginx := dag.Container().From(nginxImage)

	// Check if nginx is healthy on port 80
	_, err := dag.HealthCheck().Http(ctx, nginx, dagger.HealthCheckHttpOpts{
		Port: 80,
		Path: "/",
	})
	if err != nil {
		return "", err
	}

	return "✓ Nginx is healthy and responding on port 80", nil
}

// Example: Check if a TCP port is accepting connections (Redis)
func (m *HealthCheckExamples) CheckTcpPort(ctx context.Context) (string, error) {
	redis := dag.Container().From("redis:alpine")

	// Check if Redis port 6379 is open
	_, err := dag.HealthCheck().Tcp(ctx, redis, dagger.HealthCheckTcpOpts{
		Port: 6379,
	})
	if err != nil {
		return "", err
	}

	return "✓ Redis port 6379 is open and accepting connections", nil
}

// Example: Check a custom health endpoint with timeout
func (m *HealthCheckExamples) CheckWithCustomEndpoint(ctx context.Context) (string, error) {
	// Simulate an API service
	api := dag.Container().
		From("python:3.11-slim").
		WithExec([]string{"pip", "install", "flask"}).
		WithNewFile("/app.py", `from flask import Flask
app = Flask(__name__)
@app.route("/api/health")
def health(): return "OK"
if __name__ == "__main__": app.run(host="0.0.0.0", port=5000)`).
		WithExec([]string{"python", "/app.py"}, dagger.ContainerWithExecOpts{
			UseEntrypoint: true,
		})

	// Check custom health endpoint
	_, err := dag.HealthCheck().Http(ctx, api, dagger.HealthCheckHttpOpts{
		Port:    5000,
		Path:    "/api/health",
		Timeout: 30,
	})
	if err != nil {
		return "", err
	}

	return "✓ API service health endpoint is responding", nil
}

// Example: Health check using a command execution
func (m *HealthCheckExamples) CheckWithExec(ctx context.Context) (string, error) {
	postgres := dag.Container().
		From("postgres:alpine").
		WithEnvVariable("POSTGRES_PASSWORD", "secret")

	// Check PostgreSQL using pg_isready command
	_, err := dag.HealthCheck().Exec(ctx, postgres, []string{"pg_isready", "-U", "postgres"})
	if err != nil {
		return "", err
	}

	return "✓ PostgreSQL is ready to accept connections", nil
}

// Example: Use the ready() convenience method
func (m *HealthCheckExamples) UseReadyHelper(ctx context.Context) (string, error) {
	// HTTP check (with endpoint)
	nginx := dag.Container().From(nginxImage)
	_, err := dag.HealthCheck().Ready(ctx, nginx, 80, dagger.HealthCheckReadyOpts{
		Endpoint: "/",
		Timeout:  30,
	})
	if err != nil {
		return "", err
	}

	// TCP check (without endpoint)
	redis := dag.Container().From("redis:alpine")
	_, err = dag.HealthCheck().Ready(ctx, redis, 6379, dagger.HealthCheckReadyOpts{
		Timeout: 30,
	})
	if err != nil {
		return "", err
	}

	return "✓ Both services passed readiness checks", nil
}

// Example: Chain health check with other container operations
func (m *HealthCheckExamples) ChainWithOtherOperations(ctx context.Context) (string, error) {
	// Start a service, check it's healthy, then use it
	api := dag.Container().
		From(nginxImage).
		WithNewFile("/usr/share/nginx/html/index.html", "Hello!")

	// Health check returns the original container, so you can chain operations
	healthy, err := dag.HealthCheck().Http(ctx, api, dagger.HealthCheckHttpOpts{
		Port: 80,
	})
	if err != nil {
		return "", err
	}

	result, err := healthy.
		WithExec([]string{"cat", "/usr/share/nginx/html/index.html"}).
		Stdout(ctx)
	if err != nil {
		return "", err
	}

	return "✓ Service is healthy. Content: " + result, nil
}
