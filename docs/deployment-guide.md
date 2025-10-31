# Deployment Guide

This comprehensive guide covers deploying Shrutik in various environments, from development to production, including cloud platforms and on-premises infrastructure.

## 🎯 Deployment Overview

Shrutik supports multiple deployment strategies to accommodate different use cases, from small community instances to large-scale enterprise deployments.

### Deployment Options

| Option | Use Case | Complexity | Scalability |
|--------|----------|------------|-------------|
| **Docker Compose** | Development, Small Teams | Low | Limited |
| **Kubernetes** | Production, Enterprise | High | Excellent |
| **Cloud Platforms** | Managed Services | Medium | Excellent |
| **Bare Metal** | On-Premises, Custom | Medium | Good |

## 🐳 Docker Compose Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB disk space

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/shrutik.git
cd shrutik

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Deploy
docker-compose up -d

# Verify deployment
docker-compose ps
curl http://localhost:8000/health
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

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
      - ./backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  backend:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=${FRONTEND_API_URL}
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./uploads:/var/www/uploads:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

Deploy production:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster 1.24+
- kubectl configured
- Helm 3.0+ (optional)
- Ingress controller
- Persistent storage

### Namespace Setup

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: shrutik
  labels:
    name: shrutik
```

### ConfigMap and Secrets

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shrutik-config
  namespace: shrutik
data:
  DATABASE_URL: "postgresql://shrutik:password@postgres:5432/shrutik"
  REDIS_URL: "redis://redis:6379/0"
  UPLOAD_DIR: "/app/uploads"
  LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: shrutik-secrets
  namespace: shrutik
type: Opaque
stringData:
  SECRET_KEY: "your-super-secret-key-change-in-production"
  POSTGRES_PASSWORD: "secure-database-password"
  SMTP_PASSWORD: "email-service-password"
```

### Database Deployment

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: shrutik
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: shrutik
        - name: POSTGRES_USER
          value: shrutik
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: shrutik-secrets
              key: POSTGRES_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: shrutik
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Redis Deployment

```yaml
# redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: shrutik
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--appendonly", "yes"]
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: shrutik
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: shrutik
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### Backend Deployment

```yaml
# backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: shrutik
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: shrutik/backend:latest
        envFrom:
        - configMapRef:
            name: shrutik-config
        - secretRef:
            name: shrutik-secrets
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: uploads-storage
          mountPath: /app/uploads
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: uploads-storage
        persistentVolumeClaim:
          claimName: uploads-pvc

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
  namespace: shrutik
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi

---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: shrutik
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
```

### Worker Deployment

```yaml
# worker.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  namespace: shrutik
spec:
  replicas: 5
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: shrutik/backend:latest
        command: ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]
        envFrom:
        - configMapRef:
            name: shrutik-config
        - secretRef:
            name: shrutik-secrets
        volumeMounts:
        - name: uploads-storage
          mountPath: /app/uploads
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: uploads-storage
        persistentVolumeClaim:
          claimName: uploads-pvc
```

### Frontend Deployment

```yaml
# frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: shrutik
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: shrutik/frontend:latest
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "https://api.yourdomain.com"
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "256Mi"
            cpu: "125m"
          limits:
            memory: "512Mi"
            cpu: "250m"

---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: shrutik
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shrutik-ingress
  namespace: shrutik
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - yourdomain.com
    - api.yourdomain.com
    secretName: shrutik-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

### Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f backend.yaml
kubectl apply -f worker.yaml
kubectl apply -f frontend.yaml
kubectl apply -f ingress.yaml

