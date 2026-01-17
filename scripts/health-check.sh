#!/bin/bash

# Health Check Script for Production Deployment
# Validates that all services are running correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 Shrutik Production Health Check${NC}"
echo "=================================="

# Check if docker-compose is running
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${RED}❌ No services are running${NC}"
    echo "Start services with: docker-compose -f docker-compose.prod.yml up -d"
    exit 1
fi

# Function to check service health
check_service_health() {
    local service=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Unhealthy${NC}"
        return 1
    fi
}

# Check individual services
echo -e "${BLUE}Service Health Checks:${NC}"

# Check backend health endpoint
check_service_health "Backend API" "http://localhost:8000/health" || true

# Check frontend (through nginx if configured, otherwise direct)
check_service_health "Frontend" "http://localhost:3000/health" || check_service_health "Frontend" "http://localhost:3000/" || true

# Check Flower monitoring
check_service_health "Flower Monitor" "http://localhost:5555/" || true

# Check database connectivity
echo -n "Checking PostgreSQL... "
if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U production_user >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# Check Redis connectivity
echo -n "Checking Redis... "
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# Check Celery workers
echo -n "Checking Celery workers... "
if docker-compose -f docker-compose.prod.yml logs celery 2>/dev/null | grep -q "ready"; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${YELLOW}⚠️  Check logs${NC}"
fi

# Check disk space
echo -e "${BLUE}System Resources:${NC}"
echo -n "Disk space: "
df -h . | awk 'NR==2 {print $4 " available (" $5 " used)"}'

# Check memory usage
echo -n "Memory usage: "
free -h | awk 'NR==2{printf "%.1f%% used\n", $3/$2*100}'

# Check Docker container status
echo -e "${BLUE}Container Status:${NC}"
docker-compose -f docker-compose.prod.yml ps

# Check recent logs for errors
echo -e "${BLUE}Recent Error Check:${NC}"
error_count=$(docker-compose -f docker-compose.prod.yml logs --since="5m" 2>/dev/null | grep -i error | wc -l)
if [ "$error_count" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $error_count errors in last 5 minutes${NC}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs"
else
    echo -e "${GREEN}✅ No recent errors found${NC}"
fi

echo ""
echo -e "${GREEN}Health check completed!${NC}"