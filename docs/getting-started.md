# Getting Started with Shrutik

Welcome to Shrutik! This guide will help you set up and start using the platform in just a few minutes.

## Overview

Shrutik is a voice data collection platform that allows communities to contribute voice recordings and transcriptions in their native languages. You can either contribute data or set up your own instance of the platform.

## Quick Setup Options

### Option 1: Docker (Recommended)

The fastest way to get Shrutik running is with Docker:

```bash
# Clone the repository
git clone https://github.com/Onuronon-lab/Shrutik.git
cd shrutik

# Copy Docker environment configuration
cp .env.docker .env

# Build images and start all services
docker compose up --build -d
```

**Access the platform:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

> **Note:** For detailed Docker setup instructions, see our comprehensive [Docker Local Setup Guide](docker-local-setup.md) for configuration details, troubleshooting, and switching between local/Docker environments.

### Option 2: Local Development

For development or customization:

```bash
# Clone and setup
git clone https://github.com/Onuronon-lab/Shrutik.git
cd shrutik

# Switch to the deployment-dev branch
git fetch origin
git switch deployment-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
To start backend, frontend, and Celery worker, see the [Local Setup Guide](local-development.md#start-services).

## Initial Configuration

### 1. Environment Variables

Edit the `.env` file with your configuration:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_collection

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE=104857600  # 100MB

# Optional: CDN Configuration
CDN_ENABLED=false
CDN_BASE_URL=
```

### 2. Create Admin User

```bash
# Using Docker
docker-compose exec backend python create_admin.py

# Local development
python scripts/create_admin.py --name "AdminUser" --email admin@example.com
```

Follow the prompts to create your first admin user.

### 3. Verify Setup

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

## First Steps

### For Contributors

1. **Register an Account**: Visit http://localhost:3000 and create an account
2. **Choose a Language**: Select the language you want to contribute to
3. **Start Recording**: Begin with voice recordings or transcriptions
4. **Track Progress**: Monitor your contributions in the dashboard

### For Administrators

1. **Access Admin Panel**: Login with your admin account
2. **Configure Languages**: Add supported languages and scripts
3. **Manage Users**: Review user registrations and assign roles
4. **Monitor Quality**: Review transcription quality and consensus

## Contributing Voice Data

### Recording Guidelines

- **Environment**: Record in a quiet environment
- **Equipment**: Use a good quality microphone
- **Duration**: Keep recordings between 2-10 seconds
- **Content**: Read the provided text clearly and naturally

### Transcription Guidelines

- **Accuracy**: Transcribe exactly what you hear
- **Formatting**: Follow language-specific formatting rules
- **Quality**: Rate the audio quality honestly
- **Consensus**: Multiple transcriptions improve dataset quality

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# All services
docker compose logs -f

# Specific service (example: backend)
docker compose logs -f backend

# Restart all services
docker compose restart

# Restart a single Service
docker compose restart backend

# Or check status
docker compose ps
```

**Database connection errors:**
```bash
# Stop services and remove volumes
docker compose down -v --remove-orphans
# (Optional) Clean unused Docker resources
docker system prune -f
# Rebuild and start all services
docker compose up -d --build

# Run migrations inside the backend container
docker compose exec backend python scripts/init-db.py
# If that fails, try the fallback
docker compose exec backend python scripts/simple-init.py


```

**Permission errors:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER uploads/
chmod -R 755 uploads/
```

### Getting Help

- **Documentation**: Check our [comprehensive docs](README.md)
- **GitHub Issues**: Report bugs and request features
- **Discord**: Join our community for real-time help
- **Email**: Contact us at support@shrutik.org

## Next Steps

- **[Local Development Guide](local-development.md)** - Set up development environment
- **[Docker Local Setup](docker-local-setup.md)** - Docker development environment
- **[API Reference](api-reference.md)** - Integrate with external systems
- **[Contributing Guide](contributing.md)** - Contribute to the project
- **[Architecture Overview](architecture.md)** - Understand the system design

## Welcome to the Community

You're now ready to start using Shrutik! Whether you're contributing voice data, developing features, or deploying your own instance, you're part of a global movement to make voice technology more inclusive.

Join our community channels to connect with other contributors and stay updated on the latest developments.
