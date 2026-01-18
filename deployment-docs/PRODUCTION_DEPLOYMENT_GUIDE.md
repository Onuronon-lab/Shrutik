# Production Deployment Guide - Shrutik

**Complete production setup with domain (shrutik.org) and SSL certificates**

## Prerequisites

- ✅ EC2 instance running
- ✅ Vault configured
- ✅ Domain purchased (shrutik.org from Namecheap)
- ✅ SSH access to EC2

## Step 1: Configure DNS in Namecheap

### Get Your EC2 Public IP
```bash
# On your EC2 instance:
curl -s http://checkip.amazonaws.com/
# Example: 3.15.123.45
```

### Set Up DNS Records in Namecheap
1. **Log into Namecheap**
   - Go to namecheap.com → Domain List
   - Click "Manage" next to shrutik.org

2. **Go to Advanced DNS tab**

3. **Add/Update these DNS records:**
   ```
   Type: A Record    | Host: @     | Value: 3.15.123.45 | TTL: 300
   Type: A Record    | Host: www   | Value: 3.15.123.45 | TTL: 300
   ```

4. **Delete any existing records** that point to parking pages

5. **Wait for DNS propagation** (5-30 minutes)

### Test DNS Propagation
```bash
# From your local machine (not EC2):
nslookup shrutik.org
dig shrutik.org

# Should return your EC2 IP address
```

## Step 2: Configure Security Groups

Ensure your EC2 security group allows HTTPS traffic:

**Required inbound rules:**
- **HTTP (80):** 0.0.0.0/0 - For Let's Encrypt verification
- **HTTPS (443):** 0.0.0.0/0 - For secure traffic
- **SSH (22):** Your IP only

**Via AWS Console:**
1. EC2 → Security Groups → Your security group
2. Add inbound rules for ports 80 and 443

**Via CLI:**
```bash
# First, find your security group ID:
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
SECURITY_GROUP_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)

# Then add the rules:
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 443 --cidr 0.0.0.0/0
```

## Step 3: Install Docker (if not already installed)

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

# Log out and log back in
exit
# SSH back in
```

## Step 4: Update Domain Configuration in Vault

```bash
# Navigate to project directory
cd /opt/shrutik

# Update Vault with your domain
export VAULT_ADDR='http://127.0.0.1:8200'
vault kv patch secret/shrutik/domain \
  domain_name="shrutik.org" \
  ssl_email="admin@shrutik.org"

# Verify the update
vault kv get secret/shrutik/domain
```

## Step 5: Set Up Production Nginx Configuration

```bash
# Set up nginx for production with SSL
./scripts/nginx-config.sh setup-prod -d shrutik.org
```

**Expected output:**
```
🔧 Setting up nginx for production environment...
Domain: shrutik.org
⚠️  Creating placeholder SSL certificates...
✅ Production configuration activated
Configuration: HTTPS with SSL certificates
Domain: https://shrutik.org/

⚠️  Next steps:
1. Run SSL setup script: ./scripts/ssl-setup.sh -d shrutik.org
2. Update DNS records to point to this server
3. Test configuration: ./scripts/nginx-config.sh validate
```

## Step 6: Deploy the Application

```bash
# Deploy with Vault secrets
./scripts/deploy-with-vault.sh
```

**Expected output:**
```
🚀 Deploying Shrutik with Vault secrets...
✅ Secrets retrieved from Vault
✅ Docker containers started
✅ Database initialized
✅ Application deployed successfully

Access your application at:
• Frontend: https://shrutik.org/
• API: https://shrutik.org/api/
• Admin: https://shrutik.org/admin/flower/
```

## Step 7: Set Up SSL Certificates

**Wait for DNS to propagate first!** Test with `nslookup shrutik.org`

```bash
# Set up Let's Encrypt SSL certificates
./scripts/ssl-setup.sh -d shrutik.org
```

**Expected output:**
```
🔒 Setting up SSL certificates for shrutik.org...
✅ Let's Encrypt certificates obtained
✅ Nginx configuration updated
✅ SSL certificates installed

Your site is now secure: https://shrutik.org/
```

## Step 8: Verify Production Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Test HTTPS
curl -I https://shrutik.org/
# Should return: HTTP/2 200

# Test API
curl https://shrutik.org/api/health
# Should return: {"status": "healthy"}

# Test SSL certificate
curl -I https://shrutik.org/ | grep -i "HTTP"
# Should show HTTP/2 200
```

## Step 9: Configure SSL Auto-Renewal

```bash
# Set up automatic certificate renewal
sudo crontab -e

# Add this line to renew certificates monthly:
0 3 1 * * /opt/shrutik/scripts/ssl-setup.sh -d shrutik.org --renew
```

