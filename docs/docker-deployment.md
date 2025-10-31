# Docker Deployment Guide

This guide covers deploying Shrutik in production using Docker and Docker Compose, including configuration for different environments and scaling considerations.

## 🎯 Overview

Shrutik is designed to be deployed easily using Docker containers. This guide covers:

- Production deployment with Docker Compose
- Environment configuration
- SSL/TLS setup
- Monitoring and logging
- Backup and recovery
- Scaling considerations

## 🚀 Quick Production Deployment

### Prerequisites

- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher
- **Domain**: For SSL certificate (recommended)
- **Server**: Minimum 2GB RAM, 2 CPU cores

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Deploy Shrutik

```bash
# Clone repository
git clone https://github.com/Onuronon-lab/Shrutik.git
cd shrutik

# Copy and configure environment
cp .env.example .env
nano .env  # Edit configuration

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

## 🔧 Production Configuration

### Environment Variables (.env)

```env
# Application
APP_NAME=Shrutik
DEBUG=false
VERSION=1.0.0

# Database
DATABASE_URL=postgresql://shrutik_user:secure_password@db:5432/shrutik
POSTGRES_DB=shrutik
POSTGRES_USER=shrutik_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_HOSTS=["https://yourdomain.com", "https://www.yourdomain.com"]

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=104857600  # 100MB

# Performance
ENABLE_CACHING=true
ENABLE_RATE_LIMITING=true
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# CDN (Optional)
CDN_ENABLED=false
CDN_BASE_URL=https://cdn.yourdomain.com
CDN_PROVIDER=cloudflare

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn  # Optional

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Docker Compose Configuration

The main `docker-compose.yml` includes:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - db
      - redis
    restart: unless-stopped

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

## 🔒 SSL/TLS Setup

### Option 1: Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: Manual SSL Certificate

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS Configuration
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # File uploads
        client_max_body_size 100M;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }
}
```

## 📊 Monitoring and Logging

### Health Checks

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs worker

# Follow logs in real-time
docker-compose logs -f
```

### Monitoring Setup

Create `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana_data:
```

Start monitoring:

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Log Management

Configure log rotation in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## 💾 Backup and Recovery

### Database Backup

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T db pg_dump -U shrutik_user shrutik > $BACKUP_DIR/db_backup_$DATE.sql

# Files backup
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz uploads/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /path/to/shrutik/backup.sh
```

### Recovery

```bash
# Restore database
docker-compose exec -T db psql -U shrutik_user -d shrutik < /path/to/backup.sql

# Restore files
tar -xzf /path/to/uploads_backup.tar.gz
```

## 📈 Scaling

### Horizontal Scaling

Scale specific services:

```bash
# Scale workers
docker-compose up -d --scale worker=3

# Scale backend
docker-compose up -d --scale backend=2
```

### Load Balancer Configuration

For multiple backend instances, update `nginx.conf`:

```nginx
upstream backend {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

### Database Scaling

For high-traffic deployments:

1. **Read Replicas**: Configure PostgreSQL read replicas
2. **Connection Pooling**: Use PgBouncer
3. **Caching**: Enable Redis clustering

## 🔧 Maintenance

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Clean up old images
docker system prune -f
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current
```

### Performance Tuning

Monitor and adjust:

```bash
# Check resource usage
docker stats

# Adjust memory limits in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Restart specific service
docker-compose restart backend

# Full restart
docker-compose down && docker-compose up -d
```

**Database connection issues:**
```bash
# Check database status
docker-compose exec db pg_isready -U shrutik_user

# Reset database
docker-compose down -v
docker-compose up -d
```

**SSL certificate issues:**
```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Test SSL configuration
openssl s_client -connect yourdomain.com:443
```

### Performance Issues

```bash
# Check system resources
htop
df -h
free -h

# Monitor Docker containers
docker stats

# Check application metrics
curl http://localhost:8000/metrics
```

## 📚 Additional Resources

- **[Architecture Overview](architecture.md)** - System design details
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Monitoring Guide](monitoring.md)** - Advanced monitoring setup
- **[Security Guide](security.md)** - Security best practices

## 🆘 Support

For deployment issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review [GitHub issues](https://github.com/Onuronon-lab/Shrutik/issues)
3. Join our [Discord community](https://discord.gg/9hZ9eW8ARk)
4. Contact support at deploy@shrutik.org

Happy deploying! 🚀