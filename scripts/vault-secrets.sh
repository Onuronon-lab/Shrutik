#!/bin/bash

# Vault Secrets Management Script for Shrutik
# Retrieves secrets from Vault and manages environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Vault configuration
VAULT_ADDR='http://127.0.0.1:8200'
VAULT_TOKEN_FILE='/opt/shrutik/vault-token'

# Check if vault is available
check_vault() {
    if ! command -v vault &> /dev/null; then
        echo -e "${RED}❌ Vault not installed${NC}"
        exit 1
    fi
    
    if ! curl -s $VAULT_ADDR/v1/sys/health &>/dev/null; then
        echo -e "${RED}❌ Vault is not running or not accessible${NC}"
        echo "Start vault: sudo systemctl start vault"
        exit 1
    fi
    
    if ! vault status | grep -q "Sealed.*false"; then
        echo -e "${RED}❌ Vault is sealed${NC}"
        echo "Unseal vault: vault operator unseal"
        exit 1
    fi
}

# Load vault token
load_token() {
    if [[ ! -f "$VAULT_TOKEN_FILE" ]]; then
        echo -e "${RED}❌ Vault token file not found: $VAULT_TOKEN_FILE${NC}"
        echo "Run: ./scripts/vault-configure.sh"
        exit 1
    fi
    
    export VAULT_ADDR
    export VAULT_TOKEN=$(cat $VAULT_TOKEN_FILE)
}

# Get secret from vault
get_secret() {
    local path="$1"
    local field="$2"
    
    vault kv get -field="$field" "secret/shrutik/$path" 2>/dev/null || {
        echo -e "${RED}❌ Failed to retrieve $path/$field${NC}"
        exit 1
    }
}

# Export all secrets as environment variables (silent version for sourcing)
export_secrets_silent() {
    check_vault >/dev/null 2>&1
    load_token
    
    # Database secrets
    POSTGRES_DB=$(get_secret "database" "postgres_db")
    POSTGRES_USER=$(get_secret "database" "postgres_user")
    POSTGRES_PASSWORD=$(get_secret "database" "postgres_password")
    echo "export POSTGRES_DB='$POSTGRES_DB'"
    echo "export POSTGRES_USER='$POSTGRES_USER'"
    echo "export POSTGRES_PASSWORD='$POSTGRES_PASSWORD'"
    echo "export DATABASE_URL='postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$POSTGRES_DB'"
    
    # Application secrets
    SECRET_KEY=$(get_secret "app" "secret_key")
    DEBUG=$(get_secret "app" "debug")
    echo "export SECRET_KEY='$SECRET_KEY'"
    echo "export DEBUG='$DEBUG'"
    
    # Monitoring secrets
    FLOWER_USERNAME=$(get_secret "monitoring" "flower_username")
    FLOWER_PASSWORD=$(get_secret "monitoring" "flower_password")
    echo "export FLOWER_USERNAME='$FLOWER_USERNAME'"
    echo "export FLOWER_PASSWORD='$FLOWER_PASSWORD'"
    echo "export FLOWER_BASIC_AUTH='$FLOWER_USERNAME:$FLOWER_PASSWORD'"
    
    # Domain configuration
    DOMAIN_NAME=$(get_secret "domain" "domain_name")
    SSL_EMAIL=$(get_secret "domain" "ssl_email")
    echo "export DOMAIN_NAME='$DOMAIN_NAME'"
    echo "export SSL_EMAIL='$SSL_EMAIL'"
    
    # Additional configuration
    echo "export REDIS_URL='redis://redis:6379/0'"
    echo "export UPLOAD_DIR='/app/uploads'"
    echo "export EXPORT_DIR='/app/exports'"
    
    # R2 Configuration (if available)
    if vault kv get secret/shrutik/r2 &>/dev/null; then
        echo "export EXPORT_STORAGE_TYPE='r2'"
        R2_ACCOUNT_ID=$(get_secret "r2" "account_id")
        R2_ACCESS_KEY_ID=$(get_secret "r2" "access_key_id")
        R2_SECRET_ACCESS_KEY=$(get_secret "r2" "secret_access_key")
        R2_BUCKET_NAME=$(get_secret "r2" "bucket_name")
        R2_ENDPOINT_URL=$(get_secret "r2" "endpoint_url")
        echo "export R2_ACCOUNT_ID='$R2_ACCOUNT_ID'"
        echo "export R2_ACCESS_KEY_ID='$R2_ACCESS_KEY_ID'"
        echo "export R2_SECRET_ACCESS_KEY='$R2_SECRET_ACCESS_KEY'"
        echo "export R2_BUCKET_NAME='$R2_BUCKET_NAME'"
        echo "export R2_ENDPOINT_URL='$R2_ENDPOINT_URL'"
    else
        echo "export EXPORT_STORAGE_TYPE='local'"
    fi
    
    # Export Configuration (if available)
    if vault kv get secret/shrutik/export &>/dev/null; then
        EXPORT_BATCH_SIZE=$(get_secret "export" "batch_size")
        EXPORT_COMPRESSION_LEVEL=$(get_secret "export" "compression_level")
        EXPORT_MAX_CHUNK_SIZE_MB=$(get_secret "export" "max_chunk_size_mb")
        EXPORT_DAILY_DOWNLOAD_LIMIT=$(get_secret "export" "daily_download_limit")
    else
        EXPORT_BATCH_SIZE="200"
        EXPORT_COMPRESSION_LEVEL="3"
        EXPORT_MAX_CHUNK_SIZE_MB="50"
        EXPORT_DAILY_DOWNLOAD_LIMIT="2"
    fi
    
    echo "export EXPORT_BATCH_SIZE='$EXPORT_BATCH_SIZE'"
    echo "export EXPORT_COMPRESSION_LEVEL='$EXPORT_COMPRESSION_LEVEL'"
    echo "export EXPORT_MAX_CHUNK_SIZE_MB='$EXPORT_MAX_CHUNK_SIZE_MB'"
    echo "export EXPORT_DAILY_DOWNLOAD_LIMIT='$EXPORT_DAILY_DOWNLOAD_LIMIT'"
    
    echo "export ALLOWED_HOSTS='[\"https://$DOMAIN_NAME\", \"https://www.$DOMAIN_NAME\"]'"
    echo "export CORS_ALLOWED_ORIGINS='https://$DOMAIN_NAME,https://www.$DOMAIN_NAME'"
}

