# Voice Data Collection Platform

A web-based crowdsourcing platform for collecting Bangla voice recordings and transcriptions to train Sworik AI.

## Features

- Voice recording with script reading (2, 5, 10 minute durations)
- Intelligent audio chunking using VAD and sentence boundary detection
- Transcription interface with consensus validation
- Admin dashboard for user and data management
- Secure data export for authorized developers
- Role-based access control

## Technology Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Audio Processing**: librosa, pydub
- **Background Jobs**: Celery
- **Frontend**: React (to be implemented)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Node.js 18+ (for frontend)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd voice-data-collection
   ```

2. **Set up Python virtual environment**
   ```bash
   ./scripts/setup-venv.sh
   source venv/bin/activate
   ```

3. **Start development services**
   ```bash
   ./scripts/start-dev.sh
   ```

4. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Manual Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL and Redis**
   ```bash
   docker-compose up -d postgres redis
   ```

3. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Start Celery worker (in another terminal)**
   ```bash
   celery -A app.core.celery_app worker --loglevel=info
   ```

## Project Structure

```
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core configuration and utilities
│   ├── db/            # Database configuration
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── tasks/         # Celery tasks
│   └── utils/         # Utility functions
├── alembic/           # Database migrations
├── scripts/           # Development scripts
├── uploads/           # File uploads (created at runtime)
├── docker-compose.yml # Docker services
├── Dockerfile         # Application container
└── requirements.txt   # Python dependencies
```

## Environment Configuration

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Key configuration options:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (change in production)
- `UPLOAD_DIR`: Directory for file uploads
- `MAX_FILE_SIZE`: Maximum upload file size

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

### Running Tests

```bash
pytest
```

### Code Quality

The project uses standard Python tools for code quality:
- Black for code formatting
- isort for import sorting
- flake8 for linting

## Deployment

### Production Deployment

1. Build the Docker image:
   ```bash
   docker build -t voice-collection-platform .
   ```

2. Deploy using Docker Compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment Variables

Set the following environment variables in production:
- `DEBUG=false`
- `SECRET_KEY=<secure-random-key>`
- `DATABASE_URL=<production-database-url>`
- `REDIS_URL=<production-redis-url>`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[License information to be added]