## Step 10: Set Up Monitoring and Backups

### Database Backups
```bash
# Create backup script
sudo crontab -e

# Add daily database backup at 2 AM:
0 2 * * * docker exec $(docker-compose -f /opt/shrutik/docker-compose.prod.yml ps -q postgres) pg_dump -U production_user voice_collection > /opt/backups/db_$(date +\%Y\%m\%d).sql
```

### Log Rotation
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/docker

# Add:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

## Production URLs

Your application is now live at:

- **Main Application:** https://shrutik.org/
- **API Documentation:** https://shrutik.org/api/docs
- **Admin Panel:** https://shrutik.org/admin/flower/
- **Health Check:** https://shrutik.org/health

## Managing Production

### View Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs

# View specific service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs nginx

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Redeploy (zero-downtime)
./scripts/deploy-with-vault.sh

# Or manual update:
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Scale Services
```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=2
```

## Taking Production DOWN (Maintenance)

### Planned Maintenance
```bash
# Put up maintenance page (if you have one)
# Then stop services gracefully
docker-compose -f docker-compose.prod.yml stop

# To start again
docker-compose -f docker-compose.prod.yml start
```

### Emergency Shutdown
```bash
# Complete shutdown
docker-compose -f docker-compose.prod.yml down

# To redeploy
./scripts/deploy-with-vault.sh
```

## Monitoring and Alerts

### Health Checks
```bash
# Create health check script
nano /opt/shrutik/scripts/health-monitor.sh

#!/bin/bash
if ! curl -f https://shrutik.org/health > /dev/null 2>&1; then
    echo "ALERT: Shrutik is down!" | mail -s "Shrutik Down" admin@shrutik.org
fi

# Run every 5 minutes
sudo crontab -e
*/5 * * * * /opt/shrutik/scripts/health-monitor.sh
```

### Disk Space Monitoring
```bash
# Monitor disk usage
df -h
docker system df

# Clean up old images/containers
docker system prune -f
```

## Security Hardening

### Firewall Configuration
```bash
# Enable UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 8200/tcp  # Block Vault from external access
```

### Regular Updates
```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Troubleshooting

### SSL Certificate Issues
```bash
# Check certificate status
./scripts/ssl-setup.sh -d shrutik.org --test

# Renew certificates manually
./scripts/ssl-setup.sh -d shrutik.org --renew

# Check certificate expiry
openssl x509 -in /opt/shrutik/nginx/ssl/live/shrutik.org/fullchain.pem -text -noout | grep "Not After"
```

### DNS Issues
```bash
# Test DNS resolution
nslookup shrutik.org
dig shrutik.org

# Check if domain points to correct IP
host shrutik.org
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Check database performance
docker-compose -f docker-compose.prod.yml exec postgres psql -U production_user -d voice_collection -c "SELECT * FROM pg_stat_activity;"

# Check nginx access logs
docker-compose -f docker-compose.prod.yml logs nginx | tail -100
```

## Backup and Recovery

### Full Backup
```bash
# Create backup directory
sudo mkdir -p /opt/backups

# Backup database
docker exec $(docker-compose -f docker-compose.prod.yml ps -q postgres) pg_dump -U production_user voice_collection > /opt/backups/db_backup.sql

# Backup uploaded files
tar -czf /opt/backups/uploads_backup.tar.gz /opt/shrutik/uploads/

# Backup Vault data
sudo tar -czf /opt/backups/vault_backup.tar.gz /opt/vault/data/
```

### Recovery
```bash
# Restore database
docker exec -i $(docker-compose -f docker-compose.prod.yml ps -q postgres) psql -U production_user voice_collection < /opt/backups/db_backup.sql

# Restore uploads
tar -xzf /opt/backups/uploads_backup.tar.gz -C /
```

## Quick Commands Reference

```bash
# Production deployment
./scripts/nginx-config.sh setup-prod -d shrutik.org
./scripts/deploy-with-vault.sh
./scripts/ssl-setup.sh -d shrutik.org

# Check status
docker-compose -f docker-compose.prod.yml ps
curl -I https://shrutik.org/

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Update application
git pull && ./scripts/deploy-with-vault.sh

# Maintenance mode
docker-compose -f docker-compose.prod.yml stop
docker-compose -f docker-compose.prod.yml start
```

---

**Congratulations!** 🎉 

Shrutik is now live in production at **https://shrutik.org/** with:
- ✅ SSL certificates (HTTPS)
- ✅ Automatic certificate renewal
- ✅ Production-grade security
- ✅ Monitoring and backups
- ✅ Scalable architecture

Your voice collection platform is ready for real users!