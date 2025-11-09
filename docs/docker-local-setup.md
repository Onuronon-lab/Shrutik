# Docker Local Setup Guide

This guide explains how to run Shrutik completely with Docker on your local machine, including all the configuration changes needed to switch from local development to Docker.

## Quick Docker Setup

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 1. Clone the repo

```bash
# Clone the repository
git clone https://github.com/Onuronon-lab/Shrutik.git
cd shrutik
```

### 2. Configure Environment for Docker

Copy the Docker-specific environment file:

```bash
# Use Docker-specific configuration
cp .env.docker .env
```

**Available Environment Files:**
- `.env.example` - Template with all available options
- `.env.development` - Local development (localhost)
- `.env.docker` - Docker development (service names)

Or manually edit the `.env` file with Docker-specific settings:

```env
# Application
APP_NAME=Voice Data Collection Platform
DEBUG=true
VERSION=1.0.0

# Database (Docker service names)
DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection

# Redis (Docker service name)
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# CORS (for local development)
ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:8000"]

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=104857600

# Performance
ENABLE_CACHING=true
ENABLE_RATE_LIMITING=true
USE_CELERY=true

# Development settings
LOG_LEVEL=DEBUG
```

### 3. Frontend Configuration

```bash
cp .env.example .env
```

### 4. Start All Services

```bash
# Make the script executable
chmod +x docker-dev.sh

# Start all services (recommended)
./docker-dev.sh start

# Or use docker-compose directly
docker-compose up -d
```

### 5. Initialize Database

```bash
# Run database migrations
./docker-dev.sh migrate

# Create admin user
DATABASE_URL="postgresql://postgres:password@localhost:5432/voice_collection" python scripts/create_admin.py --name "Admin" --email admin@example.com
```

Follow the prompts to create your first admin user.

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Configuration Changes Explained

### Key Differences: Local vs Docker

| Component | Local Development | Docker |
|-----------|------------------|---------|
| **Database URL** | `localhost:5432` | `postgres:5432` |
| **Redis URL** | `localhost:6379` | `redis:6379` |
| **Frontend API URL** | `http://localhost:8000` | `http://localhost:8000` |
| **File Paths** | `./uploads` | `/app/uploads` |

### Files to Modify for Docker

#### 1. Environment Variables (`.env`)

**Local Development:**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection
REDIS_URL=redis://localhost:6379/0
```

**Docker:**
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection
REDIS_URL=redis://redis:6379/0
```

*Note: This stays the same because we're accessing from the host machine*

#### 3. Database Configuration (Automatic)

The `app/core/config.py` automatically reads from environment variables, so no changes needed.

#### 4. Alembic Configuration (Automatic)

Alembic migrations automatically use the correct database URL from environment variables:
- **Local Development**: Uses `localhost:5432`
- **Docker**: Uses `postgres:5432` (Docker service name)

The `alembic/env.py` file is configured to read from `settings.DATABASE_URL`, so no manual changes needed when switching between local and Docker environments.

## Docker Compose Services

### Service Overview

```yaml
services:
  postgres:          # PostgreSQL database
  redis:       # Redis cache and queue
  backend:     # FastAPI application
  worker:      # Celery background worker
  frontend:    # Next.js frontend
```

### Service Details

#### Database (PostgreSQL)
- **Container Name**: `voice_collection_postgres`
- **Port**: 5432 (internal)
- **Data**: Persisted in Docker volume

#### Redis
- **Container Name**: `voice_collection_redis`
- **Port**: 6379 (internal)
- **Usage**: Cache and Celery queue

#### Backend (FastAPI)
- **Container Name**: `voice_collection_backend`
- **Port**: 8000 (exposed to host)
- **Features**: API server with hot reload

#### Worker (Celery)
- **Container Name**: `voice_collection_flower, voice_collection_celery_beat, voice_collection_celery`
- **Purpose**: Background job processing

#### Frontend (Next.js)
- **Container Name**: `voice_collection_frontend`
- **Port**: 3000 (exposed to host)
- **Features**: React app with hot reload

## Development Workflow

### Starting Development

```bash
# Start all services
docker-compose up -d

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
```

### Making Code Changes

#### Backend Changes
- Code changes are automatically reflected (hot reload enabled)
- No need to restart containers

#### Frontend Changes
- Code changes are automatically reflected (Next.js hot reload)
- No need to restart containers

#### Database Changes
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"
```

### Useful Commands

#### Using docker-dev.sh (Recommended)

```bash
# Stop all services
./docker-dev.sh stop

# Restart services
./docker-dev.sh restart

# View logs for all services
./docker-dev.sh logs

# View logs for specific service
./docker-dev.sh logs backend

# Check service status
./docker-dev.sh status

# Clean up everything
./docker-dev.sh cleanup

# Run database migrations
./docker-dev.sh migrate

# Create admin user
./docker-dev.sh admin

# Show help
./docker-dev.sh help
```

#### Direct Docker Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Rebuild services after dependency changes
docker-compose build --no-cache

# Access backend container shell
docker-compose exec backend bash

# Access database
docker-compose exec db psql -U postgres -d shrutik
```

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check logs
docker-compose logs

# Check if ports are in use
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# Kill processes using ports
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:3000 | xargs kill -9
```

#### 2. Database Connection Issues

```bash
# Check database status
docker-compose exec db pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up -d db
docker-compose exec backend alembic upgrade head
```

#### 3. Redis Connection Issues

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

#### 4. File Permission Issues

```bash
# Fix upload directory permissions
sudo chown -R $USER:$USER uploads/
chmod -R 755 uploads/
```

#### 5. Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase memory limits (edit docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

## Switching Between Local and Docker

### From Local to Docker

1. **Stop local services**:
   ```bash
   # Stop local PostgreSQL and Redis
   sudo systemctl stop postgresql
   sudo systemctl stop redis
   
   # Or kill processes
   pkill -f uvicorn
   pkill -f celery
   ```

2. **Update configuration**:
   ```bash
   # Use Docker configuration
   cp .env.docker .env
   ```

3. **Start Docker**:
   ```bash
   ./docker-dev.sh start
   ```

### From Docker to Local

1. **Stop Docker services**:
   ```bash
   ./docker-dev.sh stop
   ```

2. **Update configuration**:
   ```bash
   # Use local development configuration
   cp .env.development .env
   ```

3. **Start local services**:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl start redis
   ./scripts/start-dev.sh
   ```

## Monitoring Docker Services

### Health Checks

```bash
# Check all services health
docker-compose ps

# Detailed service info
docker-compose exec backend curl http://localhost:8000/health

# Check database
docker-compose exec db pg_isready -U postgres

# Check Redis
docker-compose exec redis redis-cli ping
```

### Logs and Debugging

```bash
# View logs for all services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs worker

# View last 50 lines
docker-compose logs --tail=50 backend
```

## Production-Like Local Setup

For testing production configurations locally:

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With environment variables
cp .env.example .env.production
# Edit .env.production with production-like settings
docker-compose --env-file .env.production up -d
```

## Next Steps

After getting Docker setup working:

1. **[Contributing Guide](contributing.md)** - Start contributing to Shrutik
2. **[API Reference](api-reference.md)** - Explore the API endpoints
3. **[Architecture Overview](architecture.md)** - Understand the system design
4. **[Local Development Guide](local-development.md)** - Native development setup

## Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. View logs: `docker-compose logs`
3. Join our [Discord community](https://discord.gg/9hZ9eW8ARk)
4. Create an issue on [GitHub](https://github.com/Onuronon-lab/Shrutik/issues)

---

**Happy coding with Docker! 🐳✨**