# Local Development Guide

This guide covers setting up Shrutik for local development, including all the tools and configurations needed for contributing to the project.

## 🛠️ Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **PostgreSQL**: 13 or higher
- **Redis**: 6 or higher
- **Git**: Latest version

### Development Tools (Recommended)

- **IDE**: VS Code with Python and TypeScript extensions
- **API Testing**: Postman or Insomnia
- **Database GUI**: pgAdmin or DBeaver
- **Redis GUI**: RedisInsight

## 🚀 Setup Instructions

### 1. Clone and Navigate

```bash
git clone https://github.com/Onuronon-lab/Shrutik.git
cd shrutik
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### Database Setup

```bash
# Start PostgreSQL (if not running)
sudo systemctl start postgresql  # Linux
brew services start postgresql   # Mac

# Create database
createdb shrutik_dev

# Set environment variables
cp .env.example .env.development
```

Edit `.env.development`:

```env
# Development Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/shrutik_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Development Settings
DEBUG=true
USE_CELERY=true

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE=104857600

# Security (use a secure key in production)
SECRET_KEY=dev-secret-key-change-in-production
```

#### Run Database Migrations

```bash
# Run database migrations
alembic upgrade head

# Create admin user
python create_admin.py
```

Follow the prompts to create your first admin user.

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
```

Edit `frontend/.env.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Development Settings
NODE_ENV=development
```

### 4. Start Development Services

#### Option A: Using Scripts (Recommended)

```bash
# Start all services
./scripts/start-dev.sh
```

This script will start:
- PostgreSQL and Redis (if not running)
- Backend API server
- Celery worker
- Frontend development server

#### Option B: Manual Start

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🔧 Development Configuration

### Alembic Configuration

Alembic is configured to automatically use the correct database URL from your environment variables:

- The `alembic/env.py` file reads from `settings.DATABASE_URL`
- No manual configuration changes needed when switching environments
- Migrations work seamlessly in both local and Docker environments

### Switching Between Local and Docker

When switching between local development and Docker, you need to update these configurations:

#### 1. Environment Variables (`.env` file)

**Local Development:**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/shrutik_dev
REDIS_URL=redis://localhost:6379/0
```

**Docker:**
```env
DATABASE_URL=postgresql://postgres:password@db:5432/shrutik
REDIS_URL=redis://redis:6379/0
```

#### 2. Frontend Configuration (`frontend/.env.local`)

**Local Development:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Docker:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
*Note: This stays the same for local Docker since we access from host*

#### 3. Quick Switch Commands

**Switch to Docker:**
```bash
# Stop local services
pkill -f uvicorn
pkill -f celery

# Update config for Docker
sed -i 's/localhost/db/g' .env
sed -i 's/localhost/redis/g' .env

# Start Docker using development script
chmod +x docker-dev.sh
./docker-dev.sh start
```

**Switch to Local:**
```bash
# Stop Docker
docker-compose down

# Update config for local
sed -i 's/@db:/@localhost:/g' .env
sed -i 's/redis:6379/localhost:6379/g' .env

# Start local services
./scripts/start-dev.sh
```

> **📋 Complete Docker Guide**: For detailed Docker setup instructions, troubleshooting, and configuration explanations, see our [Docker Local Setup Guide](docker-local-setup.md).

### Environment Files Summary

| File | Purpose | When to Use |
|------|---------|-------------|
| `.env.example` | Template with all variables | Copy to create other env files |
| `.env` | Production configuration | Docker production deployment |
| `.env.development` | Local development | Local Python development |
| `frontend/.env.local` | Frontend development | Local frontend development |

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## 🔍 Debugging

### Backend Debugging

#### VS Code Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/uvicorn",
            "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env.development"
        }
    ]
}
```

#### Logging Configuration

Enable debug logging in `.env.development`:

```env
LOG_LEVEL=DEBUG
```

### Frontend Debugging

#### Browser DevTools

- Use React Developer Tools extension
- Enable source maps for debugging TypeScript
- Use Network tab to debug API calls

#### VS Code Configuration

Install recommended extensions:
- ES7+ React/Redux/React-Native snippets
- TypeScript Importer
- Prettier - Code formatter
- ESLint

## 📊 Database Management

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration status
alembic current
```

### Database Reset

```bash
# Drop and recreate database
dropdb shrutik_dev
createdb shrutik_dev
alembic upgrade head
python create_admin.py
```

### Sample Data

```bash
# Load sample data for development
python scripts/load_sample_data.py
```

## 🔧 Common Development Tasks

### Adding New API Endpoints

1. Create schema in `app/schemas/`
2. Add model in `app/models/` (if needed)
3. Implement service in `app/services/`
4. Create router in `app/api/`
5. Register router in `app/main.py`
6. Add tests in `tests/`

### Adding New Frontend Components

1. Create component in `frontend/src/components/`
2. Add TypeScript types in `frontend/src/types/`
3. Implement API calls in `frontend/src/services/`
4. Add routing in `frontend/src/pages/`
5. Add tests in `frontend/src/__tests__/`

### Database Schema Changes

1. Modify models in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and edit migration file if needed
4. Apply migration: `alembic upgrade head`
5. Update tests and documentation

## 🚀 Performance Optimization

### Development Performance

```bash
# Use faster database for development
export DATABASE_URL="sqlite:///./dev.db"

# Disable Celery for faster startup
export USE_CELERY=false

# Use development Redis
export REDIS_URL="redis://localhost:6379/1"
```

### Hot Reload Configuration

Backend hot reload is enabled by default with `--reload` flag.

Frontend hot reload configuration in `frontend/next.config.js`:

```javascript
module.exports = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    esmExternals: false
  }
}
```

## 📚 Additional Resources

- **[API Documentation](api-reference.md)** - Complete API reference
- **[Architecture Overview](architecture.md)** - System design details
- **[Contributing Guide](contributing.md)** - Contribution guidelines
- **[Docker Local Setup](docker-local-setup.md)** - Docker development environment

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Database connection issues:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

**Redis connection issues:**
```bash
# Check Redis status
redis-cli ping

# Start Redis
redis-server
```

**Permission errors:**
```bash
# Fix upload directory permissions
mkdir -p uploads
chmod 755 uploads
```

### Getting Help

If you encounter issues:

1. Check the [troubleshooting section](getting-started.md#troubleshooting)
2. Search existing [GitHub issues](https://github.com/Onuronon-lab/Shrutik/issues)
3. Join our [Discord community](https://discord.gg/9hZ9eW8ARk)
4. Create a new issue with detailed information

Happy coding! 🎉