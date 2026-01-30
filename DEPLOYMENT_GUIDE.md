# Shrutik Development Deployment Guide

**Complete setup guide for development deployment on EC2 with Vault and Docker Hub images**

This guide will help you deploy Shrutik on EC2 for development/testing purposes. You'll have a production-like environment accessible via your EC2 public IP, perfect for testing before going to production with your own domain.

## Prerequisites

- ✅ EC2 instance running (Ubuntu recommended)
- ✅ SSH access configured (`ssh shrutik-ec2` should work)
- ✅ Docker Hub account (free)
- ✅ About 30-45 minutes

## Overview

This deployment uses:
- **HashiCorp Vault** for secure secrets management
- **Docker Hub** for pre-built images (no building on EC2)
- **Nginx** for reverse proxy and static file serving
- **PostgreSQL** for database
- **Redis** for caching and Celery
- **Celery** for background tasks

## Part 1: Local Setup (Run on Your Local Machine)

### Step 1: Prepare Your Docker Hub Image

First, build and push your image to Docker Hub:

```bash
# Login to Docker Hub
docker login

# Build and push your image (replace 'yourusername' with your Docker Hub username)
docker build -f Dockerfile.prod -t yourusername/shrutik:latest .
docker push yourusername/shrutik:latest

# Or use the provided script
./scripts/build-and-push.sh yourusername latest
```

### Step 2: Sync Files to EC2

Use the local setup script to sync necessary files to your EC2:

```bash
# This will sync all necessary files to EC2 and prepare the environment
./scripts/local-setup.sh yourusername/shrutik:latest
```

