# Troubleshooting

This guide covers common issues and their solutions when working with Shrutik.

## 🐳 Docker Issues

### Services Won't Start

**Problem**: Docker services fail to start or crash immediately.

**Solutions**:

```bash
# Check logs for all services
./docker-dev.sh logs

# Check specific service logs
./docker-dev.sh logs backend
./docker-dev.sh logs postgres
./docker-dev.sh logs redis

# Restart services
./docker-dev.sh restart

# Clean restart (removes volumes)
./docker-dev.sh cleanup
./docker-dev.sh start
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
./docker-dev.sh logs postgres

# Reset database
./docker-dev.sh cleanup
./docker-dev.sh start
./docker-dev.sh migrate
```

### Redis Connection Issues

**Problem**: Backend can't connect to Redis.

**Solutions**:

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
./docker-dev.sh logs redis

# Restart Redis
docker-compose restart redis
```

## 🖥️ Local Development Issues

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

## 🔧 Application Issues

### Admin User Creation Fails

**Problem**: Cannot create admin user or login fails.

**Solutions**:

```bash
# Ensure database is migrated
alembic upgrade head

# Create admin user interactively
python create_admin.py

# Check user in database
docker-compose exec postgres psql -U postgres -d voice_collection -c "SELECT * FROM users;"
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
./docker-dev.sh logs backend

# Check API health
curl http://localhost:8000/health

# Check specific endpoint
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🌐 Frontend Issues

### Frontend Won't Load

**Problem**: Frontend shows blank page or connection errors.

**Solutions**:

```bash
# Check frontend logs
./docker-dev.sh logs frontend

# Verify API connection
curl http://localhost:8000/health

# Check environment variables
cat frontend/.env.local
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

## 🔍 Debugging Tips

### Enable Debug Logging

Add to your `.env` file:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Check Service Health

```bash
# Backend health check
curl http://localhost:8000/health

# Database connection
docker-compose exec postgres pg_isready -U postgres

# Redis connection
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

## 🆘 Getting Help

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

### Issue Template

When reporting issues, please include:

```
**Environment:**
- OS: [e.g., Ubuntu 22.04, macOS 13.0, Windows 11]
- Docker version: [run `docker --version`]
- Docker Compose version: [run `docker-compose --version`]

**Problem Description:**
[Clear description of the issue]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [And so on...]

**Expected Behavior:**
[What you expected to happen]

**Actual Behavior:**
[What actually happened]

**Error Messages:**
```
[Paste complete error messages here]
```

**Logs:**
```
[Paste relevant log outputs here]
```
```

This helps us diagnose and fix issues quickly!