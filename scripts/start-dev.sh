#!/bin/bash

# Start development environment
echo "Starting Voice Data Collection Platform development environment..."

# Start Docker services
docker-compose up -d postgres redis

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI application
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload