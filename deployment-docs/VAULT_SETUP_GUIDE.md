# HashiCorp Vault Setup Guide for Shrutik

This guide will walk you through setting up HashiCorp Vault for secure secrets management in your Shrutik voice collection platform. Vault will store all your sensitive information (database passwords, API keys, etc.) securely encrypted and separate from your application code.

## Table of Contents

1. [Why Use Vault?](#why-use-vault)
2. [Prerequisites](#prerequisites)
3. [Step 1: Install Vault on EC2](#step-1-install-vault-on-ec2)
4. [Step 2: Configure Vault](#step-2-configure-vault)
5. [Step 3: Initialize Vault](#step-3-initialize-vault)
6. [Step 4: Unseal Vault](#step-4-unseal-vault)
7. [Step 5: Configure Shrutik Secrets](#step-5-configure-shrutik-secrets)
8. [Step 6: Deploy Application](#step-6-deploy-application)
9. [Daily Operations](#daily-operations)
10. [Troubleshooting](#troubleshooting)
11. [Security Best Practices](#security-best-practices)

## Why Use Vault?

**Problem with traditional secrets management:**
- Secrets stored in plain text files (`.env`)
- Anyone with server access can read them
- No audit trail of who accessed what
- Difficult to rotate secrets
- Secrets often committed to git accidentally

**How Vault solves this:**
- All secrets encrypted at rest
- Access controlled by policies
- Complete audit trail
- Easy secret rotation
- Secrets never stored in files
- Enterprise-grade security for free

## Prerequisites

Before starting, ensure you have:

- SSH access to your EC2 instance
- Basic familiarity with command line
- Your Shrutik project files ready to deploy
- About 30 minutes of time

**What you'll need to save securely:**
- 5 unseal keys (you'll get these during setup)
- 1 root token (you'll get this during setup)
- Application token (generated automatically)

## Step 1: Install Vault on EC2

### 1.1 Connect to Your EC2 Instance

```bash
# From your local machine
ssh shrutik-ec2
```

### 1.2 Prepare Your Project

```bash
# Create application directory
sudo mkdir -p /opt/shrutik
sudo chown ubuntu:ubuntu /opt/shrutik

# Copy your project files from local machine to EC2
# Run this from your LOCAL machine (not EC2):
rsync -av --exclude='.git' --exclude='node_modules' --exclude='venv' . ubuntu@YOUR_EC2_IP:/opt/shrutik/

# Back on EC2, go to project directory
cd /opt/shrutik
```

### 1.3 Run the Vault Setup Script

```bash
# Make sure the script is executable
chmod +x scripts/vault-setup.sh

# Run the setup script
./scripts/vault-setup.sh
```

**What this script does:**
- Downloads and installs HashiCorp Vault
- Creates a dedicated `vault` user for security
- Sets up proper directory structure
- Creates systemd service for automatic startup
- Starts the Vault service
- Initializes Vault (if not already done)

**Expected output:**
```
🔐 Setting up HashiCorp Vault for Shrutik
==============================================
📦 Installing Vault...
✅ Vault installed
📁 Creating vault directories...
⚙️  Creating vault configuration...
🔧 Creating systemd service...
🚀 Starting Vault service...
✅ Vault service started successfully
🔑 Initializing Vault...
⚠️  IMPORTANT: Save the following output securely!
==================================================
Unseal Key 1: ABC123DEF456GHI789JKL012MNO345PQR678STU901VWX234YZ
Unseal Key 2: BCD234EFG567HIJ890KLM123NOP456QRS789TUV012WXY345ZAB
Unseal Key 3: CDE345FGH678IJK901LMN234OPQ567RST890UVW123XYZ456ABC
Unseal Key 4: DEF456GHI789JKL012MNO345PQR678STU901VWX234YZA567BCD
Unseal Key 5: EFG567HIJ890KLM123NOP456QRS789TUV012WXY345ZAB678CDE

Initial Root Token: s.ABCDEFGHIJKLMNOPQRSTUVWX
==================================================
❗ SAVE THE UNSEAL KEYS AND ROOT TOKEN ABOVE!
```

### 1.4 CRITICAL: Save Your Keys

**🚨 EXTREMELY IMPORTANT 🚨**

Copy and paste the unseal keys and root token into a secure location:

1. **Text file on your local machine** (not on EC2)
2. **Password manager** (recommended)
3. **Encrypted note-taking app**
4. **Physical paper** (as backup)

**DO NOT:**
- Leave them in your terminal history
- Save them in a file on EC2
- Share them with anyone
- Commit them to git

**Why you need these:**
- **Unseal keys**: Required to unlock Vault after restart (need 3 of 5)
- **Root token**: Administrative access to configure Vault

## Step 2: Configure Vault

### 2.1 Set Vault Environment

```bash
# Set the Vault address (run this in every new terminal session)
export VAULT_ADDR='http://127.0.0.1:8200'

# Check Vault status
vault status
```

**Expected output:**
```
Key                Value
---                -----
Seal Type          shamir
Initialized        true
Sealed             true    ← This means Vault is locked
Total Shares       5
Threshold          3
Unseal Progress    0/3
```

### 2.2 Unseal Vault

Vault starts "sealed" (locked) for security. You need to unseal it using 3 of your 5 keys:

```bash
# Unseal with first key
vault operator unseal
# Paste your first unseal key when prompted

# Unseal with second key  
vault operator unseal
# Paste your second unseal key when prompted

# Unseal with third key
vault operator unseal
# Paste your third unseal key when prompted
```

**After third key, you should see:**
```
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false   ← Now unlocked!
Total Shares    5
Threshold       3
```

### 2.3 Configure Shrutik Secrets

```bash
# Run the configuration script
./scripts/vault-configure.sh
```

**What this script does:**
- Authenticates with your root token
- Creates a policy for Shrutik application
- Generates secure random passwords
- Stores all secrets in Vault
- Creates an application token for Shrutik to use

**You'll be prompted for:**
```
Enter your Vault root token: [paste your root token here]
```

**Expected output:**
```
⚙️  Configuring Vault for Shrutik
==================================
✅ Authenticated with Vault
🔧 Enabling KV secrets engine...
✅ KV secrets engine enabled
📋 Creating Shrutik policy...
✅ Shrutik policy created
🔐 Generating and storing secrets...
✅ Secrets stored in Vault
🎫 Creating application token...
✅ Application token created and saved
🧪 Testing secret retrieval...
✅ Secret retrieval test passed

🎉 Vault configuration completed!
==================================
Summary:
• Vault is running on http://127.0.0.1:8200
• Secrets stored under secret/shrutik/
• Application token saved to /opt/shrutik/vault-token

Generated credentials:
• Database password: [random 32-character password]
• Flower admin: admin:[random 16-character password]

⚠️  Save these credentials securely!

Next steps:
1. Update domain: vault kv patch secret/shrutik/domain domain_name=your-actual-domain.com
2. Run deployment: ./scripts/deploy-with-vault.sh
```

## Step 3: Initialize Vault

This step is automatically handled by the setup script, but here's what happens behind the scenes:

### 3.1 Understanding Vault Initialization

When Vault is first started, it's in an uninitialized state. Initialization:

1. **Generates master key** - Used to encrypt all data
2. **Splits master key** - Into 5 pieces using Shamir's Secret Sharing
3. **Creates root token** - For initial administrative access
4. **Sets up encryption** - All future data will be encrypted

### 3.2 Shamir's Secret Sharing Explained

- Master key is split into 5 pieces
- Any 3 pieces can reconstruct the master key
- This means:
  - You can lose 2 keys and still access Vault
  - No single person has complete access
  - Requires cooperation to unlock Vault

## Step 4: Unseal Vault

### 4.1 Understanding Sealing

**Vault starts sealed after:**
- Initial installation
- Server restart
- Manual sealing
- Certain error conditions

**When sealed:**
- No data can be read or written
- Only unseal operations are allowed
- All secrets are protected

### 4.2 Unsealing Process

```bash
# Check if Vault is sealed
vault status

# If sealed, unseal with 3 keys
vault operator unseal [key1]
vault operator unseal [key2]  
vault operator unseal [key3]

# Verify it's unsealed
vault status
```

### 4.3 Automatic Unsealing (Optional)

For convenience, you can set up auto-unseal, but this reduces security:

```bash
# Create unseal script (LESS SECURE)
cat > /opt/vault/unseal.sh << 'EOF'
#!/bin/bash
export VAULT_ADDR='http://127.0.0.1:8200'
vault operator unseal "your-key-1"
vault operator unseal "your-key-2"
vault operator unseal "your-key-3"
EOF

chmod 700 /opt/vault/unseal.sh
```

**⚠️ Security Warning:** This stores unseal keys on disk, reducing security.

## Step 5: Configure Shrutik Secrets

### 5.1 Understanding the Secret Structure

Vault organizes secrets in a hierarchical structure:

```
secret/shrutik/
├── database/
│   ├── postgres_password
│   ├── postgres_user
│   └── postgres_db
├── app/
│   ├── secret_key
│   └── debug
├── monitoring/
│   ├── flower_username
│   └── flower_password
└── domain/
    ├── domain_name
    └── ssl_email
```

### 5.2 Viewing Secrets

```bash
# Set up environment
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN=$(cat /opt/shrutik/vault-token)

# List all Shrutik secrets
./scripts/vault-secrets.sh list

# View specific secret group
vault kv get secret/shrutik/database
vault kv get secret/shrutik/app
vault kv get secret/shrutik/monitoring
vault kv get secret/shrutik/domain
```

### 5.3 Updating Secrets

```bash
# Update domain configuration
./scripts/vault-secrets.sh update-domain your-actual-domain.com admin@your-domain.com

# Update individual secrets
vault kv patch secret/shrutik/database postgres_password="new-password"
vault kv patch secret/shrutik/app secret_key="new-secret-key"

# Add new secrets
vault kv patch secret/shrutik/app new_setting="new-value"
```

### 5.4 Understanding Policies

The configuration script creates a policy that allows Shrutik to:

```hcl
# Read, write, update, delete secrets under secret/shrutik/
path "secret/data/shrutik/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage metadata for secret/shrutik/
path "secret/metadata/shrutik/*" {
  capabilities = ["list", "delete"]
}
```

This means:
- ✅ Shrutik can access its own secrets
- ❌ Shrutik cannot access other applications' secrets
- ❌ Shrutik cannot change Vault configuration
- ❌ Shrutik cannot create new policies

## Step 6: Deploy Application

### 6.1 Deploy with Vault Integration

```bash
# Deploy Shrutik using Vault secrets
./scripts/deploy-with-vault.sh
```

**What this script does:**

1. **Validates Vault connectivity**
   ```bash
   # Tests that Vault is accessible and unsealed
   ./scripts/vault-secrets.sh test
   ```

2. **Creates environment file from Vault**
   ```bash
   # Retrieves all secrets and creates .env.prod
   ./scripts/vault-secrets.sh create-env
   ```

3. **Builds and starts services**
   ```bash
   # Stops old containers, builds new ones, starts services
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Validates deployment**
   ```bash
   # Checks that all services are healthy
   docker-compose -f docker-compose.prod.yml ps
   ```

### 6.2 Expected Deployment Output

```
🚀 Deploying Shrutik with Vault Integration
==============================================
📁 Setting up application directory...
📋 Copying application files...
🧪 Testing Vault connectivity...
✅ Vault connectivity test passed
🔐 Creating environment file from Vault...
✅ .env.prod created with secure permissions
🛑 Stopping existing containers...
🧹 Cleaning up development files...
🏗️  Building production images...
📁 Creating data directories...
🔐 Setting file permissions...
🚀 Starting production services...
⏳ Waiting for services to be healthy...
🏥 Checking service health...
✅ postgres is healthy
✅ redis is healthy
✅ backend is healthy

🎉 Deployment completed successfully!
==============================================
Services Status:
NAME                     COMMAND                  SERVICE             STATUS              PORTS
shrutik_backend_prod     "uvicorn app.main:ap…"   backend             running (healthy)   
shrutik_celery_beat_prod "celery -A app.core.c…"   celery-beat         running             
shrutik_celery_prod      "celery -A app.core.c…"   celery              running             
shrutik_flower_prod      "celery -A app.core.c…"   celery-flower       running             
shrutik_frontend_prod    "nginx -g 'daemon of…"   frontend            running             
shrutik_nginx_prod       "nginx -g 'daemon of…"   nginx               running             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
shrutik_postgres_prod    "docker-entrypoint.s…"   postgres            running (healthy)   
shrutik_redis_prod       "docker-entrypoint.s…"   redis               running (healthy)   

🔑 Important Information:
• Vault UI: http://localhost:8200
• Flower Monitor: http://localhost:5555 (admin:AbC123XyZ)
• Application: http://localhost (after nginx setup)
```

### 6.3 Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Test application health
curl http://localhost:8000/health
```

## Daily Operations

### 7.1 Starting/Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### 7.2 Managing Vault

```bash
# Check Vault status
vault status

# If Vault is sealed after restart, unseal it
vault operator unseal [key1]
vault operator unseal [key2]
vault operator unseal [key3]

# View Vault logs
sudo journalctl -u vault -f
```

### 7.3 Updating Secrets

```bash
# Update domain
./scripts/vault-secrets.sh update-domain new-domain.com

# Update database password
vault kv patch secret/shrutik/database postgres_password="new-password"

# Recreate .env file with new secrets
./scripts/vault-secrets.sh create-env

# Restart services to use new secrets
docker-compose -f docker-compose.prod.yml restart
```

### 7.4 Viewing Application Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### 7.5 Health Monitoring

```bash
# Run health check script
./scripts/health-check.sh

# Check individual service health
curl http://localhost:8000/health
curl http://localhost:3000/health
```

## Troubleshooting

### 8.1 Vault Issues

**Problem: Vault is sealed**
```bash
# Symptoms
vault status
# Shows: Sealed: true

# Solution
vault operator unseal [key1]
vault operator unseal [key2]
vault operator unseal [key3]
```

**Problem: Vault service not running**
```bash
# Check service status
sudo systemctl status vault

# Start service
sudo systemctl start vault

# Check logs
sudo journalctl -u vault -f
```

**Problem: Cannot connect to Vault**
```bash
# Check if Vault is listening
netstat -tlnp | grep 8200

# Check firewall
sudo ufw status

# Verify configuration
sudo cat /opt/vault/config/vault.hcl
```

### 8.2 Application Issues

**Problem: Services not starting**
```bash
# Check Docker status
docker ps -a

# Check specific service logs
docker-compose -f docker-compose.prod.yml logs backend

# Check .env file exists and has correct permissions
ls -la .env.prod
```

**Problem: Database connection errors**
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database credentials in Vault
vault kv get secret/shrutik/database

# Recreate .env file
./scripts/vault-secrets.sh create-env
```

**Problem: Permission denied errors**
```bash
# Fix file permissions
chmod 600 .env.prod
chmod -R 755 data/ logs/
sudo chown -R $(whoami):$(whoami) /opt/shrutik
```

### 8.3 Network Issues

**Problem: Cannot access application**
```bash
# Check nginx is running
docker-compose -f docker-compose.prod.yml ps nginx

# Check port bindings
docker-compose -f docker-compose.prod.yml port nginx 80

# Check firewall rules
sudo ufw status
```

### 8.4 Common Error Messages

**"Error: vault is sealed"**
- Solution: Unseal Vault with 3 keys

**"Error: permission denied"**
- Solution: Check file permissions and ownership

**"Error: connection refused"**
- Solution: Check if services are running

**"Error: invalid token"**
- Solution: Check Vault token file exists and is valid

## Security Best Practices

### 9.1 Vault Security

**Unseal Keys:**
- Store in multiple secure locations
- Never store all keys in one place
- Consider using a password manager
- Share keys among trusted team members
- Regularly audit who has access

**Root Token:**
- Use only for initial setup
- Create limited-privilege tokens for daily use
- Revoke root token after setup (advanced)
- Never store in application code

**Access Control:**
- Use policies to limit access
- Create separate tokens for different applications
- Regularly rotate tokens
- Monitor access logs

### 9.2 System Security

**File Permissions:**
```bash
# Vault data should be owned by vault user
sudo chown -R vault:vault /opt/vault/

# Application files should have restricted permissions
chmod 600 .env.prod
chmod 700 /opt/shrutik/vault-token
```

**Network Security:**
- Vault only listens on localhost (127.0.0.1)
- Use firewall to restrict access
- Consider VPN for remote access
- Enable TLS in production (advanced)

**Backup Security:**
```bash
# Backup Vault data regularly
sudo tar -czf vault-backup-$(date +%Y%m%d).tar.gz /opt/vault/data/

# Store backups securely (encrypted)
gpg --symmetric --cipher-algo AES256 vault-backup-$(date +%Y%m%d).tar.gz
```

### 9.3 Monitoring and Auditing

**Enable Audit Logging:**
```bash
# Enable file audit device
vault audit enable file file_path=/opt/vault/logs/audit.log

# Monitor audit logs
tail -f /opt/vault/logs/audit.log
```

**Regular Security Checks:**
```bash
# Check Vault status
vault status

# List active tokens
vault auth -method=token -token=$ROOT_TOKEN
vault token lookup

# Review policies
vault policy list
vault policy read shrutik-policy
```

### 9.4 Disaster Recovery

**Backup Strategy:**
1. **Vault data**: `/opt/vault/data/` (contains all secrets)
2. **Vault configuration**: `/opt/vault/config/vault.hcl`
3. **Unseal keys**: Stored securely offline
4. **Application code**: Git repository

**Recovery Process:**
1. Restore Vault data from backup
2. Start Vault service
3. Unseal with 3 keys
4. Verify secrets are accessible
5. Redeploy application

**Testing Recovery:**
```bash
# Test backup restoration (on test system)
sudo systemctl stop vault
sudo rm -rf /opt/vault/data/*
sudo tar -xzf vault-backup-YYYYMMDD.tar.gz -C /
sudo systemctl start vault
vault operator unseal [key1]
vault operator unseal [key2]
vault operator unseal [key3]
vault kv get secret/shrutik/database
```

## Conclusion

You now have a production-ready HashiCorp Vault setup that provides:

✅ **Enterprise-grade security** for all your secrets  
✅ **Encrypted storage** with access control  
✅ **Audit trail** of all secret access  
✅ **Easy secret rotation** without code changes  
✅ **High availability** with backup and recovery  
✅ **Zero-cost** solution using open source tools  

Your secrets are now stored securely in Vault instead of plain text files, giving you the same level of security that major companies use for their production systems.

## Next Steps

1. **Set up SSL certificates** for HTTPS access
2. **Configure domain name** and DNS
3. **Set up monitoring** and alerting
4. **Create backup automation**
5. **Document your specific procedures**

Remember to keep your unseal keys and root token secure - they are the keys to your entire system!