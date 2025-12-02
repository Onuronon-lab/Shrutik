#!/bin/bash

# Build and serve Shrutik documentation with mdBook

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

# Check if mdBook is installed
check_mdbook() {
    if ! command -v mdbook &> /dev/null; then
        print_error "mdBook is not installed!"
        echo ""
        echo "Install mdBook using one of these methods:"
        echo ""
        echo "1. Using Cargo (Rust package manager):"
        echo "   cargo install mdbook"
        echo ""
        echo "2. Using pre-built binaries:"
        echo "   Visit: https://github.com/rust-lang/mdBook/releases"
        echo ""
        echo "3. Using package managers:"
        echo "   # macOS with Homebrew"
        echo "   brew install mdbook"
        echo ""
        echo "   # Ubuntu/Debian"
        echo "   sudo apt install mdbook"
        echo ""
        exit 1
    fi
}

# Function to build documentation
build_docs() {
    print_status "Building Shrutik documentation..."

    # Create theme directory if it doesn't exist
    mkdir -p docs/theme

    # Build the book
    if mdbook build; then
        print_success "Documentation built successfully!"
        print_status "Output directory: $(pwd)/book"
    else
        print_error "Failed to build documentation"
        exit 1
    fi
}

# Function to serve documentation locally
serve_docs() {
    print_status "Starting local documentation server..."
    print_status "Documentation will be available at: http://localhost:3000"
    print_status "Press Ctrl+C to stop the server"
    echo ""

    # Serve the book with live reload
    mdbook serve --port 3000 --hostname 0.0.0.0
}

# Function to watch for changes
watch_docs() {
    print_status "Watching for changes and rebuilding automatically..."
    print_status "Documentation will be available at: http://localhost:3000"
    print_status "Press Ctrl+C to stop watching"
    echo ""

    # Watch and serve with live reload
    mdbook serve --port 3000 --hostname 0.0.0.0 --open
}

# Function to clean build artifacts
clean_docs() {
    print_status "Cleaning documentation build artifacts..."

    if [ -d "book" ]; then
        rm -rf book
        print_success "Cleaned build directory"
    else
        print_warning "No build directory found"
    fi
}

# Function to test documentation
test_docs() {
    print_status "Testing documentation..."

    # Test the book for broken links and other issues
    if mdbook test; then
        print_success "Documentation tests passed!"
    else
        print_error "Documentation tests failed"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "Shrutik Documentation Builder"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     Build the documentation (static files)"
    echo "  serve     Build and serve documentation locally"
    echo "  watch     Watch for changes and rebuild automatically (default)"
    echo "  clean     Clean build artifacts"
    echo "  test      Test documentation for issues"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Watch and serve with live reload"
    echo "  $0 build          # Build static documentation"
    echo "  $0 serve          # Serve documentation locally"
    echo "  $0 clean          # Clean build directory"
    echo ""
    echo "The documentation will be available at http://localhost:3000"
    echo ""
}

# Main script logic
main() {
    # Check if mdBook is installed
    check_mdbook

    # Parse command line arguments
    case "${1:-watch}" in
        "build")
            build_docs
            ;;
        "serve")
            build_docs
            serve_docs
            ;;
        "watch")
            watch_docs
            ;;
        "clean")
            clean_docs
            ;;
        "test")
            test_docs
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
