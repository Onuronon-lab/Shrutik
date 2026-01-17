#!/bin/bash

# Nginx Configuration Test Script
# Tests nginx configuration without starting full services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Nginx Configuration${NC}"
echo "================================="

# Test nginx configuration syntax
echo -e "${BLUE}Testing configuration syntax...${NC}"
echo -e "${YELLOW}⚠️  Skipping syntax test (requires full nginx environment)${NC}"
echo -e "${GREEN}✅ Configuration files will be validated when nginx starts${NC}"

# Test configuration files exist
echo -e "${BLUE}Checking configuration files...${NC}"

required_files=(
    "nginx/nginx.conf"
    "nginx/sites-available/shrutik.conf"
    "nginx/sites-available/shrutik-dev.conf"
    "nginx/error-pages.conf"
    "nginx/html/error/404.html"
    "nginx/html/error/50x.html"
    "nginx/html/error/403.html"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file (missing)${NC}"
    fi
done

# Test SSL directory structure
echo -e "${BLUE}Checking SSL directory structure...${NC}"
if [ -d "nginx/ssl" ]; then
    echo -e "${GREEN}✅ SSL directory exists${NC}"
else
    echo -e "${YELLOW}⚠️  SSL directory missing (will be created during setup)${NC}"
fi

# Test rate limiting configuration
echo -e "${BLUE}Checking rate limiting zones...${NC}"
if grep -q "limit_req_zone" nginx/nginx.conf; then
    echo -e "${GREEN}✅ Rate limiting zones configured${NC}"
else
    echo -e "${RED}❌ Rate limiting zones not found${NC}"
fi

# Test security headers
echo -e "${BLUE}Checking security headers...${NC}"
if grep -q "X-Frame-Options" nginx/nginx.conf; then
    echo -e "${GREEN}✅ Security headers configured${NC}"
else
    echo -e "${RED}❌ Security headers not found${NC}"
fi

# Test upstream definitions
echo -e "${BLUE}Checking upstream definitions...${NC}"
if grep -q "upstream backend" nginx/sites-available/shrutik.conf; then
    echo -e "${GREEN}✅ Backend upstream configured${NC}"
else
    echo -e "${RED}❌ Backend upstream not found${NC}"
fi

if grep -q "upstream frontend" nginx/sites-available/shrutik.conf; then
    echo -e "${GREEN}✅ Frontend upstream configured${NC}"
else
    echo -e "${RED}❌ Frontend upstream not found${NC}"
fi

if grep -q "upstream flower" nginx/sites-available/shrutik.conf; then
    echo -e "${GREEN}✅ Flower upstream configured${NC}"
else
    echo -e "${RED}❌ Flower upstream not found${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Nginx configuration test completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Set up for development: ./scripts/nginx-config.sh setup-dev"
echo "2. Set up for production: ./scripts/nginx-config.sh setup-prod -d your-domain.com"
echo "3. Start services: docker-compose -f docker-compose.prod.yml up -d"