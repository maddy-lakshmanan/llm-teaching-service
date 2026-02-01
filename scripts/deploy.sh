#!/bin/bash
# Deployment script for Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID}"
SERVICE_NAME="llm-teaching-service"
REGION="us-central1"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:latest"

echo "======================================"
echo "Deploying LLM Teaching Service"
echo "======================================"
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Build Docker image
echo "📦 Building Docker image..."
docker build -f docker/Dockerfile -t $IMAGE_NAME .

# Push to Artifact Registry
echo "🚀 Pushing image to Artifact Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 300s \
  --set-env-vars="ENVIRONMENT=production" \
  --set-env-vars="OLLAMA_URL=${OLLAMA_URL}" \
  --set-env-vars="REDIS_URL=${REDIS_URL}" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --allow-unauthenticated

echo ""
echo "✅ Deployment completed!"
echo ""
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
