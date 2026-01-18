#!/bin/bash

# Production Deployment Script with Vault Integration
# Deploys Shrutik using secrets from HashiCorp Vault

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying Shrutik with Vault Integration${NC}"
echo "=============================================="

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

# Copy application files
echo -e "${BLUE}📋 Copying application files...${NC}"
rsync -av --exclude='.git' --exclude='node_modules' --exclude='venv' . /opt/shrutik/

# Change to application directory
cd /opt/shrutik

# Test vault connectivity
echo -e "${BLUE}🧪 Testing Vault connectivity...${NC}"
./scripts/vault-secrets.sh test

# Create .env file from vault
echo -e "${BLUE}🔐 Creating environment file from Vault...${NC}"
./scripts/vault-secrets.sh create-env

# Stop existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# Clean up development files
echo -e "${BLUE}🧹 Cleaning up development files...${NC}"
./scripts/cleanup-dev-files.sh

# Build production images
echo -e "${BLUE}🏗️  Building production images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Create data directories
echo -e "${BLUE}📁 Creating data directories...${NC}"
mkdir -p data/{postgres,redis,uploads,exports}
mkdir -p logs/{nginx,app,system}
mkdir -p nginx/ssl

# Set proper permissions
echo -e "${BLUE}🔐 Setting file permissions...${NC}"
chmod -R 755 data/ logs/ nginx/
chmod 600 .env.prod

# Start services
echo -e "${BLUE}🚀 Starting production services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"
services=("postgres" "redis" "backend")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "${service}.*healthy"; then
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
docker-compose -f docker-compose.prod.yml ps

# Get secrets for display
source <(./scripts/vault-secrets.sh export)

echo ""
echo -e "${BLUE}🔑 Important Information:${NC}"
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
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f [service]"
echo "  Update secrets: vault kv patch secret/shrutik/[path] key=value"
echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  Health check: ./scripts/health-check.sh"
echo ""
echo -e "${YELLOW}⚠️  Remember:${NC}"
echo "  - Keep your Vault unseal keys secure"
echo "  - Backup /opt/vault/data regularly"
echo "  - Monitor vault logs: sudo journalctl -u vault -f"