# Export all secrets as environment variables
export_secrets() {
    # Only show messages if not being sourced (for interactive use)
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        echo -e "${BLUE}🔐 Loading secrets from Vault...${NC}"
    fi
    
    check_vault
    load_token
    
    # Database secrets
    export POSTGRES_DB=$(get_secret "database" "postgres_db")
    export POSTGRES_USER=$(get_secret "database" "postgres_user")
    export POSTGRES_PASSWORD=$(get_secret "database" "postgres_password")
    export DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$POSTGRES_DB"
    
    # Application secrets
    export SECRET_KEY=$(get_secret "app" "secret_key")
    export DEBUG=$(get_secret "app" "debug")
    
    # Monitoring secrets
    export FLOWER_USERNAME=$(get_secret "monitoring" "flower_username")
    export FLOWER_PASSWORD=$(get_secret "monitoring" "flower_password")
    export FLOWER_BASIC_AUTH="$FLOWER_USERNAME:$FLOWER_PASSWORD"
    
    # Domain configuration
    export DOMAIN_NAME=$(get_secret "domain" "domain_name")
    export SSL_EMAIL=$(get_secret "domain" "ssl_email")
    
    # Additional configuration
    export REDIS_URL="redis://redis:6379/0"
    export UPLOAD_DIR="/app/uploads"
    export EXPORT_DIR="/app/exports"
    
    # R2 Configuration (if available)
    if vault kv get secret/shrutik/r2 &>/dev/null; then
        export EXPORT_STORAGE_TYPE="r2"
        export R2_ACCOUNT_ID=$(get_secret "r2" "account_id")
        export R2_ACCESS_KEY_ID=$(get_secret "r2" "access_key_id")
        export R2_SECRET_ACCESS_KEY=$(get_secret "r2" "secret_access_key")
        export R2_BUCKET_NAME=$(get_secret "r2" "bucket_name")
        export R2_ENDPOINT_URL=$(get_secret "r2" "endpoint_url")
    else
        export EXPORT_STORAGE_TYPE="local"
    fi
    
    # Export Configuration (if available)
    if vault kv get secret/shrutik/export &>/dev/null; then
        export EXPORT_BATCH_SIZE=$(get_secret "export" "batch_size")
        export EXPORT_COMPRESSION_LEVEL=$(get_secret "export" "compression_level")
        export EXPORT_MAX_CHUNK_SIZE_MB=$(get_secret "export" "max_chunk_size_mb")
        export EXPORT_DAILY_DOWNLOAD_LIMIT=$(get_secret "export" "daily_download_limit")
    else
        export EXPORT_BATCH_SIZE="200"
        export EXPORT_COMPRESSION_LEVEL="3"
        export EXPORT_MAX_CHUNK_SIZE_MB="50"
        export EXPORT_DAILY_DOWNLOAD_LIMIT="2"
    fi
    
    export ALLOWED_HOSTS="[\"https://$DOMAIN_NAME\", \"https://www.$DOMAIN_NAME\"]"
    export CORS_ALLOWED_ORIGINS="https://$DOMAIN_NAME,https://www.$DOMAIN_NAME"
    
    # Only show success message if not being sourced
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        echo -e "${GREEN}✅ Secrets loaded from Vault${NC}"
    fi
}

