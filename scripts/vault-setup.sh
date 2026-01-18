#!/bin/bash

# Vault Setup Script for Shrutik
# Run this on your EC2 instance to set up Vault

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 Setting up HashiCorp Vault for Shrutik${NC}"
echo "=============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Don't run this script as root${NC}"
   exit 1
fi

# Install Vault
echo -e "${BLUE}📦 Installing Vault...${NC}"
if ! command -v vault &> /dev/null; then
    wget -q https://releases.hashicorp.com/vault/1.15.2/vault_1.15.2_linux_amd64.zip
    unzip -q vault_1.15.2_linux_amd64.zip
    sudo mv vault /usr/local/bin/
    sudo chmod +x /usr/local/bin/vault
    rm vault_1.15.2_linux_amd64.zip
    echo -e "${GREEN}✅ Vault installed${NC}"
else
    echo -e "${GREEN}✅ Vault already installed${NC}"
fi

# Create vault user and directories
echo -e "${BLUE}📁 Creating vault directories...${NC}"
sudo mkdir -p /opt/vault/{data,config,logs}
if ! id "vault" &>/dev/null; then
    sudo useradd -r -d /opt/vault -s /bin/false vault
fi
sudo chown -R vault:vault /opt/vault

# Create vault configuration
echo -e "${BLUE}⚙️  Creating vault configuration...${NC}"
sudo tee /opt/vault/config/vault.hcl > /dev/null << 'EOF'
# Vault Configuration for Shrutik

storage "file" {
  path = "/opt/vault/data"
}

listener "tcp" {
  address     = "127.0.0.1:8200"
  tls_disable = 1
}

api_addr = "http://127.0.0.1:8200"
cluster_addr = "https://127.0.0.1:8201"
ui = true
log_level = "INFO"
log_file = "/opt/vault/logs/vault.log"
disable_mlock = true
EOF

sudo chown vault:vault /opt/vault/config/vault.hcl

# Create systemd service
echo -e "${BLUE}🔧 Creating systemd service...${NC}"
sudo tee /etc/systemd/system/vault.service > /dev/null << 'EOF'
[Unit]
Description=HashiCorp Vault
Documentation=https://www.vaultproject.io/docs/
Requires=network-online.target
After=network-online.target
ConditionFileNotEmpty=/opt/vault/config/vault.hcl

[Service]
Type=notify
User=vault
Group=vault
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=yes
PrivateDevices=yes
SecureBits=keep-caps
AmbientCapabilities=CAP_IPC_LOCK
CapabilityBoundingSet=CAP_SYSLOG CAP_IPC_LOCK
NoNewPrivileges=yes
ExecStart=/usr/local/bin/vault server -config=/opt/vault/config/vault.hcl
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
StartLimitInterval=60
StartLimitBurst=3
LimitNOFILE=65536
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF

# Start vault service
echo -e "${BLUE}🚀 Starting Vault service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable vault
sudo systemctl start vault

# Wait for vault to start
sleep 3

# Check if vault is running
if sudo systemctl is-active --quiet vault; then
    echo -e "${GREEN}✅ Vault service started successfully${NC}"
else
    echo -e "${RED}❌ Vault service failed to start${NC}"
    sudo systemctl status vault
    exit 1
fi

# Set vault address
export VAULT_ADDR='http://127.0.0.1:8200'

# Check if vault is already initialized
if vault status 2>/dev/null | grep -q "Initialized.*true"; then
    echo -e "${YELLOW}⚠️  Vault is already initialized${NC}"
    echo "Use 'vault operator unseal' to unseal if needed"
else
    echo -e "${BLUE}🔑 Initializing Vault...${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Save the following output securely!${NC}"
    echo "=================================================="
    vault operator init
    echo "=================================================="
    echo -e "${RED}❗ SAVE THE UNSEAL KEYS AND ROOT TOKEN ABOVE!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Unseal vault: vault operator unseal (use 3 different keys)"
    echo "2. Run: ./scripts/vault-configure.sh"
fi

echo -e "${GREEN}🎉 Vault setup completed!${NC}"