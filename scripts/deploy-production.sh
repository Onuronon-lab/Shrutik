#!/bin/bash

# Production Deployment Script for Shrutik Voice Collection Platform
# This script prepares and deploys the application in production mode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Shrutik Production Deployment${NC}"
echo "=================================================="

# Check if .env.prod exists
if [ ! -f ".env.prod" ]; then
    echo -e "${YELLOW}⚠️  .env.prod file not found!${NC}"
    echo "Creating .env.prod from template..."
    cp .env.prod.example .env.prod
    echo -e "${RED}❗ IMPORTANT: Edit .env.prod with your production values before continuing!${NC}"
    echo "Required changes:"
    echo "  - POSTGRES_PASSWORD"
    echo "  - SECRET_KEY"
    echo "  - ALLOWED_HOSTS"
    echo "  - CORS_ALLOWED_ORIGINS"
    echo "  - DOMAIN_NAME"
    echo "  - SSL_EMAIL"
    echo "  - FLOWER_BASIC_AUTH"
    echo ""
    read -p "Press Enter after editing .env.prod to continue..."
fi

# Validate required environment variables
echo -e "${BLUE}🔍 Validating environment configuration...${NC}"
source .env.prod

required_vars=("POSTGRES_PASSWORD" "SECRET_KEY" "DOMAIN_NAME" "SSL_EMAIL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "CHANGE_THIS_PASSWORD" ] || [ "${!var}" = "CHANGE_THIS_TO_SECURE_RANDOM_KEY_64_CHARS_MINIMUM" ] || [ "${!var}" = "your-domain.com" ] || [ "${!var}" = "admin@your-domain.com" ]; then
        echo -e "${RED}❌ $var is not set or still has default value in .env.prod${NC}"
        echo "Please update .env.prod with proper production values."
        exit 1
    fi
done

echo -e "${GREEN}✅ Environment configuration validated${NC}"

# Stop existing containers if running
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# Clean up development files
echo -e "${BLUE}🧹 Cleaning up development files...${NC}"
./scripts/cleanup-dev-files.sh

# Build production images
echo -e "${BLUE}🏗️  Building production Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Create necessary directories
echo -e "${BLUE}📁 Creating data directories...${NC}"
mkdir -p data/{postgres,redis,uploads,exports}
mkdir -p logs/{nginx,app,system}
mkdir -p nginx/{ssl,sites-available}

# Set proper permissions
echo -e "${BLUE}🔐 Setting file permissions...${NC}"
chmod -R 755 data/
chmod -R 755 logs/
chmod -R 755 nginx/

# Start services
echo -e "${BLUE}🚀 Starting production services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"
services=("postgres" "redis" "backend")
for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "${service}.*healthy"; then
        echo -e "${GREEN}✅ $service is healthy${NC}"
    else
        echo -e "${RED}❌ $service is not healthy${NC}"
        echo "Check logs with: docker-compose -f docker-compose.prod.yml logs $service"
    fi
done

# Display deployment status
echo ""
echo -e "${GREEN}🎉 Production deployment completed!${NC}"
echo "=================================================="
echo -e "${BLUE}Services Status:${NC}"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Configure SSL certificates (run: ./scripts/ssl-setup.sh)"
echo "2. Set up Nginx reverse proxy configuration"
echo "3. Configure domain DNS to point to this server"
echo "4. Set up monitoring and backup scripts"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f [service]"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  Update services: docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo -e "${YELLOW}⚠️  Remember to:${NC}"
echo "  - Configure your firewall (UFW)"
echo "  - Set up SSL certificates"
echo "  - Configure backup schedules"
echo "  - Set up monitoring alerts"