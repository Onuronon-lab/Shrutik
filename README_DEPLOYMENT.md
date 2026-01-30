# Shrutik Deployment - Quick Start

**Streamlined deployment for development testing on EC2**

## Quick Setup (2 Scripts Only)

### 1. Local Machine (Build & Sync)
```bash
# Build and push your Docker image
docker build -f Dockerfile.prod -t yourusername/shrutik:latest .
docker push yourusername/shrutik:latest

# Sync files to EC2
./scripts/local-setup.sh yourusername/shrutik:latest
```

### 2. EC2 Instance (Deploy Everything)
```bash
# SSH to EC2
ssh shrutik-ec2

# Run complete deployment
cd /opt/shrutik
./scripts/ec2-deploy.sh yourusername/shrutik:latest
```

**That's it!** Your application will be running at `http://YOUR-EC2-IP:3080/`

## What Gets Set Up

- ✅ **HashiCorp Vault** for secure secrets management
- ✅ **Docker & Docker Compose** installation
- ✅ **PostgreSQL** database with initialization
- ✅ **Redis** for caching and Celery
- ✅ **Nginx** reverse proxy (HTTP for development)
- ✅ **Celery** workers for background tasks
- ✅ **Flower** monitoring dashboard
- ✅ **Health checks** and logging

## Access URLs

After deployment:
- **Main App:** `http://YOUR-EC2-IP:3080/`
- **API Docs:** `http://YOUR-EC2-IP:3080/api/docs`
- **Admin Panel:** `http://YOUR-EC2-IP:3080/admin/flower/`
- **Health Check:** `http://YOUR-EC2-IP:3080/health`

## Management Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update application
docker-compose pull && docker-compose up -d

# Stop/start
docker-compose stop
docker-compose start
```

## Files Structure

```
├── DEPLOYMENT_GUIDE.md          # Complete deployment guide
├── docker-compose.yml           # Single Docker Compose file
├── scripts/
│   ├── local-setup.sh          # Run on local machine
│   ├── ec2-deploy.sh           # Run on EC2 instance
│   ├── vault-setup.sh          # Vault installation (auto-called)
│   ├── vault-configure.sh      # Vault configuration (auto-called)
│   ├── vault-secrets.sh        # Vault secrets management
│   ├── nginx-config.sh         # Nginx configuration
│   └── health-check.sh         # Health monitoring
└── nginx/                      # Nginx configuration files
```

## Security Groups

Make sure your EC2 security group allows:
- **HTTP (3080):** `0.0.0.0/0`
- **SSH (22):** Your IP only

## Troubleshooting

1. **Can't access application:** Check security groups allow port 3080
2. **Services not starting:** Check logs with `docker-compose logs`
3. **Vault issues:** May need to unseal after EC2 restart
4. **Database issues:** Check PostgreSQL logs with `docker-compose logs postgres`

## Going to Production

When ready for production with your own domain:
1. Update Vault with domain: `vault kv patch secret/shrutik/domain domain_name="yourdomain.com"`
2. Set up SSL certificates
3. Configure production nginx with HTTPS
4. Update security groups for HTTPS (port 443)

---

**Need help?** Check the complete [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.