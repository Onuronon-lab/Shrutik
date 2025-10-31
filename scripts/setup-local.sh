#!/bin/bash

# Shrutik (শ্রুতিক) Local Setup Script
# This script sets up the development environment for Shrutik

set -e

echo "🎤 Setting up Shrutik (শ্রুতিক) - Voice Data Collection Platform"
echo "=================================================================="

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

# Check if running on supported OS
check_os() {
    print_status "Checking operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_success "Linux detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "macOS detected"
    else
        print_error "Unsupported operating system: $OSTYPE"
        print_error "This script supports Linux and macOS only"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_success "Python 3.11 found"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$PYTHON_VERSION" == "3.11" ]] || [[ "$PYTHON_VERSION" == "3.12" ]]; then
            PYTHON_CMD="python3"
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.11+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3.11+ not found"
        print_error "Please install Python 3.11 or higher"
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [[ "$NODE_VERSION" -ge 18 ]]; then
            print_success "Node.js $NODE_VERSION found"
        else
            print_error "Node.js 18+ required, found $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js not found"
        print_error "Please install Node.js 18 or higher"
        exit 1
    fi
    
    # Check PostgreSQL
    if command -v psql &> /dev/null; then
        print_success "PostgreSQL found"
    else
        print_warning "PostgreSQL not found"
        print_warning "You'll need to install PostgreSQL manually"
    fi
    
    # Check Redis
    if command -v redis-cli &> /dev/null; then
        print_success "Redis found"
    else
        print_warning "Redis not found"
        print_warning "You'll need to install Redis manually"
    fi
}

# Setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [[ ! -d "venv" ]]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    if [[ -d "frontend" ]]; then
        cd frontend
        
        # Install dependencies
        print_status "Installing Node.js dependencies..."
        npm install
        
        # Copy environment file
        if [[ ! -f ".env.local" ]]; then
            cp .env.example .env.local
            print_success "Frontend environment file created"
        else
            print_warning "Frontend environment file already exists"
        fi
        
        cd ..
        print_success "Frontend setup complete"
    else
        print_warning "Frontend directory not found, skipping frontend setup"
    fi
}

# Setup environment files
setup_environment() {
    print_status "Setting up environment configuration..."
    
    # Backend environment
    if [[ ! -f ".env.development" ]]; then
        cp .env.example .env.development
        print_success "Backend development environment file created"
        print_warning "Please edit .env.development with your database and Redis configuration"
    else
        print_warning "Backend environment file already exists"
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if PostgreSQL is running
    if command -v pg_isready &> /dev/null && pg_isready -q; then
        print_success "PostgreSQL is running"
        
        # Create database if it doesn't exist
        if ! psql -lqt | cut -d \| -f 1 | grep -qw shrutik_dev; then
            createdb shrutik_dev
            print_success "Development database created"
        else
            print_warning "Development database already exists"
        fi
        
        # Run migrations
        source venv/bin/activate
        alembic upgrade head
        print_success "Database migrations applied"
        
    else
        print_warning "PostgreSQL is not running or not accessible"
        print_warning "Please start PostgreSQL and run: createdb shrutik_dev"
        print_warning "Then run: alembic upgrade head"
    fi
}

# Create admin user
create_admin_user() {
    print_status "Creating admin user..."
    
    if [[ -f "create_admin.py" ]]; then
        source venv/bin/activate
        print_warning "Please follow the prompts to create an admin user:"
        python create_admin.py
    else
        print_warning "Admin user creation script not found"
    fi
}

# Final instructions
show_final_instructions() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "Next steps:"
    echo "1. Start PostgreSQL and Redis if not already running"
    echo "2. Edit .env.development with your configuration"
    echo "3. Run the development servers:"
    echo ""
    echo "   # Start backend (in one terminal)"
    echo "   source venv/bin/activate"
    echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "   # Start Celery worker (in another terminal)"
    echo "   source venv/bin/activate"
    echo "   celery -A app.tasks.celery_app worker --loglevel=info"
    echo ""
    echo "   # Start frontend (in another terminal)"
    echo "   cd frontend && npm run dev"
    echo ""
    echo "4. Access the application:"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo ""
    echo "📚 Documentation: docs/README.md"
    echo "🤝 Contributing: docs/contributing.md"
    echo "💬 Community: https://discord.gg/9hZ9eW8ARk"
    echo ""
    echo "Happy coding! 🚀"
}

# Main execution
main() {
    check_os
    check_prerequisites
    setup_python_env
    setup_frontend
    setup_environment
    setup_database
    create_admin_user
    show_final_instructions
}

# Run main function
main "$@"