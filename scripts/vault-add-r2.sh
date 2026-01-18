#!/bin/bash

# Add R2 Credentials to Vault
# Usage: ./scripts/vault-add-r2.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 Adding R2 Credentials to Vault${NC}"
echo "=================================="

# Set vault address
export VAULT_ADDR='http://127.0.0.1:8200'

# Load vault token
VAULT_TOKEN_FILE='/opt/shrutik/vault-token'
if [[ ! -f "$VAULT_TOKEN_FILE" ]]; then
    echo -e "${RED}❌ Vault token file not found: $VAULT_TOKEN_FILE${NC}"
    echo "Run: ./scripts/vault-configure.sh"
    exit 1
fi

export VAULT_TOKEN=$(cat $VAULT_TOKEN_FILE)

# Prompt for R2 credentials
echo -e "${BLUE}Please enter your Cloudflare R2 credentials:${NC}"
echo ""

read -p "R2 Account ID: " R2_ACCOUNT_ID
read -p "R2 Access Key ID: " R2_ACCESS_KEY_ID
read -s -p "R2 Secret Access Key: " R2_SECRET_ACCESS_KEY
echo ""
read -p "R2 Bucket Name: " R2_BUCKET_NAME

# Generate endpoint URL
R2_ENDPOINT_URL="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

echo ""
echo -e "${BLUE}📝 Summary:${NC}"
echo "Account ID: $R2_ACCOUNT_ID"
echo "Access Key ID: $R2_ACCESS_KEY_ID"
echo "Secret Access Key: [HIDDEN]"
echo "Bucket Name: $R2_BUCKET_NAME"
echo "Endpoint URL: $R2_ENDPOINT_URL"
echo ""

read -p "Save these credentials to Vault? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo -e "${YELLOW}❌ Cancelled${NC}"
    exit 0
fi

# Store R2 credentials in Vault
echo -e "${BLUE}💾 Storing R2 credentials in Vault...${NC}"
vault kv put secret/shrutik/r2 \
  account_id="$R2_ACCOUNT_ID" \
  access_key_id="$R2_ACCESS_KEY_ID" \
  secret_access_key="$R2_SECRET_ACCESS_KEY" \
  bucket_name="$R2_BUCKET_NAME" \
  endpoint_url="$R2_ENDPOINT_URL"

# Store export configuration
echo -e "${BLUE}⚙️  Setting export configuration...${NC}"
vault kv put secret/shrutik/export \
  storage_type="r2" \
  batch_size="200" \
  compression_level="3" \
  max_chunk_size_mb="50" \
  daily_download_limit="2"

echo -e "${GREEN}✅ R2 credentials stored in Vault${NC}"

# Test the credentials
echo -e "${BLUE}🧪 Testing R2 credentials...${NC}"
if vault kv get -field=account_id secret/shrutik/r2 &>/dev/null; then
    echo -e "${GREEN}✅ R2 credentials test passed${NC}"
else
    echo -e "${RED}❌ R2 credentials test failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 R2 setup completed!${NC}"
echo "=================================="
echo -e "${BLUE}Next steps:${NC}"
echo "1. Deploy with R2: ./scripts/deploy-with-vault-hub.sh your-username latest"
echo "2. Your app will now use R2 for export storage"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "• View R2 config: vault kv get secret/shrutik/r2"
echo "• Update R2 config: vault kv patch secret/shrutik/r2 key=value"
echo "• Test deployment: ./scripts/vault-secrets.sh create-env && cat .env.prod"