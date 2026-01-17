#!/bin/bash

# Nginx Configuration Management Script
# Manages nginx configurations for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NGINX_DIR="$PROJECT_DIR/nginx"

show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup-dev     Set up nginx for development (HTTP only)"
    echo "  setup-prod    Set up nginx for production (HTTPS with SSL)"
    echo "  validate      Validate nginx configuration"
    echo "  reload        Reload nginx configuration"
    echo "  status        Show nginx status"
    echo "  logs          Show nginx logs"
    echo ""
    echo "Options:"
    echo "  -d, --domain DOMAIN    Set domain name for production setup"
    echo "  -h, --help            Show this help message"
}

validate_config() {
    echo -e "${BLUE}🔍 Validating nginx configuration...${NC}"
    
    if docker-compose -f docker-compose.prod.yml exec nginx nginx -t 2>/dev/null; then
        echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
        return 0
    else
        echo -e "${RED}❌ Nginx configuration has errors${NC}"
        return 1
    fi
}

setup_development() {
    echo -e "${BLUE}🔧 Setting up nginx for development environment...${NC}"
    
    # Copy development configuration
    cp "$NGINX_DIR/sites-available/shrutik-dev.conf" "$NGINX_DIR/sites-available/default.conf"
    
    echo -e "${GREEN}✅ Development configuration activated${NC}"
    echo "Configuration: HTTP only, no SSL required"
    echo "Access: http://localhost/"
}

setup_production() {
    local domain="$1"
    
    if [ -z "$domain" ]; then
        echo -e "${RED}❌ Domain name is required for production setup${NC}"
        echo "Usage: $0 setup-prod -d your-domain.com"
        exit 1
    fi
    
    echo -e "${BLUE}🔧 Setting up nginx for production environment...${NC}"
    echo "Domain: $domain"
    
    # Replace domain placeholder in production config
    sed "s/\${DOMAIN_NAME}/$domain/g" "$NGINX_DIR/sites-available/shrutik.conf" > "$NGINX_DIR/sites-available/default.conf"
    
    # Create SSL directory structure
    mkdir -p "$NGINX_DIR/ssl/live/$domain"
    
    # Create placeholder SSL certificates (will be replaced by Let's Encrypt)
    if [ ! -f "$NGINX_DIR/ssl/live/$domain/fullchain.pem" ]; then
        echo -e "${YELLOW}⚠️  Creating placeholder SSL certificates...${NC}"
        openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
            -keyout "$NGINX_DIR/ssl/live/$domain/privkey.pem" \
            -out "$NGINX_DIR/ssl/live/$domain/fullchain.pem" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$domain" 2>/dev/null
        
        cp "$NGINX_DIR/ssl/live/$domain/fullchain.pem" "$NGINX_DIR/ssl/live/$domain/chain.pem"
    fi
    
    echo -e "${GREEN}✅ Production configuration activated${NC}"
    echo "Configuration: HTTPS with SSL certificates"
    echo "Domain: https://$domain/"
    echo ""
    echo -e "${YELLOW}⚠️  Next steps:${NC}"
    echo "1. Run SSL setup script: ./scripts/ssl-setup.sh -d $domain"
    echo "2. Update DNS records to point to this server"
    echo "3. Test configuration: ./scripts/nginx-config.sh validate"
}

reload_nginx() {
    echo -e "${BLUE}🔄 Reloading nginx configuration...${NC}"
    
    if docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload 2>/dev/null; then
        echo -e "${GREEN}✅ Nginx configuration reloaded${NC}"
    else
        echo -e "${RED}❌ Failed to reload nginx configuration${NC}"
        echo "Check logs: docker-compose -f docker-compose.prod.yml logs nginx"
        exit 1
    fi
}

show_status() {
    echo -e "${BLUE}📊 Nginx Status${NC}"
    echo "===================="
    
    # Check if nginx container is running
    if docker-compose -f docker-compose.prod.yml ps nginx | grep -q "Up"; then
        echo -e "${GREEN}✅ Nginx container is running${NC}"
        
        # Show configuration file in use
        echo ""
        echo "Active configuration:"
        if [ -f "$NGINX_DIR/sites-available/default.conf" ]; then
            if grep -q "ssl_certificate" "$NGINX_DIR/sites-available/default.conf"; then
                echo "  - Production (HTTPS)"
            else
                echo "  - Development (HTTP)"
            fi
        else
            echo "  - No configuration found"
        fi
        
        # Show listening ports
        echo ""
        echo "Listening ports:"
        docker-compose -f docker-compose.prod.yml port nginx 80 2>/dev/null && echo "  - HTTP: $(docker-compose -f docker-compose.prod.yml port nginx 80)"
        docker-compose -f docker-compose.prod.yml port nginx 443 2>/dev/null && echo "  - HTTPS: $(docker-compose -f docker-compose.prod.yml port nginx 443)"
        
    else
        echo -e "${RED}❌ Nginx container is not running${NC}"
        echo "Start with: docker-compose -f docker-compose.prod.yml up -d nginx"
    fi
}

show_logs() {
    echo -e "${BLUE}📋 Nginx Logs${NC}"
    echo "=============="
    docker-compose -f docker-compose.prod.yml logs --tail=50 nginx
}

# Parse command line arguments
COMMAND=""
DOMAIN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        setup-dev|setup-prod|validate|reload|status|logs)
            COMMAND="$1"
            shift
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Execute command
case "$COMMAND" in
    setup-dev)
        setup_development
        ;;
    setup-prod)
        setup_production "$DOMAIN"
        ;;
    validate)
        validate_config
        ;;
    reload)
        reload_nginx
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    "")
        echo -e "${RED}❌ No command specified${NC}"
        show_usage
        exit 1
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        show_usage
        exit 1
        ;;
esac