# Create .env file from vault secrets
create_env_file() {
    echo -e "${BLUE}📝 Creating .env.prod from Vault...${NC}"
    
    check_vault
    load_token
    
    # Get secrets
    POSTGRES_DB=$(get_secret "database" "postgres_db")
    POSTGRES_USER=$(get_secret "database" "postgres_user")
    POSTGRES_PASSWORD=$(get_secret "database" "postgres_password")
    SECRET_KEY=$(get_secret "app" "secret_key")
    DEBUG=$(get_secret "app" "debug")
    FLOWER_USERNAME=$(get_secret "monitoring" "flower_username")
    FLOWER_PASSWORD=$(get_secret "monitoring" "flower_password")
    DOMAIN_NAME=$(get_secret "domain" "domain_name")
    SSL_EMAIL=$(get_secret "domain" "ssl_email")
    
    # Create .env file
    cat > .env.prod << EOF
# Generated from Vault - $(date)
# DO NOT EDIT - Use vault to update secrets

# Database Configuration
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$POSTGRES_DB

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Configuration
DEBUG=$DEBUG
SECRET_KEY=$SECRET_KEY

# Domain Configuration
DOMAIN_NAME=$DOMAIN_NAME
SSL_EMAIL=$SSL_EMAIL
ALLOWED_HOSTS=["https://$DOMAIN_NAME", "https://www.$DOMAIN_NAME"]
CORS_ALLOWED_ORIGINS=https://$DOMAIN_NAME,https://www.$DOMAIN_NAME

# Monitoring Configuration
FLOWER_BASIC_AUTH=$FLOWER_USERNAME:$FLOWER_PASSWORD

# File Storage Configuration
UPLOAD_DIR=/app/uploads
EXPORT_DIR=/app/exports

# R2 Configuration (if available)
EOF

    # Add R2 configuration if available
    if vault kv get secret/shrutik/r2 &>/dev/null; then
        R2_ACCOUNT_ID=$(get_secret "r2" "account_id")
        R2_ACCESS_KEY_ID=$(get_secret "r2" "access_key_id")
        R2_SECRET_ACCESS_KEY=$(get_secret "r2" "secret_access_key")
        R2_BUCKET_NAME=$(get_secret "r2" "bucket_name")
        R2_ENDPOINT_URL=$(get_secret "r2" "endpoint_url")
        
        cat >> .env.prod << EOF
EXPORT_STORAGE_TYPE=r2
R2_ACCOUNT_ID=$R2_ACCOUNT_ID
R2_ACCESS_KEY_ID=$R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY=$R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME=$R2_BUCKET_NAME
R2_ENDPOINT_URL=$R2_ENDPOINT_URL
EOF
    else
        cat >> .env.prod << EOF
EXPORT_STORAGE_TYPE=local
EOF
    fi

    # Add export configuration
    if vault kv get secret/shrutik/export &>/dev/null; then
        EXPORT_BATCH_SIZE=$(get_secret "export" "batch_size")
        EXPORT_COMPRESSION_LEVEL=$(get_secret "export" "compression_level")
        EXPORT_MAX_CHUNK_SIZE_MB=$(get_secret "export" "max_chunk_size_mb")
        EXPORT_DAILY_DOWNLOAD_LIMIT=$(get_secret "export" "daily_download_limit")
    else
        EXPORT_BATCH_SIZE="200"
        EXPORT_COMPRESSION_LEVEL="3"
        EXPORT_MAX_CHUNK_SIZE_MB="50"
        EXPORT_DAILY_DOWNLOAD_LIMIT="2"
    fi
    
    cat >> .env.prod << EOF

# Export Configuration
EXPORT_BATCH_SIZE=$EXPORT_BATCH_SIZE
EXPORT_COMPRESSION_LEVEL=$EXPORT_COMPRESSION_LEVEL
EXPORT_MAX_CHUNK_SIZE_MB=$EXPORT_MAX_CHUNK_SIZE_MB
EXPORT_DAILY_DOWNLOAD_LIMIT=$EXPORT_DAILY_DOWNLOAD_LIMIT
EXPORT_SCHEDULE_CRON=0 2 * * *
EXPORT_MIN_CHUNKS_THRESHOLD=200
EOF

    # Secure the file
    chmod 600 .env.prod
    
    echo -e "${GREEN}✅ .env.prod created with secure permissions${NC}"
}

