#!/bin/bash

# Vault Configuration Script for Shrutik
# Run this after vault is initialized and unsealed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}⚙️  Configuring Vault for Shrutik${NC}"
echo "=================================="

# Set vault address
export VAULT_ADDR='http://127.0.0.1:8200'

# Check if vault is unsealed
if ! vault status | grep -q "Sealed.*false"; then
    echo -e "${RED}❌ Vault is sealed. Please unseal it first:${NC}"
    echo "vault operator unseal"
    exit 1
fi

# Check authentication (use existing token from vault login)
echo -e "${BLUE}🔐 Checking Vault authentication...${NC}"
if ! vault token lookup &>/dev/null; then
    echo -e "${RED}❌ Not authenticated with Vault${NC}"
    echo -e "${YELLOW}Please run: vault login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Authenticated with Vault${NC}"

# Enable KV secrets engine
echo -e "${BLUE}🔧 Enabling KV secrets engine...${NC}"
if vault secrets list | grep -q "secret/"; then
    echo -e "${GREEN}✅ KV secrets engine already enabled${NC}"
else
    vault secrets enable -path=secret kv-v2
    echo -e "${GREEN}✅ KV secrets engine enabled${NC}"
fi

# Create policy for Shrutik
echo -e "${BLUE}📋 Creating Shrutik policy...${NC}"
vault policy write shrutik-policy - << 'EOF'
# Policy for Shrutik application
path "secret/data/shrutik/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/shrutik/*" {
  capabilities = ["list", "delete"]
}
EOF

echo -e "${GREEN}✅ Shrutik policy created${NC}"

# Generate secrets
echo -e "${BLUE}🔐 Generating and storing secrets...${NC}"

# Database secrets
POSTGRES_PASSWORD=$(openssl rand -base64 32)
vault kv put secret/shrutik/database \
  postgres_password="$POSTGRES_PASSWORD" \
  postgres_user="production_user" \
  postgres_db="voice_collection"

# Application secrets
SECRET_KEY=$(openssl rand -base64 64)
vault kv put secret/shrutik/app \
  secret_key="$SECRET_KEY" \
  debug="false"

# Monitoring secrets
FLOWER_PASSWORD=$(openssl rand -base64 16)
vault kv put secret/shrutik/monitoring \
  flower_username="admin" \
  flower_password="$FLOWER_PASSWORD"

# Domain configuration (you can update this later)
vault kv put secret/shrutik/domain \
  domain_name="your-domain.com" \
  ssl_email="admin@your-domain.com"

echo -e "${GREEN}✅ Secrets stored in Vault${NC}"

# Create application token
echo -e "${BLUE}🎫 Creating application token...${NC}"
APP_TOKEN=$(vault token create -policy=shrutik-policy -ttl=8760h -display-name="shrutik-app" -format=json | jq -r '.auth.client_token')

# Save token to file (secure permissions)
echo "$APP_TOKEN" > /opt/shrutik/vault-token
chmod 600 /opt/shrutik/vault-token
sudo chown $(whoami):$(whoami) /opt/shrutik/vault-token

echo -e "${GREEN}✅ Application token created and saved${NC}"

# Test reading secrets
echo -e "${BLUE}🧪 Testing secret retrieval...${NC}"
export VAULT_TOKEN=$APP_TOKEN

if vault kv get -field=postgres_password secret/shrutik/database &>/dev/null; then
    echo -e "${GREEN}✅ Secret retrieval test passed${NC}"
else
    echo -e "${RED}❌ Secret retrieval test failed${NC}"
    exit 1
fi

# Display summary
echo ""
echo -e "${GREEN}🎉 Vault configuration completed!${NC}"
echo "=================================="
echo -e "${BLUE}Summary:${NC}"
echo "• Vault is running on http://127.0.0.1:8200"
echo "• Secrets stored under secret/shrutik/"
echo "• Application token saved to /opt/shrutik/vault-token"
echo ""
echo -e "${BLUE}Generated credentials:${NC}"
echo "• Database password: $POSTGRES_PASSWORD"
echo "• Flower admin: admin:$FLOWER_PASSWORD"
echo ""
echo -e "${YELLOW}⚠️  Save these credentials securely!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Update domain: vault kv patch secret/shrutik/domain domain_name=your-actual-domain.com"
echo "2. Run deployment: ./scripts/deploy-with-vault.sh"