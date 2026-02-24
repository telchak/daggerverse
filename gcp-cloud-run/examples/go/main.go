// Examples for using the gcp-cloud-run Dagger module in Go.
package main

import (
	"context"
	"dagger/gcp-cloud-run-examples/internal/dagger"
	"fmt"
)

type GcpCloudRunExamples struct{}

// Example: Deploy a service to Cloud Run with scale-to-zero.
func (m *GcpCloudRunExamples) DeployService(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// Container image URI
	image string,
	// Service name
	serviceName string,
) (string, error) {
	cr := dag.GcpCloudRun()

	_, err := cr.DeployService(ctx, gcloud, image, serviceName, dagger.GcpCloudRunDeployServiceOpts{
		MinInstances:         0,
		MaxInstances:         10,
		AllowUnauthenticated: false,
	})
	if err != nil {
		return "", err
	}

	url, err := cr.GetServiceUrl(ctx, gcloud, serviceName)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Deployed %s at %s", serviceName, url), nil
}

// Example: Deploy and execute a Cloud Run job.
func (m *GcpCloudRunExamples) DeployAndRunJob(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// Container image URI
	image string,
	// Job name
	jobName string,
) (string, error) {
	cr := dag.GcpCloudRun()

	_, err := cr.DeployJob(ctx, gcloud, image, jobName, dagger.GcpCloudRunDeployJobOpts{
		Tasks:   1,
		Timeout: "600s",
	})
	if err != nil {
		return "", err
	}

	result, err := cr.ExecuteJob(ctx, gcloud, jobName, dagger.GcpCloudRunExecuteJobOpts{
		Wait: true,
	})
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Job %s completed: %s", jobName, result), nil
}
