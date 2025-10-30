# Voice Data Collection Platform - Docker Setup

This guide helps you run the entire Voice Data Collection Platform using Docker Compose with a single command.

## 🚀 Quick Start

```bash
# Start all services
./docker-dev.sh start

# Or simply
./docker-dev.sh
```

That's it! All services will be running:
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000  
- 📚 **API Documentation**: http://localhost:8000/docs
- 🗄️ **PostgreSQL**: localhost:5432
- 🔴 **Redis**: localhost:6379

## 📋 Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM available for containers
- Ports 3000, 8000, 5432, 6379 available

## 🛠️ Available Commands

```bash
./docker-dev.sh start       # Start all services
./docker-dev.sh stop        # Stop all services  
./docker-dev.sh restart     # Restart all services
./docker-dev.sh logs        # Show all logs
./docker-dev.sh logs backend # Show specific service logs
./docker-dev.sh status      # Show service status
./docker-dev.sh cleanup     # Clean up Docker resources
./docker-dev.sh migrate     # Run database migrations
./docker-dev.sh admin       # Create admin user
./docker-dev.sh help        # Show help
```

## 🏗️ Architecture

The Docker Compose setup includes:

### Core Services
- **postgres**: PostgreSQL database for data storage
- **redis**: Redis for Celery task queue and caching
- **backend**: FastAPI application server
- **celery**: Background worker for audio processing
- **frontend**: React development server

### Service Dependencies
```
frontend → backend → postgres, redis
celery → backend → postgres, redis
```

## 🔧 Development Workflow

### 1. Initial Setup
```bash
# Start services
./docker-dev.sh start

# Run migrations (first time only)
./docker-dev.sh migrate

# Create admin user (first time only)  
./docker-dev.sh admin
```

### 2. Daily Development
```bash
# Start development
./docker-dev.sh start

# View logs while developing
./docker-dev.sh logs

# Stop when done
./docker-dev.sh stop
```

### 3. Debugging
```bash
# Check service status
./docker-dev.sh status

# View specific service logs
./docker-dev.sh logs backend
./docker-dev.sh logs celery
./docker-dev.sh logs frontend

# Restart problematic service
docker-compose restart backend
```

## 📁 Volume Mounts

The setup includes volume mounts for hot reloading:

- **Backend**: `./app` → `/app/app` (Python code changes)
- **Frontend**: `./frontend/src` → `/app/src` (React code changes)
- **Uploads**: `./uploads` → `/app/uploads` (Persistent file storage)
- **Environment**: `./.env` → `/app/.env` (Configuration)

## 🔍 Monitoring

### Health Checks
All services include health checks:
- **postgres**: `pg_isready`
- **redis**: `redis-cli ping`  
- **backend**: HTTP request to `/`

### Logs
```bash
# All services
./docker-dev.sh logs

# Specific service
./docker-dev.sh logs [service_name]

# Follow logs in real-time
docker-compose logs -f backend
```

## 🐛 Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8000

# Stop conflicting services
./docker-dev.sh stop
```

**Database connection issues:**
```bash
# Check postgres health
docker-compose ps postgres

# View postgres logs
./docker-dev.sh logs postgres

# Restart database
docker-compose restart postgres
```

**Celery not processing:**
```bash
# Check celery worker
./docker-dev.sh logs celery

# Restart celery
docker-compose restart celery
```

**Frontend not loading:**
```bash
# Check frontend logs
./docker-dev.sh logs frontend

# Rebuild frontend
docker-compose up --build frontend
```

### Clean Slate Reset
```bash
# Stop everything and clean up
./docker-dev.sh cleanup

# Start fresh
./docker-dev.sh start
./docker-dev.sh migrate
./docker-dev.sh admin
```

## 🔧 Configuration

### Environment Variables
Edit `.env` file for configuration:
```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection

# Redis  
REDIS_URL=redis://redis:6379/0

# Audio formats
ALLOWED_AUDIO_FORMATS=[".wav", ".mp3", ".m4a", ".flac", ".webm"]
```

### Docker Compose Override
Create `docker-compose.override.yml` for local customizations:
```yaml
version: '3.8'
services:
  backend:
    ports:
      - "8001:8000"  # Use different port
```

## 📊 Performance

### Resource Usage
- **Total RAM**: ~2-3GB
- **CPU**: Moderate during audio processing
- **Disk**: Grows with uploaded recordings

### Scaling
```bash
# Scale celery workers
docker-compose up --scale celery=3

# Monitor resource usage
docker stats
```

## 🔒 Security Notes

- Default passwords are for development only
- Change credentials in production
- Database and Redis are exposed on localhost only
- File uploads are stored in `./uploads` directory

## 📝 Next Steps

1. **Start developing**: Services are ready for development
2. **Upload recordings**: Use the frontend at http://localhost:3000
3. **Process audio**: Celery automatically processes uploads
4. **Transcribe**: Use the transcription interface
5. **Monitor**: Check logs and service status regularly

## 🆘 Getting Help

If you encounter issues:
1. Check service status: `./docker-dev.sh status`
2. View logs: `./docker-dev.sh logs [service]`
3. Try cleanup and restart: `./docker-dev.sh cleanup && ./docker-dev.sh start`
4. Check Docker Desktop for resource issues