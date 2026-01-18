# Nginx Setup Guide for Shrutik

This guide walks you through setting up nginx for your Shrutik application on EC2.

## Prerequisites

- ✅ EC2 instance running
- ✅ Vault configured (you've done this)
- ✅ Domain name (optional for development)

## Step 1: Install Docker and Docker Compose

First, make sure Docker is installed on your EC2 instance:

```bash
# Check if Docker is installed
docker --version
docker-compose --version

# If not installed, install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

**Important:** After adding yourself to the docker group, log out and log back in for the changes to take effect.

## Step 2: Choose Your Setup Type

You have two options:

### Option A: Development Setup (HTTP only)
- No SSL certificates needed
- Access via `http://your-ec2-ip`
- Good for testing

### Option B: Production Setup (HTTPS with SSL)
- Requires a domain name
- Automatic SSL certificates via Let's Encrypt
- Access via `https://yourdomain.com`
- Recommended for production

## Step 3A: Development Setup (HTTP Only)

If you just want to test without a domain:

```bash
# Navigate to your project directory
cd /opt/shrutik

# Set up nginx for development
./scripts/nginx-config.sh setup-dev

# Deploy the application
./scripts/deploy-with-vault.sh
```

Your application will be available at:
- **Frontend:** `http://your-ec2-ip/`
- **API:** `http://your-ec2-ip/api/`
- **Admin:** `http://your-ec2-ip/admin/flower/`

## Step 3B: Production Setup (HTTPS with Domain)

If you have a domain name:

```bash
# Navigate to your project directory
cd /opt/shrutik

# Set up nginx for production (replace with your domain)
./scripts/nginx-config.sh setup-prod -d yourdomain.com

# Deploy the application
./scripts/deploy-with-vault.sh

# Set up SSL certificates (after DNS is configured)
./scripts/ssl-setup.sh -d yourdomain.com
```

**Important:** Before running SSL setup, make sure your domain's DNS A record points to your EC2 instance's public IP.

## Step 4: Configure Security Groups

Make sure your EC2 security group allows the necessary ports:

```bash
# Check current security group rules
aws ec2 describe-security-groups --group-ids sg-your-security-group-id

# Or via AWS Console:
# 1. Go to EC2 → Security Groups
# 2. Find your instance's security group
# 3. Add these inbound rules:
```

**Required ports:**
- **Port 80 (HTTP):** `0.0.0.0/0` - For Let's Encrypt and HTTP redirect
- **Port 443 (HTTPS):** `0.0.0.0/0` - For HTTPS traffic
- **Port 22 (SSH):** Your IP only - For SSH access

## Step 5: Update Domain Configuration in Vault

If using a domain, update the domain configuration in Vault:

```bash
# Set your actual domain
export VAULT_ADDR='http://127.0.0.1:8200'
vault kv patch secret/shrutik/domain \
  domain_name="yourdomain.com" \
  ssl_email="admin@yourdomain.com"
```

## Step 6: Verify Setup

Check that everything is working:

```bash
# Check nginx status
./scripts/nginx-config.sh status

# Check all services
docker-compose -f docker-compose.prod.yml ps

# Check nginx logs if there are issues
./scripts/nginx-config.sh logs

# Test configuration
./scripts/nginx-config.sh validate
```

## Step 7: Access Your Application

### Development Setup:
- **Application:** `http://your-ec2-public-ip/`
- **API Docs:** `http://your-ec2-public-ip/api/docs`
- **Flower (Celery Monitor):** `http://your-ec2-public-ip/admin/flower/`

### Production Setup:
- **Application:** `https://yourdomain.com/`
- **API Docs:** `https://yourdomain.com/api/docs`
- **Flower (Celery Monitor):** `https://yourdomain.com/admin/flower/`

## Troubleshooting

### Common Issues:

1. **"Connection refused" error:**
   ```bash
   # Check if services are running
   docker-compose -f docker-compose.prod.yml ps
   
   # Restart if needed
   docker-compose -f docker-compose.prod.yml restart
   ```

2. **SSL certificate errors:**
   ```bash
   # Check SSL setup
   ./scripts/ssl-setup.sh -d yourdomain.com --test
   
   # Renew certificates if needed
   ./scripts/ssl-setup.sh -d yourdomain.com --renew
   ```

3. **502 Bad Gateway:**
   ```bash
   # Check backend logs
   docker-compose -f docker-compose.prod.yml logs backend
   
   # Check if backend is healthy
   curl http://localhost:8000/health
   ```

4. **Permission denied errors:**
   ```bash
   # Make sure you're in the docker group
   sudo usermod -aG docker ubuntu
   # Log out and log back in
   ```

## Security Notes

- The nginx configuration includes security headers and rate limiting
- Flower monitoring is protected and accessible only via `/admin/flower/`
- Static files are cached for performance
- File uploads have special handling with increased timeouts

## Next Steps

After nginx is set up:

1. **Test your application** - Make sure all features work
2. **Set up monitoring** - Check Flower for Celery tasks
3. **Configure backups** - Set up database backups
4. **Set up log rotation** - Manage log file sizes
5. **Configure alerts** - Monitor application health

## Quick Commands Reference

```bash
# Setup development (HTTP)
./scripts/nginx-config.sh setup-dev

# Setup production (HTTPS)
./scripts/nginx-config.sh setup-prod -d yourdomain.com

# Check status
./scripts/nginx-config.sh status

# View logs
./scripts/nginx-config.sh logs

# Reload configuration
./scripts/nginx-config.sh reload

# Validate configuration
./scripts/nginx-config.sh validate

# Deploy application
./scripts/deploy-with-vault.sh
```

---

**Ready to proceed?** 

If you just want to test quickly, use the development setup. If you have a domain and want production setup, use the production option.

The `deploy-with-vault.sh` script will handle most of the heavy lifting once nginx is configured!