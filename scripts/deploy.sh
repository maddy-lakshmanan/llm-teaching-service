#!/bin/bash
# Deployment script for Cloud Run

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
PROJECT_ID="guidedpath-829b2"
SERVICE_NAME="llm-teaching-service"
REGION="us-central1"
REPOSITORY="llm-services"  # Artifact Registry repository name
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}:latest"

echo "======================================"
echo "Deploying LLM Teaching Service"
echo "======================================"
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Image: $IMAGE_NAME"
echo ""

# Check if Dockerfile exists
if [ ! -f "$PROJECT_ROOT/docker/Dockerfile" ]; then
    echo "❌ Error: docker/Dockerfile not found at $PROJECT_ROOT/docker/Dockerfile"
    exit 1
fi

# Ensure Artifact Registry repository exists
echo "🔧 Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories describe $REPOSITORY \
    --location=$REGION \
    --project=$PROJECT_ID 2>/dev/null || \
gcloud artifacts repositories create $REPOSITORY \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID \
    --description="Docker images for LLM Teaching Service"

# Configure Docker to use Artifact Registry
echo "🔑 Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build Docker image from project root for AMD64 platform
echo "📦 Building Docker image for AMD64/Linux..."
cd "$PROJECT_ROOT"

# Use buildx to build for AMD64 platform (Cloud Run requirement)
docker buildx build \
  --platform linux/amd64 \
  -f docker/Dockerfile \
  -t $IMAGE_NAME \
  --load \
  .

# Push to Artifact Registry
echo "🚀 Pushing image to Artifact Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --project=$PROJECT_ID \
  --memory=4Gi \
  --cpu=4 \
  --min-instances=0 \
  --max-instances=1 \
  --timeout=300s \
  --port=8080 \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,HOST=0.0.0.0" \
  --allow-unauthenticated

echo ""
echo "✅ Deployment completed!"
echo ""
echo "Service URL:"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)')
echo "$SERVICE_URL"
echo ""
echo "Test the service:"
echo "  curl $SERVICE_URL/health"