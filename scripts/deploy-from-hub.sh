#!/bin/bash

# Deploy from Docker Hub images
# Usage: ./scripts/deploy-from-hub.sh [your-dockerhub-username] [tag]

set -e

# Configuration
DOCKER_USERNAME=${1:-"your-dockerhub-username"}
TAG=${2:-"latest"}
IMAGE_NAME="$DOCKER_USERNAME/shrutik"
COMPOSE_FILE="docker-compose.prod.hub.yml"

echo "🚀 Deploying from Docker Hub..."
echo "Username: $DOCKER_USERNAME"
echo "Tag: $TAG"
echo "Full image name: $IMAGE_NAME:$TAG"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Compose file $COMPOSE_FILE not found!"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure environment variables are set."
fi

# Pull the latest image
echo "📥 Pulling latest image from Docker Hub..."
docker pull "$IMAGE_NAME:$TAG"

# Stop existing containers
echo "🛑 Stopping existing containers..."
DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f "$COMPOSE_FILE" down

# Start new containers
echo "🚀 Starting new containers..."
DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f "$COMPOSE_FILE" up -d

# Wait a moment for containers to start
echo "⏳ Waiting for containers to start..."
sleep 10

# Check container status
echo "📊 Container status:"
DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f "$COMPOSE_FILE" ps

# Check backend health
echo "🏥 Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    elif [ $i -eq 30 ]; then
        echo "❌ Backend health check failed after 30 attempts"
        echo "📋 Backend logs:"
        DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f "$COMPOSE_FILE" logs backend
        exit 1
    else
        echo "⏳ Waiting for backend to be ready... (attempt $i/30)"
        sleep 2
    fi
done

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Your application should be available at:"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:8080"
echo "   - Flower (Celery monitoring): http://localhost:8080/flower"
echo ""
echo "📋 To view logs:"
echo "   DOCKER_IMAGE=$IMAGE_NAME:$TAG docker-compose -f $COMPOSE_FILE logs -f"