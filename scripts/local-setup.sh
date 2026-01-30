#!/bin/bash

# Local Setup Script for Shrutik EC2 Deployment
# Run this on your LOCAL machine to sync files to EC2
# Usage: ./scripts/local-setup.sh [docker-image]

set -e

# Configuration
DOCKER_IMAGE=${1:-"yourusername/shrutik:latest"}
EC2_HOST="shrutik-ec2"
EC2_USER="ubuntu"
EC2_PATH="/opt/shrutik"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Shrutik Local Setup - Syncing to EC2${NC}"
echo "=============================================="
echo "Docker Image: $DOCKER_IMAGE"
echo "EC2 Host: $EC2_HOST"
echo "EC2 Path: $EC2_PATH"
echo ""

# Check if we can SSH to EC2
echo -e "${BLUE}🔍 Testing SSH connection to EC2...${NC}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $EC2_HOST "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${RED}❌ Cannot connect to EC2 via SSH${NC}"
    echo "Make sure:"
    echo "1. Your EC2 instance is running"
    echo "2. SSH key is configured"
    echo "3. You can run: ssh $EC2_HOST"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Create directory on EC2
echo -e "${BLUE}📁 Creating application directory on EC2...${NC}"
ssh $EC2_HOST "sudo mkdir -p $EC2_PATH && sudo chown $EC2_USER:$EC2_USER $EC2_PATH"

# Sync files to EC2 (excluding source code since we're using Docker Hub)
echo -e "${BLUE}📋 Syncing configuration files to EC2...${NC}"
rsync -av --progress \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='venv/' \
    --exclude='app/' \
    --exclude='frontend/src/' \
    --exclude='frontend/node_modules/' \
    --exclude='frontend/build/' \
    --exclude='tests/' \
    --exclude='.pytest_cache/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='.env.local' \
    --exclude='uploads/' \
    --exclude='exports/' \
    --exclude='logs/' \
    --exclude='data/' \
    --include='docker-compose.yml' \
    --include='nginx/' \
    --include='scripts/' \
    --include='alembic/' \
    --include='init.sql' \
    --include='.env.example' \
    --include='.env.prod.example' \
    --include='requirements*.txt' \
    --include='Dockerfile*' \
    --include='DEPLOYMENT_GUIDE.md' \
    . $EC2_HOST:$EC2_PATH/

echo -e "${GREEN}✅ Files synced successfully${NC}"

# Update docker-compose.yml with the correct image
echo -e "${BLUE}🔧 Updating docker-compose.yml with Docker image...${NC}"
ssh $EC2_HOST "cd $EC2_PATH && sed -i 's|your-dockerhub-username/shrutik:latest|$DOCKER_IMAGE|g' docker-compose.yml"

# Make scripts executable
echo -e "${BLUE}🔧 Making scripts executable on EC2...${NC}"
ssh $EC2_HOST "cd $EC2_PATH && chmod +x scripts/*.sh"

# Create necessary directories
echo -e "${BLUE}📁 Creating data directories on EC2...${NC}"
ssh $EC2_HOST "cd $EC2_PATH && mkdir -p {data,logs,uploads,exports,nginx/ssl}"

echo ""
echo -e "${GREEN}🎉 Local setup completed successfully!${NC}"
echo "=============================================="
echo -e "${BLUE}Files synced to EC2:${NC}"
echo "• Configuration files and scripts"
echo "• Docker Compose configuration"
echo "• Nginx configuration"
echo "• Database initialization scripts"
echo "• Deployment documentation"
echo ""
echo -e "${BLUE}Docker Image configured:${NC} $DOCKER_IMAGE"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. SSH to your EC2: ssh $EC2_HOST"
echo "2. Navigate to project: cd $EC2_PATH"
echo "3. Run deployment: ./scripts/ec2-deploy.sh $DOCKER_IMAGE"
echo ""
echo -e "${YELLOW}⚠️  Note:${NC}"
echo "• Source code is NOT synced (using Docker Hub image instead)"
echo "• Make sure your Docker image is pushed to Docker Hub"
echo "• The EC2 deployment script will handle Vault setup and service startup"