#!/bin/bash

# Voice Data Collection Platform - Docker Development Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to start all services
start_services() {
    print_status "Starting Voice Data Collection Platform..."

    check_docker

    # Build and start services
    docker compose up --build -d

    print_status "Waiting for services to be ready..."

    # Wait for backend to be healthy
    print_status "Waiting for backend to start..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/ > /dev/null 2>&1; then
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done

    if [ $timeout -le 0 ]; then
        print_error "Backend failed to start within 60 seconds"
        docker compose logs backend
        exit 1
    fi

    print_success "All services are running!"
    print_status "Frontend: http://localhost:3000"
    print_status "Backend API: http://localhost:8000"
    print_status "API Docs: http://localhost:8000/docs"
    print_status "PostgreSQL: localhost:5432"
    print_status "Redis: localhost:6379"
}

# Function to stop all services
stop_services() {
    print_status "Stopping all services..."
    docker compose down
    print_success "All services stopped!"
}

# Function to restart all services
restart_services() {
    print_status "Restarting all services..."
    docker compose restart
    print_success "All services restarted!"
}

# Function to show logs
show_logs() {
    service=${1:-""}
    if [ -n "$service" ]; then
        print_status "Showing logs for $service..."
        docker compose logs -f "$service"
    else
        print_status "Showing logs for all services..."
        docker compose logs -f
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker compose ps
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker compose down -v --remove-orphans
    docker system prune -f
    print_success "Cleanup completed!"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database initialization..."

    # Try the comprehensive initialization script first
    if docker compose exec backend python scripts/init-db.py; then
        print_success "Database initialization completed!"
    else
        print_warning "Comprehensive initialization failed, trying simple approach..."
        if docker compose exec backend python scripts/simple-init.py; then
            print_success "Simple database initialization completed!"
        else
            print_error "Both initialization methods failed!"
            return 1
        fi
    fi
}

# Function to create admin user
create_admin() {
    print_status "Creating admin user..."
    docker compose exec backend python create_admin.py
    print_success "Admin user created!"
}

# Function to show help
show_help() {
    echo "Voice Data Collection Platform - Docker Development Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs [svc]  Show logs (optionally for specific service)"
    echo "  status      Show service status"
    echo "  cleanup     Clean up Docker resources"
    echo "  migrate     Run database migrations"
    echo "  admin       Create admin user"
    echo "  help        Show this help message"
    echo ""
    echo "Services: backend, frontend, celery, postgres, redis"
    echo ""
    echo "Examples:"
    echo "  $0 start                 # Start all services"
    echo "  $0 logs backend          # Show backend logs"
    echo "  $0 logs                  # Show all logs"
}

# Main script logic
case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs "$2"
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    migrate)
        run_migrations
        ;;
    admin)
        create_admin
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
