# Shrutik Kubernetes Deployment Guide

This guide explains how to deploy Shrutik to the NesoHQ Kubernetes cluster.

## Overview

Shrutik is deployed using the same infrastructure pattern as other NesoHQ applications:
- **2 Docker images** (backend, frontend) pushed to GitHub Container Registry
- **Kustomize** for Kubernetes manifest management
- **GitHub Actions** for automated CI/CD
- **Traefik** for ingress routing
- **Caddy** for SSL termination

## Architecture

```
Internet (HTTPS)
    ↓
Caddy (VPS) - SSL Termination
    ↓
Traefik (K8s) - Ingress Controller
    ↓
┌─────────────────────────────────────────┐
│  Shrutik Application Components         │
├─────────────────────────────────────────┤
│  Frontend (3 replicas)                  │
│  Backend API (3 replicas)               │
│  Celery Worker (3 replicas)             │
│  Celery Beat (1 replica)                │
├─────────────────────────────────────────┤
│  PostgreSQL (StatefulSet)               │
│  Redis (StatefulSet)                    │
└─────────────────────────────────────────┘
```

## Components

### Applications (Deployments)
| Component | Replicas | Image | Purpose |
|-----------|----------|-------|---------|
| shrutik-frontend | 3 | ghcr.io/onuronon-lab/shrutik-frontend | React web interface |
| shrutik-backend | 3 | ghcr.io/onuronon-lab/shrutik-backend | FastAPI REST API |
| shrutik-celery-worker | 3 | ghcr.io/onuronon-lab/shrutik-backend | Background task processing |
| shrutik-celery-beat | 1 | ghcr.io/onuronon-lab/shrutik-backend | Task scheduler |

### Databases (StatefulSets)
| Component | Node | Storage | Purpose |
|-----------|------|---------|---------|
| postgres-shrutik | ip-172-31-38-6 | /data/postgres-shrutik | Application database |
| redis-shrutik | ip-172-31-18-79 | /data/redis-shrutik | Cache & Celery broker |

### Shared Storage
| Path | Purpose |
|------|---------|
| /data/shrutik/uploads | Voice recordings and audio chunks |
| /data/shrutik/exports | Export batch archives |

## Deployment Steps

### 1. Build and Push Images

The GitHub Actions workflow automatically builds and pushes images when you push to `main` or `prod` branches:

```bash
# Push to main triggers image build
git add .
git commit -m "Update Shrutik"
git push origin main
```

This creates images:
- `ghcr.io/onuronon-lab/shrutik-backend:latest`
- `ghcr.io/onuronon-lab/shrutik-frontend:latest`

### 2. Deploy to Kubernetes

The deployment is managed in the `nesohq-infra` repository:

```bash
cd nesohq-infra

# Deploy to staging (automatic on main branch push)
kubectl apply -k infra/overlays/staging/

# Deploy to production (automatic on prod branch push)
kubectl apply -k infra/overlays/prod/
```

### 3. Verify Deployment

```bash
# Check all Shrutik pods
kubectl get pods -l app=shrutik-backend
kubectl get pods -l app=shrutik-frontend
kubectl get pods -l app=shrutik-celery-worker
kubectl get pods -l app=shrutik-celery-beat

# Check databases
kubectl get pods -l app=postgres-shrutik
kubectl get pods -l app=redis-shrutik

# Check services
kubectl get svc | grep shrutik

# Check ingress
kubectl get ingress | grep shrutik
```

### 4. Configure DNS

Add DNS records pointing to the VPS public IP (91.98.134.15):

```
A Record: shrutik.nesohq.org → 91.98.134.15
A Record: api.shrutik.nesohq.org → 91.98.134.15
```

### 5. Update Caddy Configuration

On the VPS, add Shrutik domains to the Caddyfile:

