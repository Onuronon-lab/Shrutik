# Troubleshooting

This guide covers common issues and their solutions when working with Shrutik.

## Docker Issues

### Services Won't Start

**Problem**: Docker services fail to start or crash immediately.

**Solutions**:

```bash
# Check logs for all services
docker compose logs -f

# Check logs for a specific service
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f redis

# Restart all services
docker compose restart

# Clean restart (removes containers, networks, and volumes)
docker compose down -v --remove-orphans
docker system prune -f  # optional: remove unused Docker resources
docker compose up -d    # start services again
```

### Port Already in Use

**Problem**: Error messages about ports 3000, 5432, 6379, or 8000 being in use.

**Solutions**:

```bash
# Find processes using ports
sudo lsof -i :8000
sudo lsof -i :3000
sudo lsof -i :5432
sudo lsof -i :6379

# Kill processes using specific ports
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:3000 | xargs kill -9

# Or use netstat
netstat -tulpn | grep :8000
```

### Database Connection Issues

**Problem**: Backend can't connect to PostgreSQL database.

**Solutions**:

```bash
# Check database status
docker-compose exec postgres pg_isready -U postgres

# Check database logs
docker compose logs -f postgres

# Reset database and remove containers, volumes, and networks
docker compose down -v --remove-orphans

# Optional: prune unused Docker resources
docker system prune -f

# Start all services
docker compose up -d

# Run database migrations inside the backend container
docker compose exec backend alembic upgrade head

# Or use a custom initialization script if you have one
docker compose exec backend python scripts/init-db.py

```

### Redis Connection Issues

**Problem**: Backend can't connect to Redis.

**Solutions**:

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker compose logs -f redis

# Restart Redis
docker compose restart redis
```

## Local Development Issues

### Virtual Environment Issues

**Problem**: Python packages not found or import errors.

**Solutions**:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Check Python path
which python
python --version
```

### Database Issues

**Problem**: PostgreSQL connection errors in local development.

**Solutions**:

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Create database if missing
createdb voice_collection

# Run migrations
alembic upgrade head
```

### Permission Errors

**Problem**: File permission errors, especially with uploads directory.

**Solutions**:

```bash
# Fix upload directory permissions
mkdir -p uploads
sudo chown -R $USER:$USER uploads/
chmod -R 755 uploads/

# Fix general project permissions
sudo chown -R $USER:$USER .
```

## Application Issues

### Admin User Creation Fails

**Problem**: Cannot create admin user or login fails.

**Solutions**:
```bash
# Ensure the database is migrated
# Local environment
alembic upgrade head  # see Local Database docs for details.

# Docker environment
docker compose exec backend alembic upgrade head  # see Docker Database docs for details

# Create admin user 
# Local
python scripts/create_admin.py --name "AdminUser" --email admin@example.com

# Docker
docker compose exec backend python scripts/create_admin.py --name "AdminUser" --email admin@example.com

# Check users in database
# Local
psql -U postgres -d voice_collection -c "SELECT * FROM users;"

# Docker
docker compose exec postgres psql -U postgres -d voice_collection -c "SELECT * FROM users;"

```

### File Upload Issues

**Problem**: Audio file uploads fail or return errors.

**Solutions**:

1. **Check file size**: Ensure files are under 100MB (default limit)
2. **Check file format**: Supported formats: `.wav`, `.mp3`, `.m4a`, `.flac`, `.webm`
3. **Check permissions**: Ensure uploads directory is writable
4. **Check disk space**: Ensure sufficient disk space available

```bash
# Check upload directory
ls -la uploads/
df -h  # Check disk space
```

### API Errors

**Problem**: API endpoints return 500 errors or unexpected responses.

**Solutions**:

```bash
# Check backend logs
docker compose logs -f backend

# Check API health
curl http://localhost:8000/health

# Check specific endpoint
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Frontend Issues

### Frontend Won't Load

**Problem**: Frontend shows blank page or connection errors.

**Solutions**:

```bash
# Check frontend logs
docker compose logs -f frontend

# Verify API connection
curl http://localhost:8000/health

# Check environment variables
cat frontend/.env
```

### Build Errors

**Problem**: Frontend build fails with dependency or compilation errors.

**Solutions**:

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Clear Next.js cache
rm -rf .next

# Rebuild
npm run build
```

## Debugging Tips

### Enable Debug Logging

Add to your `.env` file:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Check Service Health

```bash
# Backend health check (works for both local and Docker)
curl http://localhost:8000/health

# Database connection

# Local PostgreSQL
pg_isready -U postgres -d voice_collection

# Docker PostgreSQL
docker-compose exec postgres pg_isready -U postgres -d voice_collection

# Redis connection

# Local Redis
redis-cli ping

# Docker Redis
docker-compose exec redis redis-cli ping

```

### Monitor Resource Usage

```bash
# Docker resource usage
docker stats

# System resource usage
htop
df -h
free -h
```

## Getting Help

If you're still experiencing issues:

1. **Search existing issues**: Check [GitHub Issues](https://github.com/Onuronon-lab/Shrutik/issues)
2. **Create detailed issue**: Include:
   - Operating system and version
   - Docker/Docker Compose versions
   - Complete error messages
   - Steps to reproduce
   - Relevant log outputs
3. **Join community**: [Discord Server](https://discord.gg/9hZ9eW8ARk)
4. **Check documentation**: Review relevant sections in this documentation

