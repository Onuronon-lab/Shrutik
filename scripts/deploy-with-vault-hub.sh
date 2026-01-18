#!/bin/bash

# Production Deployment Script with Vault Integration + Docker Hub Images
# Deploys Shrutik using secrets from HashiCorp Vault and pre-built Docker Hub images

set -e

# Configuration
DOCKER_USERNAME=${1:-"your-dockerhub-username"}
TAG=${2:-"latest"}
IMAGE_NAME="$DOCKER_USERNAME/shrutik"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying Shrutik with Vault Integration + Docker Hub${NC}"
echo "=============================================="
echo "Docker Image: $IMAGE_NAME:$TAG"
echo ""

# Check if vault is set up
if [[ ! -f "/opt/shrutik/vault-token" ]]; then
    echo -e "${RED}❌ Vault not configured${NC}"
    echo "Run: ./scripts/vault-setup.sh && ./scripts/vault-configure.sh"
    exit 1
fi

# Create application directory
echo -e "${BLUE}📁 Setting up application directory...${NC}"
sudo mkdir -p /opt/shrutik
sudo chown $(whoami):$(whoami) /opt/shrutik

# Copy application files (excluding source code since we're using Docker Hub)
echo -e "${BLUE}📋 Copying configuration files...${NC}"
rsync -av --exclude='.git' --exclude='node_modules' --exclude='venv' \
    --exclude='app' --exclude='frontend/src' --exclude='tests' \
    --include='docker-compose.prod.hub.yml' \
    --include='nginx/' --include='scripts/' --include='alembic/' \
    --include='init.sql' --include='.env*' \
    . /opt/shrutik/

# Change to application directory
cd /opt/shrutik

# Test vault connectivity
echo -e "${BLUE}🧪 Testing Vault connectivity...${NC}"
./scripts/vault-secrets.sh test

# Load secrets into environment (using temporary .env file)
echo -e "${BLUE}🔐 Loading secrets from Vault into environment...${NC}"
./scripts/vault-secrets.sh create-env
if [[ -f ".env.prod" ]]; then
    set -a  # automatically export all variables
    source .env.prod
    set +a  # stop auto-exporting
    rm .env.prod  # clean up immediately
    echo -e "${GREEN}✅ Secrets loaded successfully${NC}"
else
    echo -e "${RED}❌ Failed to create environment file${NC}"
    exit 1
fi

# Pull latest Docker image
echo -e "${BLUE}📥 Pulling latest Docker image from Docker Hub...${NC}"
docker pull "$IMAGE_NAME:$TAG"

# Stop existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f docker-compose.prod.hub.yml down --remove-orphans 2>/dev/null || true

# Clean up development files
echo -e "${BLUE}🧹 Cleaning up development files...${NC}"
./scripts/cleanup-dev-files.sh

# Create data directories
echo -e "${BLUE}📁 Creating data directories...${NC}"
mkdir -p data/{postgres,redis,uploads,exports}
mkdir -p logs/{nginx,app,system}
mkdir -p nginx/ssl

# Set proper permissions
echo -e "${BLUE}🔐 Setting file permissions...${NC}"
chmod -R 755 data/ logs/ nginx/

# Start services with Docker Hub image
echo -e "${BLUE}🚀 Starting production services...${NC}"
DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f docker-compose.prod.hub.yml up -d

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"
services=("postgres" "redis" "backend")
all_healthy=true

for service in "${services[@]}"; do
    if DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f docker-compose.prod.hub.yml ps | grep -q "${service}.*healthy"; then
        echo -e "${GREEN}✅ $service is healthy${NC}"
    else
        echo -e "${RED}❌ $service is not healthy${NC}"
        all_healthy=false
    fi
done

# Display deployment status
echo ""
if $all_healthy; then
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Deployment completed with warnings${NC}"
fi

echo "=============================================="
echo -e "${BLUE}Services Status:${NC}"
DOCKER_IMAGE="$IMAGE_NAME:$TAG" docker-compose -f docker-compose.prod.hub.yml ps

# Get secrets for display (create temporary .env file)
./scripts/vault-secrets.sh create-env >/dev/null 2>&1
if [[ -f ".env.prod" ]]; then
    set -a
    source .env.prod
    set +a
    rm .env.prod
fi

echo ""
echo -e "${BLUE}🔑 Important Information:${NC}"
echo "• Docker Image: $IMAGE_NAME:$TAG"
echo "• Vault UI: http://localhost:8200"
echo "• Flower Monitor: http://localhost:5555 (admin:$FLOWER_PASSWORD)"
echo "• Application: http://localhost (after nginx setup)"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Configure domain: ./scripts/vault-secrets.sh update-domain your-domain.com"
echo "2. Set up SSL: ./scripts/ssl-setup.sh -d your-domain.com"
echo "3. Configure nginx: ./scripts/nginx-config.sh setup-prod -d your-domain.com"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs: DOCKER_IMAGE=$IMAGE_NAME:$TAG docker-compose -f docker-compose.prod.hub.yml logs -f [service]"
echo "  Update secrets: vault kv patch secret/shrutik/[path] key=value"
echo "  Restart services: DOCKER_IMAGE=$IMAGE_NAME:$TAG docker-compose -f docker-compose.prod.hub.yml restart"
echo "  Health check: ./scripts/health-check.sh"
echo "  Update image: docker pull $IMAGE_NAME:$TAG && DOCKER_IMAGE=$IMAGE_NAME:$TAG docker-compose -f docker-compose.prod.hub.yml up -d"
echo ""
echo -e "${YELLOW}⚠️  Remember:${NC}"
echo "  - Keep your Vault unseal keys secure"
echo "  - Backup /opt/vault/data regularly"
echo "  - Monitor vault logs: sudo journalctl -u vault -f"
echo "  - Update Docker images regularly for security patches"