```caddyfile
# Add to ~/nesohq-infra/Caddyfile

shrutik.nesohq.org {
    reverse_proxy 91.98.134.15:30080
}

api.shrutik.nesohq.org {
    reverse_proxy 91.98.134.15:30080
}
```

Reload Caddy:

```bash
cd ~/nesohq-infra/production-rancher
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## CI/CD Workflow

### Automatic Deployment Flow

**Staging (main branch):**
```
1. Push to main branch
2. GitHub Actions builds images
3. Images pushed to ghcr.io
4. nesohq-infra main branch updated
5. Staging deployment triggered
6. Pods rolled out
```

**Production (prod branch):**
```
1. Merge main to prod
2. GitHub Actions builds images with prod tag
3. Images pushed to ghcr.io
4. nesohq-infra prod branch updated
5. Production deployment triggered
6. Pods rolled out with 3 replicas
```

## Environment Variables

### Backend & Celery
```yaml
DATABASE_URL: postgresql://shrutik:Shrutik2026SecurePass@postgres-shrutik-0.postgres-shrutik.default.svc.cluster.local:5432/voice_collection
REDIS_URL: redis://redis-shrutik-0.redis-shrutik.default.svc.cluster.local:6379/0
SECRET_KEY: Shrutik2026ProductionSecretKeyChangeThis
DEBUG: false
USE_CELERY: true
ALLOWED_HOSTS: ["https://shrutik.nesohq.org","https://api.shrutik.nesohq.org"]
UPLOAD_DIR: /app/uploads
EXPORT_LOCAL_DIR: /app/exports
```

### Frontend
```yaml
VITE_API_URL: https://api.shrutik.nesohq.org/api
```

## Database Initialization

The migration job runs automatically on deployment:

```bash
# Check migration job status
kubectl get jobs | grep shrutik-migrations