# Check deployment status
kubectl get pods -n shrutik
kubectl get services -n shrutik
kubectl get ingress -n shrutik
```

## ☁️ Cloud Platform Deployments

### AWS Deployment

#### Using AWS ECS with Fargate

```yaml
# ecs-task-definition.json
{
  "family": "shrutik-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/shrutik-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/shrutik"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-endpoint:6379/0"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:shrutik/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/shrutik-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Infrastructure as Code (Terraform)

```hcl
# main.tf
provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "shrutik-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  tags = {
    Environment = var.environment
    Project     = "shrutik"
  }
}

# RDS Database
resource "aws_db_instance" "postgres" {
  identifier = "shrutik-postgres"
  
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.medium"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true
  
  db_name  = "shrutik"
  username = "shrutik"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "shrutik-final-snapshot"
  
  tags = {
    Environment = var.environment
    Project     = "shrutik"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "shrutik-cache-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "shrutik-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
  
  tags = {
    Environment = var.environment
    Project     = "shrutik"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "shrutik-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Environment = var.environment
    Project     = "shrutik"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "shrutik-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = false
  
  tags = {
    Environment = var.environment
    Project     = "shrutik"
  }
}

# S3 Bucket for file storage
resource "aws_s3_bucket" "uploads" {
  bucket = "shrutik-uploads-${var.environment}"
  
  tags = {
    Environment = var.environment
    Project     = "shrutik"
  }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

### Google Cloud Platform (GCP)

#### Using Google Kubernetes Engine (GKE)

```bash
# Create GKE cluster
gcloud container clusters create shrutik-cluster \
    --zone=us-central1-a \
    --num-nodes=3 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=10 \
    --machine-type=e2-standard-2 \
    --disk-size=50GB \
    --enable-autorepair \
    --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials shrutik-cluster --zone=us-central1-a

# Deploy using kubectl (same as Kubernetes section above)
```

#### Cloud SQL and Redis

```bash
# Create Cloud SQL instance
gcloud sql instances create shrutik-postgres \
    --database-version=POSTGRES_15 \
    --tier=db-custom-2-4096 \
    --region=us-central1 \
    --storage-size=100GB \
    --storage-type=SSD \
    --backup-start-time=03:00

# Create database
gcloud sql databases create shrutik --instance=shrutik-postgres

# Create Redis instance
gcloud redis instances create shrutik-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0
```

### Microsoft Azure

#### Using Azure Container Instances (ACI)

```yaml
# azure-container-group.yaml
apiVersion: 2019-12-01
location: eastus
name: shrutik-container-group
properties:
  containers:
  - name: backend
    properties:
      image: shrutik/backend:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
      ports:
      - port: 8000
      environmentVariables:
      - name: DATABASE_URL
        secureValue: postgresql://user:pass@postgres.database.azure.com:5432/shrutik
      - name: REDIS_URL
        secureValue: redis://shrutik.redis.cache.windows.net:6380/0
  - name: frontend
    properties:
      image: shrutik/frontend:latest
      resources:
        requests:
          cpu: 0.5
          memoryInGb: 1
      ports:
      - port: 3000
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 80
    - protocol: tcp
      port: 8000
    - protocol: tcp
      port: 3000
type: Microsoft.ContainerInstance/containerGroups
```

## 🖥️ Bare Metal Deployment

### Server Requirements

#### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 100GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 20.04+ or CentOS 8+

#### Recommended Production
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Storage**: 500GB+ SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS

### Installation Steps

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql redis-server nginx

# 3. Create application user
sudo useradd -m -s /bin/bash shrutik
sudo usermod -aG sudo shrutik

# 4. Setup application directory
sudo mkdir -p /opt/shrutik
sudo chown shrutik:shrutik /opt/shrutik

# 5. Switch to application user
sudo su - shrutik

# 6. Clone and setup application
cd /opt/shrutik
git clone https://github.com/your-org/shrutik.git .
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Setup database
sudo -u postgres createuser shrutik
sudo -u postgres createdb shrutik -O shrutik
sudo -u postgres psql -c "ALTER USER shrutik PASSWORD 'secure_password';"

# 8. Configure environment
cp .env.example .env
nano .env  # Edit configuration

# 9. Run migrations
alembic upgrade head

# 10. Build frontend
cd frontend
npm install
npm run build
cd ..

# 11. Setup systemd services
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shrutik-backend shrutik-worker
sudo systemctl start shrutik-backend shrutik-worker

# 12. Configure Nginx
sudo cp deployment/nginx/shrutik.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/shrutik.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Systemd Service Files

#### Backend Service

```ini
# /etc/systemd/system/shrutik-backend.service
[Unit]
Description=Shrutik Backend API
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=shrutik
Group=shrutik
WorkingDirectory=/opt/shrutik
Environment=PATH=/opt/shrutik/venv/bin
ExecStart=/opt/shrutik/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Worker Service

```ini
# /etc/systemd/system/shrutik-worker.service
[Unit]
Description=Shrutik Celery Worker
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=shrutik
Group=shrutik
WorkingDirectory=/opt/shrutik
Environment=PATH=/opt/shrutik/venv/bin
ExecStart=/opt/shrutik/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 🔧 Configuration Management

### Environment-Specific Configurations

#### Development
```env
DEBUG=true
LOG_LEVEL=DEBUG
USE_CELERY=false
DATABASE_URL=postgresql://postgres:password@localhost:5432/shrutik_dev
REDIS_URL=redis://localhost:6379/1
```

#### Staging
```env
DEBUG=false
LOG_LEVEL=INFO
USE_CELERY=true
DATABASE_URL=postgresql://shrutik:password@staging-db:5432/shrutik
REDIS_URL=redis://staging-redis:6379/0
```

#### Production
```env
DEBUG=false
LOG_LEVEL=WARNING
USE_CELERY=true
DATABASE_URL=postgresql://shrutik:secure_password@prod-db:5432/shrutik
REDIS_URL=redis://prod-redis:6379/0
SENTRY_DSN=https://your-sentry-dsn
```

### Configuration Validation

```python
# config_validator.py
import os
import sys
from urllib.parse import urlparse

def validate_config():
    """Validate deployment configuration."""
    errors = []
    
    # Required environment variables
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'SECRET_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate database URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        parsed = urlparse(db_url)
        if parsed.scheme not in ['postgresql', 'postgres']:
            errors.append("DATABASE_URL must use postgresql:// scheme")
    
    # Validate Redis URL
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        parsed = urlparse(redis_url)
        if parsed.scheme != 'redis':
            errors.append("REDIS_URL must use redis:// scheme")
    
    # Validate secret key
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and len(secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters long")
    
    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Configuration validation passed!")

if __name__ == "__main__":
    validate_config()
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints

```python
# Health check implementation
@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    checks = {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### Monitoring Setup

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus_data:
  grafana_data:
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push backend
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ghcr.io/${{ github.repository }}/backend:latest
    
    - name: Build and push frontend
      uses: docker/build-push-action@v4
      with:
        context: ./frontend
        push: true
        tags: ghcr.io/${{ github.repository }}/frontend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.PROD_HOST }}
        username: ${{ secrets.PROD_USER }}
        key: ${{ secrets.PROD_SSH_KEY }}
        script: |
          cd /opt/shrutik
          git pull origin main
          docker-compose pull
          docker-compose up -d
          docker system prune -f
```

## 🚨 Troubleshooting

### Common Deployment Issues

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec backend python -c "
from app.db.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### Redis Connection Issues
```bash
# Test Redis connectivity
docker-compose exec backend python -c "
from app.core.redis_client import redis_client
try:
    redis_client.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
"
```

#### File Permission Issues
```bash
# Fix file permissions
sudo chown -R 1000:1000 uploads/
chmod -R 755 uploads/
```

#### Memory Issues
```bash
# Check memory usage
docker stats
free -h
df -h

# Adjust container memory limits
docker-compose up -d --scale backend=1
```

### Log Analysis

```bash
# View application logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend

# Check system logs
journalctl -u shrutik-backend -f
journalctl -u shrutik-worker -f

# Analyze error patterns
grep -i error /var/log/shrutik/*.log | tail -20
```

## 📚 Additional Resources

- **[Docker Documentation](https://docs.docker.com/)**
- **[Kubernetes Documentation](https://kubernetes.io/docs/)**
- **[AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)**
- **[GCP GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)**
- **[Azure Container Instances](https://docs.microsoft.com/en-us/azure/container-instances/)**

---

This deployment guide provides comprehensive coverage for deploying Shrutik in various environments. Choose the deployment strategy that best fits your requirements, infrastructure, and expertise level.