**What this script does:**
- Syncs configuration files, scripts, and docker-compose to EC2
- Excludes source code (since we're using Docker Hub images)
- Sets up the directory structure on EC2
- Prepares environment for deployment

## Part 2: EC2 Setup (Run on EC2)

### Step 3: SSH to Your EC2 and Run Deployment

```bash
# SSH to your EC2 instance
ssh shrutik-ec2

# Navigate to the project directory
cd /opt/shrutik

# Run the complete deployment script
./scripts/ec2-deploy.sh yourusername/shrutik:latest
```

**What this script does:**
1. **Installs Docker and Docker Compose** (if not already installed)
2. **Sets up HashiCorp Vault** with secure configuration
3. **Initializes and configures Vault** with all necessary secrets
4. **Configures Nginx** for development (HTTP access)
5. **Pulls your Docker image** from Docker Hub
6. **Starts all services** (database, backend, frontend, nginx, etc.)
7. **Validates deployment** and shows you access URLs

### Step 4: Access Your Application

After successful deployment, your application will be available at:

- **Main Application:** `http://YOUR-EC2-PUBLIC-IP:3080/`
- **API Documentation:** `http://YOUR-EC2-PUBLIC-IP:3080/api/docs`
- **Admin Panel (Celery Monitor):** `http://YOUR-EC2-PUBLIC-IP:3080/admin/flower/`
- **Health Check:** `http://YOUR-EC2-PUBLIC-IP:3080/health`

To get your EC2 public IP:
```bash
curl -s http://checkip.amazonaws.com/
```

## Security Groups Configuration

Make sure your EC2 security group allows HTTP traffic:

**Required inbound rules:**
- **HTTP (3080):** `0.0.0.0/0` - For web access
- **SSH (22):** Your IP only - For SSH access

**Via AWS Console:**
1. Go to EC2 → Security Groups
2. Find your instance's security group  
3. Add inbound rule: Type: Custom TCP, Port: 3080, Source: 0.0.0.0/0

## Managing Your Deployment

### View Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f postgres
```

### Restart Services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update Your Application
```bash
# On your local machine: build and push new image
docker build -f Dockerfile.prod -t yourusername/shrutik:latest .
docker push yourusername/shrutik:latest

# On EC2: pull and restart
docker-compose pull
docker-compose up -d
```

### Stop/Start Services
```bash
# Stop all services (keeps data)
docker-compose stop

# Start all services
docker-compose start

# Complete shutdown (removes containers but keeps data)
docker-compose down

# Nuclear option (removes everything including data)
docker-compose down -v
```

## Vault Management

### Viewing Secrets
```bash
# Set vault environment
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN=$(cat /opt/shrutik/vault-token)

# View all secrets
vault kv list secret/shrutik/

# View specific secret groups
vault kv get secret/shrutik/database
vault kv get secret/shrutik/app
vault kv get secret/shrutik/monitoring
```

### Updating Secrets
```bash
# Update database password
vault kv patch secret/shrutik/database postgres_password="new-password"

# Update domain (for future SSL setup)
vault kv patch secret/shrutik/domain domain_name="your-domain.com"

# After updating secrets, recreate environment and restart
./scripts/vault-secrets.sh create-env
docker-compose restart
```

### Vault Unsealing (After EC2 Restart)

If you restart your EC2 instance, Vault will be "sealed" and you'll need to unseal it:

```bash
# Check vault status
export VAULT_ADDR='http://127.0.0.1:8200'
vault status

# If sealed, unseal with 3 of your 5 keys
vault operator unseal [key1]
vault operator unseal [key2]
vault operator unseal [key3]

# Then restart your application
docker-compose restart
```

**⚠️ Important:** Keep your Vault unseal keys secure! You received them during initial setup.

## Troubleshooting

### Application Won't Start
```bash
# Check Docker is running
sudo systemctl status docker

# Check all services
docker-compose ps

# Check logs for errors
docker-compose logs
```

### Can't Access from Browser
```bash
# Check nginx is running
docker-compose ps nginx

# Check nginx logs
docker-compose logs nginx

# Verify security group allows port 80
# Check your EC2 public IP
curl -s http://checkip.amazonaws.com/
```

### Database Issues
```bash
# Check database logs
docker-compose logs postgres

# Check database connection
docker-compose exec backend python -c "
from app.db.database import engine
print('Database connection:', engine.url)
"
```

### Vault Issues
```bash
# Check vault service
sudo systemctl status vault

# Check vault logs
sudo journalctl -u vault -f

# Restart vault if needed
sudo systemctl restart vault
```

## Backup and Recovery

### Create Backup
```bash
# Backup database
docker-compose exec postgres pg_dump -U production_user voice_collection > backup.sql

# Backup vault data
sudo tar -czf vault-backup.tar.gz /opt/vault/data/

# Backup uploaded files
tar -czf uploads-backup.tar.gz uploads/
```

### Restore from Backup
```bash
# Restore database
docker-compose exec -T postgres psql -U production_user voice_collection < backup.sql

# Restore vault data (stop vault first)
sudo systemctl stop vault
sudo tar -xzf vault-backup.tar.gz -C /
sudo systemctl start vault
# Then unseal vault with your keys

# Restore uploads
tar -xzf uploads-backup.tar.gz
```

## Going to Production

When you're ready to go to production with your own domain:

1. **Purchase a domain** and configure DNS to point to your EC2
2. **Update Vault** with your domain:
   ```bash
   vault kv patch secret/shrutik/domain domain_name="yourdomain.com"
   ```
3. **Set up SSL certificates** using Let's Encrypt
4. **Configure production nginx** with HTTPS
5. **Update security groups** to allow HTTPS (port 443)

## Quick Commands Reference

```bash
# Local machine: Build and push image
./scripts/build-and-push.sh yourusername latest

# Local machine: Sync to EC2
./scripts/local-setup.sh yourusername/shrutik:latest

# EC2: Complete deployment
./scripts/ec2-deploy.sh yourusername/shrutik:latest

# EC2: Check status
docker-compose ps

# EC2: View logs
docker-compose logs -f

# EC2: Update application
docker-compose pull && docker-compose up -d

# EC2: Restart services
docker-compose restart

# EC2: Stop/start
docker-compose stop
docker-compose start
```

## Support

If you encounter issues:

1. **Check the logs** first: `docker-compose logs -f`
2. **Verify all services are running**: `docker-compose ps`
3. **Check Vault status**: `vault status`
4. **Verify security groups** allow HTTP traffic
5. **Check EC2 public IP**: `curl -s http://checkip.amazonaws.com/`

---

**That's it!** 🎉 

Your Shrutik application should now be running on your EC2 instance, accessible via HTTP, with enterprise-grade security through Vault, and ready for testing with your co-founder.

The setup provides:
- ✅ Secure secrets management with Vault
- ✅ Production-like environment
- ✅ Easy updates via Docker Hub
- ✅ Comprehensive logging and monitoring
- ✅ Simple backup and recovery
- ✅ Path to production deployment