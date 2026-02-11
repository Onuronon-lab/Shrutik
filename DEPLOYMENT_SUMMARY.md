# Shrutik Deployment - Summary

## ✅ What Was Created

### 1. GitHub Actions Workflow (Shrutik Repo)
**File**: `.github/workflows/build-and-push.yml`

Automatically builds and pushes Docker images to GitHub Container Registry when you push to `main` or `prod` branches.

**Images Created**:
- `ghcr.io/onuronon-lab/shrutik-backend:latest`
- `ghcr.io/onuronon-lab/shrutik-frontend:latest`

### 2. Kubernetes Manifests (nesohq-infra Repo)

Created following the existing NesoHQ infrastructure pattern:

#### Databases (StatefulSets)
```
nesohq-infra/infra/base/databases/
├── postgres-shrutik/
│   ├── statefulset.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── redis-shrutik/
    ├── statefulset.yaml
    ├── service.yaml
    └── kustomization.yaml
```

#### Applications (Deployments)
```
nesohq-infra/infra/base/apps/
├── shrutik-backend/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── migration-job.yaml
│   └── kustomization.yaml
├── shrutik-frontend/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
├── shrutik-celery-worker/
│   ├── deployment.yaml
│   └── kustomization.yaml
└── shrutik-celery-beat/
    ├── deployment.yaml
    └── kustomization.yaml
```

## 📋 Deployment Checklist

### Step 1: Push Images (Automatic)
```bash
cd ~/Shrutik
git add .
git commit -m "Add Kubernetes deployment"
git push origin main
```
✅ GitHub Actions will build and push images automatically

### Step 2: Deploy to Kubernetes
```bash
cd ~/nesohq-infra

# Add and commit the new manifests
git add infra/base/apps/shrutik-*
git add infra/base/databases/*-shrutik
git add infra/base/kustomization.yaml
git add infra/overlays/prod/kustomization.yaml
git commit -m "Add Shrutik application deployment"
git push origin main

# Deploy to staging (automatic)
# Or manually:
kubectl apply -k infra/overlays/staging/
```

### Step 3: Configure DNS
Add these DNS records pointing to `91.98.134.15`:
- `shrutik.nesohq.org`
- `api.shrutik.nesohq.org`

### Step 4: Update Caddy
On the VPS, add to `~/nesohq-infra/Caddyfile`:
```caddyfile
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

### Step 5: Verify Deployment
```bash
# Check pods
kubectl get pods | grep shrutik

# Check services
kubectl get svc | grep shrutik

# Check ingress
kubectl get ingress | grep shrutik

# Test health
curl https://api.shrutik.nesohq.org/health
curl https://shrutik.nesohq.org/
```

## 🎯 Architecture Summary

### Images (2)
1. **Backend Image** - Used for:
   - Backend API (3 replicas)
   - Celery Worker (3 replicas)
   - Celery Beat (1 replica)
   - Migration Job

2. **Frontend Image** - Used for:
   - Frontend (3 replicas)

### Kubernetes Resources
| Type | Count | Names |
|------|-------|-------|
| **StatefulSets** | 2 | postgres-shrutik, redis-shrutik |
| **Deployments** | 4 | shrutik-backend, shrutik-frontend, shrutik-celery-worker, shrutik-celery-beat |
| **Services** | 3 | shrutik-backend-service, shrutik-frontend-service, postgres-shrutik, redis-shrutik |
| **Ingress** | 2 | shrutik-backend-ingress, shrutik-frontend-ingress |
| **Jobs** | 1 | shrutik-migrations (runs on deployment) |

### Node Distribution
- **postgres-shrutik**: ip-172-31-38-6 (with other databases)
- **redis-shrutik**: ip-172-31-18-79 (with redis-archive)
- **Applications**: Distributed across all worker nodes

### Storage
- **PostgreSQL**: `/data/postgres-shrutik` (hostPath)
- **Redis**: `/data/redis-shrutik` (hostPath)
- **Uploads**: `/data/shrutik/uploads` (shared across pods)
- **Exports**: `/data/shrutik/exports` (shared across pods)

## 🔄 CI/CD Flow

```
Developer pushes to main
    ↓
GitHub Actions builds images
    ↓
Images pushed to ghcr.io
    ↓
nesohq-infra updated
    ↓
Kubernetes applies manifests
    ↓
Pods rolled out
    ↓
Application live! 🎉
```

## 🚀 Quick Commands

### Deploy
```bash
kubectl apply -k nesohq-infra/infra/overlays/prod/
```

### Check Status
```bash
kubectl get pods -l app=shrutik-backend
kubectl get pods -l app=shrutik-frontend
kubectl get pods -l app=shrutik-celery-worker
```

### View Logs
```bash
kubectl logs -f deployment/shrutik-backend
kubectl logs -f deployment/shrutik-celery-worker
```

### Scale
```bash
kubectl scale deployment shrutik-backend --replicas=5
kubectl scale deployment shrutik-celery-worker --replicas=5
```

### Restart
```bash
kubectl rollout restart deployment/shrutik-backend
kubectl rollout restart deployment/shrutik-frontend
kubectl rollout restart deployment/shrutik-celery-worker
```

## 📚 Documentation

- **Full Deployment Guide**: `KUBERNETES_DEPLOYMENT.md`
- **NesoHQ Infrastructure**: `nesohq-infra/README.md`
- **Setup Guide**: `nesohq-infra/docs/setup-guide.md`
- **Operations Guide**: `nesohq-infra/docs/operations-guide.md`

## ⚠️ Important Notes

1. **Celery Beat** must have exactly 1 replica (scheduler)
2. **Shared storage** is required for uploads/exports across pods
3. **Database passwords** should be changed before production
4. **SECRET_KEY** must be changed in production
5. **DNS propagation** may take a few minutes
6. **Migration job** runs automatically on first deployment

## 🎉 Success Criteria

✅ Images built and pushed to ghcr.io
✅ All pods running and healthy
✅ Databases initialized
✅ Migrations completed
✅ Frontend accessible at https://shrutik.nesohq.org
✅ Backend API accessible at https://api.shrutik.nesohq.org
✅ Celery workers processing tasks
✅ SSL certificates issued by Caddy

---

**Ready to deploy!** Follow the checklist above to get Shrutik running on your Kubernetes cluster.