# View migration logs
kubectl logs job/shrutik-migrations
```

Manual migration (if needed):

```bash
# Get backend pod name
POD=$(kubectl get pod -l app=shrutik-backend -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $POD -- alembic upgrade head

# Initialize database
kubectl exec -it $POD -- python -c "from app.db.init_db import init_db; from app.db.database import SessionLocal; db = SessionLocal(); init_db(db); db.close()"
```

## Scaling

### Scale Applications

```bash
# Scale backend
kubectl scale deployment shrutik-backend --replicas=5

# Scale frontend
kubectl scale deployment shrutik-frontend --replicas=5

# Scale Celery workers
kubectl scale deployment shrutik-celery-worker --replicas=5

# Note: Celery Beat MUST remain at 1 replica (scheduler)
```

### Update Production Replicas

Edit `nesohq-infra/infra/overlays/prod/kustomization.yaml`:

```yaml
patches:
- target:
    kind: Deployment
    name: shrutik-backend
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 5  # Change this
```

## Monitoring

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/shrutik-backend

# Frontend logs
kubectl logs -f deployment/shrutik-frontend

# Celery worker logs
kubectl logs -f deployment/shrutik-celery-worker

# Celery beat logs
kubectl logs -f deployment/shrutik-celery-beat

# Database logs
kubectl logs -f statefulset/postgres-shrutik
kubectl logs -f statefulset/redis-shrutik
```

### Check Health

```bash
# Backend health
curl https://api.shrutik.nesohq.org/health

# Frontend
curl https://shrutik.nesohq.org/

# Database connections
kubectl exec -it postgres-shrutik-0 -- psql -U shrutik -d voice_collection -c "SELECT version();"
kubectl exec -it redis-shrutik-0 -- redis-cli ping
```

### Resource Usage

```bash
# Pod resource usage
kubectl top pods | grep shrutik

# Node distribution
kubectl get pods -o wide | grep shrutik
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by='.lastTimestamp' | grep shrutik

# Check logs
kubectl logs <pod-name>
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it shrutik-backend-<pod-id> -- python -c "from app.db.database import engine; engine.connect()"

# Check database pod
kubectl logs postgres-shrutik-0

# Check service DNS
kubectl exec -it shrutik-backend-<pod-id> -- nslookup postgres-shrutik-0.postgres-shrutik.default.svc.cluster.local
```

### Celery Not Processing Tasks

```bash
# Check Celery worker logs
kubectl logs -f deployment/shrutik-celery-worker

# Check Redis connectivity
kubectl exec -it shrutik-celery-worker-<pod-id> -- python -c "import redis; r = redis.from_url('redis://redis-shrutik-0.redis-shrutik.default.svc.cluster.local:6379/0'); print(r.ping())"

# Check Celery beat scheduler
kubectl logs -f deployment/shrutik-celery-beat
```

### Storage Issues

```bash
# Check storage on nodes
kubectl get nodes
kubectl describe node ip-172-31-38-6 | grep -A 5 "Allocated resources"

# Check volume mounts
kubectl exec -it shrutik-backend-<pod-id> -- df -h /app/uploads
kubectl exec -it shrutik-backend-<pod-id> -- df -h /app/exports
```

## Rollback

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment/shrutik-backend

# Rollback to previous version
kubectl rollout undo deployment/shrutik-backend
kubectl rollout undo deployment/shrutik-frontend
kubectl rollout undo deployment/shrutik-celery-worker

# Rollback to specific revision
kubectl rollout undo deployment/shrutik-backend --to-revision=2
```

### Rollback Images

```bash
# Use specific image tag
kubectl set image deployment/shrutik-backend shrutik-backend=ghcr.io/onuronon-lab/shrutik-backend:main-abc123
```

## Maintenance

### Update Application

```bash
# Update code in Shrutik repo
cd ~/Shrutik
git pull origin main

# Rebuild and push images (automatic via GitHub Actions)
git push origin main

# Update nesohq-infra
cd ~/nesohq-infra
git pull origin main

# Restart deployments to pull new images
kubectl rollout restart deployment/shrutik-backend
kubectl rollout restart deployment/shrutik-frontend
kubectl rollout restart deployment/shrutik-celery-worker
kubectl rollout restart deployment/shrutik-celery-beat
```

### Database Backup

```bash
# Backup PostgreSQL
kubectl exec postgres-shrutik-0 -- pg_dump -U shrutik voice_collection > shrutik-backup-$(date +%Y%m%d).sql

# Restore PostgreSQL
kubectl exec -i postgres-shrutik-0 -- psql -U shrutik voice_collection < shrutik-backup-20260211.sql
```

### Clean Up Old Data

```bash
# Clean up old exports
kubectl exec -it shrutik-backend-<pod-id> -- find /app/exports -type f -mtime +30 -delete

# Clean up old uploads (be careful!)
kubectl exec -it shrutik-backend-<pod-id> -- find /app/uploads -type f -mtime +90 -delete
```

## URLs

- **Frontend**: https://shrutik.nesohq.org
- **Backend API**: https://api.shrutik.nesohq.org
- **API Docs**: https://api.shrutik.nesohq.org/docs
- **Health Check**: https://api.shrutik.nesohq.org/health

## Security Notes

⚠️ **IMPORTANT**: Before production deployment:

1. Change `SECRET_KEY` in all deployments
2. Change database passwords
3. Use Kubernetes Secrets instead of plain text env vars
4. Enable HTTPS-only (already configured via Caddy)
5. Configure proper CORS origins
6. Set up monitoring and alerting
7. Configure backup automation

## Support

For issues:
1. Check pod logs: `kubectl logs <pod-name>`
2. Check events: `kubectl get events --sort-by='.lastTimestamp'`
3. Check Rancher UI: https://rancher.nesohq.org
4. Check Traefik dashboard: https://traefik.nesohq.org

---

**Last Updated**: 2026-02-11
**Kubernetes Version**: K3s v1.28+
**Deployment Pattern**: Kustomize + GitHub Actions
