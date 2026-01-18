# Docker Build & Deployment Guide

This guide covers building Docker images locally and deploying them to your EC2 instance using Docker Hub.

## Option 1: Manual Build & Push (Immediate Solution)

### Step 1: Create Docker Hub Account

1. Go to [https://hub.docker.com](https://hub.docker.com)
2. Click "Sign Up" 
3. Choose a username (you'll use this in image names)
4. Verify your email
5. **Important**: Go to Account Settings → Security → Access Tokens
6. Create a new access token (save it - you'll need it for login)

### Step 2: Verify Docker Installation

Since you're on Arch, you likely already have Docker installed. Just verify:

```bash
# Check Docker is running
docker --version
docker-compose --version

# Start Docker service if needed
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (if not already done)
sudo usermod -aG docker $USER
# Then logout and login again for group changes to take effect
```

### Step 3: Login to Docker Hub from Terminal

```bash
# Login using your username and access token (not password)
docker login
# Enter username: your-dockerhub-username
# Enter password: your-access-token
```

### Step 4: Build Multi-Stage Docker Image

Your Dockerfile.prod is already optimized with multi-stage builds! Now build it:

```bash
# On your local machine, in your project directory
# Replace 'your-dockerhub-username' with your actual username
docker build -f Dockerfile.prod -t your-dockerhub-username/shrutik:latest .

# Example: if your username is "johnsmith"
# docker build -f Dockerfile.prod -t johnsmith/shrutik:latest .

# Or use the provided script (easier):
./scripts/build-and-push.sh your-dockerhub-username latest
```

### Step 5: Push to Docker Hub

```bash
# Push the image
docker push your-dockerhub-username/shrutik:latest

# This will upload your image to Docker Hub
# You can see it at: https://hub.docker.com/r/your-dockerhub-username/shrutik
```

### Step 6: Update docker-compose.prod.yml

I've created a new file `docker-compose.prod.hub.yml` that uses pre-built images. Update it with your Docker Hub username:

```bash
# Edit the docker-compose.prod.hub.yml file
# Replace 'your-dockerhub-username' with your actual username in the image lines:
# image: ${DOCKER_IMAGE:-your-dockerhub-username/shrutik:latest}

# Or set it as an environment variable
export DOCKER_IMAGE=your-dockerhub-username/shrutik:latest
```

### Step 7: Deploy on EC2

**If you're using HashiCorp Vault for secrets (recommended):**

```bash
# On your EC2 instance
cd /opt/shrutik

# First time: Add your R2 credentials to Vault
./scripts/vault-add-r2.sh

# Deploy with Vault + Docker Hub
./scripts/deploy-with-vault-hub.sh ifrunruhiin12 latest
```

**Note:** The `vault-add-r2.sh` script will prompt you for:
- R2 Account ID
- R2 Access Key ID  
- R2 Secret Access Key
- R2 Bucket Name

These credentials will be stored securely in Vault and used by your application for cloud storage.

**If you're NOT using Vault:**

```bash
# On your EC2 instance
cd /opt/shrutik

# Method 1: Use the deployment script (recommended)
./scripts/deploy-from-hub.sh your-dockerhub-username latest

# Method 2: Manual deployment
# Pull the latest image
docker pull your-dockerhub-username/shrutik:latest

# Stop current containers (if running)
docker-compose -f docker-compose.prod.yml down

# Start with the new image using the hub compose file
DOCKER_IMAGE=your-dockerhub-username/shrutik:latest docker-compose -f docker-compose.prod.hub.yml up -d

# Check status
docker-compose -f docker-compose.prod.hub.yml ps
```

---

## Option 2: GitHub Actions (Automated CI/CD)

### Step 1: Set up Docker Hub (same as Option 1, Steps 1-3)

### Step 2: Add Docker Hub Secrets to GitHub

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add these repository secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub access token

### Step 3: Create GitHub Actions Workflow

Create `.github/workflows/build-and-deploy.yml`:

```yaml
name: Build and Deploy Docker Image

on:
  push:
    branches: [ main, production ]
  pull_request:
    branches: [ main ]

env:
  DOCKER_IMAGE: ${{ secrets.DOCKER_USERNAME }}/shrutik

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.DOCKER_IMAGE }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./Dockerfile.prod
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/production'
    
    steps:
    - name: Deploy to EC2
      run: |
        echo "Add your EC2 deployment script here"
        echo "This could use SSH to connect to EC2 and pull the new image"
```

### Step 4: Set up EC2 Auto-Deploy (Optional)

Create a webhook endpoint on your EC2 or use SSH deployment:

```bash
# Option A: Simple script on EC2 that you can trigger
# Create /opt/shrutik/deploy.sh
#!/bin/bash
cd /opt/shrutik
docker pull your-dockerhub-username/shrutik:latest
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## Multi-Stage Dockerfile (Your Current Setup)

Your `Dockerfile.prod` is already optimized with multi-stage builds:

```dockerfile
# Production Dockerfile for Shrutik Backend
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Create requirements-prod.txt without development dependencies
RUN grep -v -E "(pytest|httpx)" requirements.txt > requirements-prod.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip config set global.timeout 1000 && \
    pip config set global.retries 5 && \
    pip install --no-cache-dir --default-timeout=1000 \
        numpy>=1.24.0 scipy>=1.11.0 && \
    pip install --no-cache-dir --default-timeout=1000 \
        librosa>=0.10.0 && \
    pip install --no-cache-dir --default-timeout=1000 \
        -r requirements-prod.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r shrutik && useradd -r -g shrutik shrutik

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=shrutik:shrutik . .

# Create necessary directories with proper permissions
RUN mkdir -p uploads exports logs && \
    chown -R shrutik:shrutik uploads exports logs

# Remove development files and test directories
RUN rm -rf tests/ .pytest_cache/ __pycache__/ \
    && find . -name "*.pyc" -delete \
    && find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Switch to non-root user
USER shrutik

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Benefits of This Approach

1. **Smaller final image**: Multi-stage builds exclude build tools from final image
2. **Faster deployments**: Only pull image, don't build on EC2
3. **Consistent builds**: Same image across all environments
4. **No EC2 disk space issues**: Building happens elsewhere
5. **Version control**: Tagged images for rollbacks

## Quick Commands Reference

```bash
# Build and push manually (local machine)
docker build -f Dockerfile.prod -t ifrunruhiin12/shrutik:latest .
docker push ifrunruhiin12/shrutik:latest

# Or use the script (easier)
./scripts/build-and-push.sh ifrunruhiin12 latest

# Deploy on EC2 with Vault
./scripts/vault-add-r2.sh  # First time only
./scripts/deploy-with-vault-hub.sh ifrunruhiin12 latest

# Check logs
DOCKER_IMAGE=ifrunruhiin12/shrutik:latest docker-compose -f docker-compose.prod.hub.yml logs -f

# Rollback (if needed)
docker pull ifrunruhiin12/shrutik:previous-tag
DOCKER_IMAGE=ifrunruhiin12/shrutik:previous-tag docker-compose -f docker-compose.prod.hub.yml up -d
```

Choose Option 1 for immediate deployment, then set up Option 2 for automated future deployments.