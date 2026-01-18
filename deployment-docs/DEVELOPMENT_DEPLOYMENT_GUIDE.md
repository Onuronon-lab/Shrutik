# Development Deployment Guide - Shrutik

**Quick setup for testing with your co-founder (no domain needed)**

## Prerequisites

- ✅ EC2 instance running
- ✅ Vault configured (you've done this)
- ✅ SSH access to EC2

## Step 1: Get Your EC2 Public IP

```bash
# On your EC2 instance, run:
curl -s http://checkip.amazonaws.com/

# Example output: 3.15.123.45
# Save this IP - you'll share it with your co-founder
```

## Step 2: Install Docker (if not already installed)

```bash
# Check if Docker is installed
docker --version
docker-compose --version

# If not installed:
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Log out and log back in for docker group to take effect
exit
# SSH back in
```

## Step 3: Configure Security Groups

Make sure your EC2 security group allows HTTP traffic:

**In AWS Console:**
1. Go to EC2 → Security Groups
2. Find your instance's security group
3. Add inbound rule:
   - Type: HTTP
   - Port: 80
   - Source: 0.0.0.0/0 (Anywhere)

**Or via CLI:**
```bash
# First, find your security group ID:
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
SECURITY_GROUP_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)

# Then add the HTTP rule:
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

## Step 4: Deploy Development Version

```bash
# Navigate to project directory
cd /opt/shrutik

# First, add your R2 credentials to Vault (if not already done)
./scripts/vault-add-r2.sh

# Set up nginx for development (HTTP only)
./scripts/nginx-config.sh setup-dev

# Deploy the application with Vault secrets + Docker Hub image
./scripts/deploy-with-vault-hub.sh ifrunruhiin12 latest
```

**Expected output:**
```
🔐 Adding R2 Credentials to Vault
==================================
Please enter your Cloudflare R2 credentials:
...
✅ R2 credentials stored in Vault

🚀 Deploying Shrutik with Vault Integration + Docker Hub
============================================
Docker Image: ifrunruhiin12/shrutik:latest
📥 Pulling latest Docker image from Docker Hub...
✅ Secrets loaded from Vault into environment
✅ Docker containers started
✅ Application deployed successfully
```

## Step 5: Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.hub.yml ps

# Should show all services as "Up":
# - nginx
# - backend
# - frontend
# - postgres
# - redis
# - celery-worker
# - celery-flower

# Check application health
curl http://localhost/health
# Should return: {"status": "healthy"}
```

## Step 6: Access Your Application

**Share these URLs with your co-founder:**

- **Main Application:** `http://YOUR-EC2-IP/`
- **API Documentation:** `http://YOUR-EC2-IP/api/docs`
- **Admin Panel (Celery Monitor):** `http://YOUR-EC2-IP/admin/flower/`

**Example (replace with your actual IP):**
- Main App: `http://3.15.123.45/`
- API Docs: `http://3.15.123.45/api/docs`
- Admin: `http://3.15.123.45/admin/flower/`

## Step 7: Test the Application

```bash
# Test frontend
curl -I http://localhost/
# Should return: HTTP/1.1 200 OK

# Test API
curl http://localhost/api/health
# Should return: {"status": "healthy"}

# Test file upload endpoint
curl -I http://localhost/api/upload
# Should return: HTTP/1.1 405 Method Not Allowed (normal for GET request)
```

## Managing the Application

### View Logs
```bash
# View all logs
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml logs

# View specific service logs
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml logs backend
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml logs frontend
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml logs nginx

# Follow logs in real-time
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml logs -f
```

### Restart Services
```bash
# Restart all services
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml restart

# Restart specific service
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml restart backend
```

### Update Application
```bash
# Pull latest Docker image and redeploy
./scripts/deploy-with-vault-hub.sh ifrunruhiin12 latest
```

## Taking the Application DOWN

### Option 1: Stop All Services (Recommended)
```bash
cd /opt/shrutik

# Stop all containers but keep data
docker-compose -f docker-compose.prod.yml stop

# To start again later
docker-compose -f docker-compose.prod.yml start
```

### Option 2: Complete Shutdown
```bash
cd /opt/shrutik

# Stop and remove containers (keeps data volumes)
docker-compose -f docker-compose.prod.yml down

# To deploy again later
./scripts/deploy-with-vault.sh
```

### Option 3: Nuclear Option (Removes Everything)
```bash
cd /opt/shrutik

# Stop and remove everything including data
docker-compose -f docker-compose.prod.yml down -v
docker system prune -a -f

# This will delete all data! Only use if you want to start fresh
```

## Troubleshooting

### Application won't start
```bash
# Check Docker is running
sudo systemctl status docker

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs

# Restart Docker if needed
sudo systemctl restart docker
```

### Can't access from browser
```bash
# Check security group allows port 80
# Check nginx is running
docker-compose -f docker-compose.prod.yml ps nginx

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

### Database issues
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Reset database (WARNING: deletes all data)
docker-compose -f docker-compose.prod.yml down -v
./scripts/deploy-with-vault.sh
```

## Sharing with Co-founder

**Send them:**
1. **Main URL:** `http://YOUR-EC2-IP/`
2. **What it is:** "Live test version of Shrutik voice collection platform"
3. **Features to test:** 
   - User registration/login
   - Voice recording
   - File upload
   - Admin dashboard (if they need access)

**Example message:**
```
Hey! Shrutik is now live for testing:

🌐 Main App: http://3.15.123.45/
📚 API Docs: http://3.15.123.45/api/docs
⚙️ Admin: http://3.15.123.45/admin/flower/

This is our development version running on AWS. 
Feel free to test all the features - recording, uploading, etc.

Let me know if you find any issues!
```

## Quick Commands Reference

```bash
# Deploy with Docker Hub image
./scripts/vault-add-r2.sh  # First time only
./scripts/nginx-config.sh setup-dev
./scripts/deploy-with-vault-hub.sh ifrunruhiin12 latest

# Check status
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml ps

# View logs
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml logs -f

# Stop (keeps data)
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml stop

# Start again
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml start

# Complete shutdown
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml down
```

---

**That's it!** Your application should now be live and accessible via your EC2 public IP address. Perfect for testing with your co-founder before going to production.