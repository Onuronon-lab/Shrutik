#!/bin/bash

# Build and Push Docker Images to Docker Hub
# Usage: ./scripts/build-and-push.sh [your-dockerhub-username] [tag]

set -e

# Configuration
DOCKER_USERNAME=${1:-"your-dockerhub-username"}
TAG=${2:-"latest"}
IMAGE_NAME="$DOCKER_USERNAME/shrutik"

echo "🚀 Building and pushing Docker images..."
echo "Username: $DOCKER_USERNAME"
echo "Tag: $TAG"
echo "Full image name: $IMAGE_NAME:$TAG"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if logged in to Docker Hub
if ! docker system info | grep -q "Username:"; then
    echo "❌ Not logged in to Docker Hub. Please run 'docker login' first."
    exit 1
fi

# Build the backend image
echo "🔨 Building backend image..."
docker build -f Dockerfile.prod -t "$IMAGE_NAME:$TAG" .

# Tag with additional tags if this is latest
if [ "$TAG" = "latest" ]; then
    # Also tag with current date
    DATE_TAG=$(date +%Y%m%d-%H%M%S)
    docker tag "$IMAGE_NAME:$TAG" "$IMAGE_NAME:$DATE_TAG"
    echo "📦 Also tagged as: $IMAGE_NAME:$DATE_TAG"
fi

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
docker push "$IMAGE_NAME:$TAG"

if [ "$TAG" = "latest" ]; then
    docker push "$IMAGE_NAME:$DATE_TAG"
fi

echo "✅ Successfully built and pushed $IMAGE_NAME:$TAG"
echo ""
echo "🚀 To deploy on your EC2 instance, run:"
echo "   DOCKER_IMAGE=$IMAGE_NAME:$TAG docker-compose -f docker-compose.prod.hub.yml up -d"
echo ""
echo "💡 Or use the deploy script:"
echo "   ./scripts/deploy-from-hub.sh $DOCKER_USERNAME $TAG"