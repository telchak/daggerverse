// Examples for using the gcp-vertex-ai Dagger module in Go.
package main

import (
	"context"
	"dagger/gcp-vertex-ai-examples/internal/dagger"
	"fmt"
)

type GcpVertexAiExamples struct{}

// Example: Deploy a containerized ML model to Vertex AI.
func (m *GcpVertexAiExamples) DeployMlModel(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
	// Container image URI for the model
	imageUri string,
	// Model display name
	modelName string,
	// Endpoint display name
	endpointName string,
) (string, error) {
	result, err := dag.GcpVertexAi().DeployModel(ctx, gcloud, imageUri, modelName, endpointName, dagger.GcpVertexAiDeployModelOpts{
		MachineType:      "n1-standard-4",
		AcceleratorType:  "NVIDIA_TESLA_T4",
		AcceleratorCount: 1,
		MinReplicas:      1,
		MaxReplicas:      3,
	})
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Deployed model: %s", result), nil
}

// Example: List all deployed models and endpoints.
func (m *GcpVertexAiExamples) ListDeployedModels(
	ctx context.Context,
	// Authenticated gcloud container
	gcloud *dagger.Container,
) (string, error) {
	vai := dag.GcpVertexAi()

	models, err := vai.ListModels(ctx, gcloud)
	if err != nil {
		return "", err
	}

	endpoints, err := vai.ListEndpoints(ctx, gcloud)
	if err != nil {
		return "", err
	}

	return fmt.Sprintf("Models:\n%s\n\nEndpoints:\n%s", models, endpoints), nil
}
