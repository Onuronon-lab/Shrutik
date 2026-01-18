#!/bin/bash

# Debug script for Vault token issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Vault Debug Script${NC}"
echo "===================="

# Set vault address
export VAULT_ADDR='http://127.0.0.1:8200'
echo -e "${BLUE}Vault Address: $VAULT_ADDR${NC}"

# Check if vault is running
echo -e "${BLUE}Checking Vault status...${NC}"
if ! vault status; then
    echo -e "${RED}❌ Cannot connect to Vault${NC}"
    exit 1
fi

# Check if vault is unsealed
echo -e "${BLUE}Checking if Vault is unsealed...${NC}"
if vault status | grep -q "Sealed.*true"; then
    echo -e "${RED}❌ Vault is sealed. Please unseal it first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Vault is running and unsealed${NC}"

# Prompt for root token
echo -e "${YELLOW}Enter your Vault root token:${NC}"
read -s ROOT_TOKEN

# Set token and test
export VAULT_TOKEN="$ROOT_TOKEN"
echo -e "${BLUE}Testing token authentication...${NC}"

# Debug: Show token length (without revealing it)
echo -e "${BLUE}Token length: ${#ROOT_TOKEN} characters${NC}"

# Test token lookup with verbose output
echo -e "${BLUE}Running: vault token lookup${NC}"
if vault token lookup; then
    echo -e "${GREEN}✅ Token is valid!${NC}"
else
    echo -e "${RED}❌ Token lookup failed${NC}"
    echo -e "${YELLOW}Possible issues:${NC}"
    echo "1. Token is incorrect"
    echo "2. Token has expired"
    echo "3. Vault connection issue"
    exit 1
fi

echo -e "${GREEN}🎉 Debug completed successfully!${NC}"