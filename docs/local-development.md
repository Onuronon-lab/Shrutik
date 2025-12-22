# Local Development Guide

This guide covers setting up Shrutik for local development, including all the tools and configurations needed for contributing to the project.

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Node.js**: 20 or higher
- **PostgreSQL**: 15 or higher
- **Redis**: 7 or higher
- **Git**: Latest version

### Development Tools (Recommended)

- **IDE**: VS Code with Python and TypeScript extensions
- **API Testing**: Postman or Insomnia
- **Database GUI**: pgAdmin or DBeaver
- **Redis GUI**: RedisInsight

## Setup Instructions

### 1. Clone and Navigate

```bash
git clone https://github.com/Onuronon-lab/Shrutik.git
cd shrutik

# Switch to the deployment-dev branch
git fetch origin
git switch deployment-dev
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
```

#### Database Setup

```bash
# Start PostgreSQL (if not running)
sudo systemctl start postgresql  # Linux
brew services start postgresql   # Mac

# Create database
createdb voice_collection

# Set environment variables
cp .env.example .env
```

Edit `.env.example`:

```env
# Development Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection

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
python scripts/create_admin.py --name "AdminUser" --email admin@example.com
```

Follow the prompts to create your first admin user.

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
```

### 4. Start Development Services


#### Start Services

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
source venv/bin/activate
celery -A  app.core.celery_app  worker  --loglevel=info
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm start
```

## Development Configuration

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
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection
REDIS_URL=redis://localhost:6379/0
```

**Docker:**
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/voice_collection
REDIS_URL=redis://redis:6379/0
```

*Note: This stays the same for local Docker since we access from host*

#### 3. Quick Switch Commands

**Switch to Docker:**
```bash
# Stop local services
pkill -f uvicorn
pkill -f celery

# Update config for Docker
cp .env.example .env

# Start Services 
docker compose up -d
```

**Switch to Local:**
```bash
# Stop Docker
docker-compose down

Follow The Previous Instructions for locally starting service
```

> **Complete Docker Guide**: For detailed Docker setup instructions, troubleshooting, and configuration explanations, see our [Docker Local Setup Guide](docker-local-setup.md).

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

## Debugging

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

## Database Management

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
dropdb voice_collection
createdb voice_collection
alembic upgrade head
python create_admin.py
```

## Common Development Tasks

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

## Performance Optimization

### Development Performance

```bash
# Use faster database for development
export DATABASE_URL="postgresql://postgres:password@localhost:5432/voice_collection"

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

## Additional Resources

- **[API Documentation](api-reference.md)** - Complete API reference
- **[Architecture Overview](architecture.md)** - System design details
- **[Contributing Guide](contributing.md)** - Contribution guidelines
- **[Docker Local Setup](docker-local-setup.md)** - Docker development environment



Happy coding! 🎉