# List all secrets
list_secrets() {
    echo -e "${BLUE}📋 Listing Shrutik secrets in Vault...${NC}"
    
    check_vault
    load_token
    
    echo -e "${BLUE}Database secrets:${NC}"
    vault kv get secret/shrutik/database
    
    echo -e "${BLUE}Application secrets:${NC}"
    vault kv get secret/shrutik/app
    
    echo -e "${BLUE}Monitoring secrets:${NC}"
    vault kv get secret/shrutik/monitoring
    
    echo -e "${BLUE}Domain configuration:${NC}"
    vault kv get secret/shrutik/domain
    
    echo -e "${BLUE}R2 configuration:${NC}"
    if vault kv get secret/shrutik/r2 &>/dev/null; then
        vault kv get secret/shrutik/r2
    else
        echo "R2 secrets not configured"
    fi
    
    echo -e "${BLUE}Export configuration:${NC}"
    if vault kv get secret/shrutik/export &>/dev/null; then
        vault kv get secret/shrutik/export
    else
        echo "Export secrets not configured"
    fi
}

# Update domain configuration
update_domain() {
    local domain="$1"
    local email="$2"
    
    if [[ -z "$domain" ]]; then
        echo -e "${RED}❌ Domain name required${NC}"
        echo "Usage: $0 update-domain your-domain.com admin@your-domain.com"
        exit 1
    fi
    
    if [[ -z "$email" ]]; then
        email="admin@$domain"
    fi
    
    echo -e "${BLUE}🌐 Updating domain configuration...${NC}"
    
    check_vault
    load_token
    
    vault kv patch secret/shrutik/domain \
        domain_name="$domain" \
        ssl_email="$email"
    
    echo -e "${GREEN}✅ Domain updated: $domain${NC}"
}

# Test vault connectivity
test_vault() {
    echo -e "${BLUE}🧪 Testing Vault connectivity...${NC}"
    
    check_vault
    load_token
    
    # Test reading a secret
    if get_secret "database" "postgres_password" &>/dev/null; then
        echo -e "${GREEN}✅ Vault connectivity test passed${NC}"
    else
        echo -e "${RED}❌ Vault connectivity test failed${NC}"
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  export              Export secrets as environment variables"
    echo "  create-env          Create .env.prod file from Vault"
    echo "  list                List all secrets in Vault"
    echo "  update-domain       Update domain configuration"
    echo "  test                Test Vault connectivity"
    echo ""
    echo "Examples:"
    echo "  $0 create-env"
    echo "  $0 update-domain your-domain.com admin@your-domain.com"
    echo "  $0 export && docker-compose up -d"
}

# Main script logic
case "$1" in
    "export")
        export_secrets
        ;;
    "export-silent")
        export_secrets_silent
        ;;
    "create-env")
        create_env_file
        ;;
    "list")
        list_secrets
        ;;
    "update-domain")
        update_domain "$2" "$3"
        ;;
    "test")
        test_vault
        ;;
    "")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac