#!/bin/bash

# EC2 Deployment Script for Shrutik
# Run this on your EC2 instance for complete deployment
# Usage: ./scripts/ec2-deploy.sh [docker-image]

set -e

# Configuration
DOCKER_IMAGE=${1:-"yourusername/shrutik:latest"}
PROJECT_DIR="/opt/shrutik"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Shrutik EC2 Deployment${NC}"
echo "=============================================="
echo "Docker Image: $DOCKER_IMAGE"
echo "Project Directory: $PROJECT_DIR"
echo ""

# Check if running on EC2
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Don't run this script as root${NC}"
   exit 1
fi

# Navigate to project directory
cd $PROJECT_DIR

# Step 1: Install Docker and Docker Compose
echo -e "${BLUE}📦 Installing Docker and Docker Compose...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt update
    sudo apt install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
    echo -e "${YELLOW}⚠️  You may need to log out and log back in for Docker group changes to take effect${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt install -y docker-compose
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Step 2: Set up HashiCorp Vault
echo -e "${BLUE}🔐 Setting up HashiCorp Vault...${NC}"
if ! command -v vault &> /dev/null; then
    echo "Installing Vault..."
    ./scripts/vault-setup.sh
else
    echo -e "${GREEN}✅ Vault already installed${NC}"
    # Start vault service if not running
    if ! sudo systemctl is-active --quiet vault; then
        sudo systemctl start vault
        sleep 3
    fi
fi

# Step 3: Configure Vault (if not already configured)
echo -e "${BLUE}🔧 Configuring Vault...${NC}"
export VAULT_ADDR='http://127.0.0.1:8200'

# Check if vault is initialized
if ! vault status 2>/dev/null | grep -q "Initialized.*true"; then
    echo -e "${RED}❌ Vault is not initialized${NC}"
    echo "Please run the vault setup script first: ./scripts/vault-setup.sh"
    exit 1
fi

# Check if vault is sealed
if vault status 2>/dev/null | grep -q "Sealed.*true"; then
    echo -e "${YELLOW}⚠️  Vault is sealed${NC}"
    echo "Please unseal Vault with your unseal keys:"
    echo "vault operator unseal [key1]"
    echo "vault operator unseal [key2]"
    echo "vault operator unseal [key3]"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Configure vault if not already configured
if [[ ! -f "/opt/shrutik/vault-token" ]]; then
    echo "Configuring Vault for Shrutik..."
    ./scripts/vault-configure.sh
else
    echo -e "${GREEN}✅ Vault already configured${NC}"
fi

# Step 4: Add R2 credentials to Vault (optional, interactive)
echo -e "${BLUE}☁️  Configuring cloud storage (optional)...${NC}"
if ! vault kv get secret/shrutik/r2 &>/dev/null; then
    echo -e "${YELLOW}R2 cloud storage not configured.${NC}"
    read -p "Do you want to configure R2 cloud storage now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./scripts/vault-add-r2.sh
    else
        echo "Skipping R2 configuration. You can configure it later with: ./scripts/vault-add-r2.sh"
    fi
else
    echo -e "${GREEN}✅ R2 cloud storage already configured${NC}"
fi

# Step 5: Configure Security Groups (reminder)
echo -e "${BLUE}🔒 Security Groups Configuration${NC}"
echo "Make sure your EC2 security group allows:"
echo "• HTTP (port 3080): 0.0.0.0/0"
echo "• SSH (port 22): Your IP only"
echo ""
echo "Your EC2 public IP:"
curl -s http://checkip.amazonaws.com/ || echo "Unable to get public IP"
echo ""

# Step 6: Configure Nginx for development
echo -e "${BLUE}🌐 Configuring Nginx for development...${NC}"
./scripts/nginx-config.sh setup-dev

# Step 7: Pull Docker image
echo -e "${BLUE}📥 Pulling Docker image from Docker Hub...${NC}"
docker pull $DOCKER_IMAGE

# Step 8: Create environment file from Vault
echo -e "${BLUE}🔐 Creating environment file from Vault...${NC}"
./scripts/vault-secrets.sh create-env

# Step 9: Stop existing containers (if any)
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
DOCKER_IMAGE=$DOCKER_IMAGE docker-compose down --remove-orphans 2>/dev/null || true

# Step 10: Start all services
echo -e "${BLUE}🚀 Starting all services...${NC}"
DOCKER_IMAGE=$DOCKER_IMAGE docker-compose up -d

# Step 11: Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 30

# Step 12: Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"
services=("postgres" "redis" "backend" "nginx")
all_healthy=true

for service in "${services[@]}"; do
    if DOCKER_IMAGE=$DOCKER_IMAGE docker-compose ps | grep -q "${service}.*Up"; then
        echo -e "${GREEN}✅ $service is running${NC}"
    else
        echo -e "${RED}❌ $service is not running${NC}"
        all_healthy=false
    fi
done

# Step 13: Test application endpoints
echo -e "${BLUE}🧪 Testing application endpoints...${NC}"
sleep 10

# Test health endpoint
if curl -f -s http://localhost:3080/health > /dev/null; then
    echo -e "${GREEN}✅ Health endpoint responding${NC}"
else
    echo -e "${YELLOW}⚠️  Health endpoint not responding yet${NC}"
fi

# Test API docs
if curl -f -s http://localhost:3080/api/docs > /dev/null; then
    echo -e "${GREEN}✅ API documentation accessible${NC}"
else
    echo -e "${YELLOW}⚠️  API documentation not accessible yet${NC}"
fi

# Get public IP for display
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com/ || echo "UNKNOWN")

# Display deployment status
echo ""
if $all_healthy; then
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Deployment completed with some issues${NC}"
fi

echo "=============================================="
echo -e "${BLUE}🌐 Access Your Application:${NC}"
echo "• Main Application: http://$PUBLIC_IP:3080/"
echo "• API Documentation: http://$PUBLIC_IP:3080/api/docs"
echo "• Admin Panel (Flower): http://$PUBLIC_IP:3080/admin/flower/"
echo "• Health Check: http://$PUBLIC_IP:3080/health"
echo ""

echo -e "${BLUE}📊 Services Status:${NC}"
DOCKER_IMAGE=$DOCKER_IMAGE docker-compose ps

# Get secrets for display
if [[ -f ".env.prod" ]]; then
    source .env.prod
    echo ""
    echo -e "${BLUE}🔑 Admin Credentials:${NC}"
    echo "• Flower Monitor: admin:$FLOWER_PASSWORD"
fi

echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  View logs: docker-compose logs -f [service]"
echo "  Restart: docker-compose restart [service]"
echo "  Stop all: docker-compose stop"
echo "  Start all: docker-compose start"
echo "  Update image: docker-compose pull && docker-compose up -d"
echo ""

echo -e "${BLUE}🔐 Vault Information:${NC}"
echo "• Vault UI: http://localhost:8200 (local access only)"
echo "• Vault token file: /opt/shrutik/vault-token"
echo "• View secrets: vault kv get secret/shrutik/[path]"
echo ""

echo -e "${YELLOW}⚠️  Important Reminders:${NC}"
echo "• Keep your Vault unseal keys secure"
echo "• Backup /opt/vault/data regularly"
echo "• Monitor logs: docker-compose logs -f"
echo "• If EC2 restarts, you'll need to unseal Vault"
echo ""

echo -e "${GREEN}🎊 Your Shrutik application is now live!${NC}"
echo "Share this URL with your co-founder: http://$PUBLIC_IP:3080/"