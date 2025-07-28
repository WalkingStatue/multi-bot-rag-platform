#!/bin/bash

# Script to run tests in different environments

set -e

echo "Multi-Bot RAG Platform Test Runner"
echo "=================================="

# Function to run tests in Docker
run_docker_tests() {
    echo "Running tests in Docker environment..."
    
    # Start test services
    echo "Starting test database services..."
    docker-compose -f docker-compose.test.yml up -d postgres-test redis-test qdrant-test
    
    # Wait for services to be healthy
    echo "Waiting for services to be ready..."
    docker-compose -f docker-compose.test.yml exec postgres-test pg_isready -U postgres
    
    # Run tests
    echo "Running tests..."
    docker-compose -f docker-compose.test.yml run --rm backend-test
    
    # Cleanup
    echo "Cleaning up test services..."
    docker-compose -f docker-compose.test.yml down -v
}

# Function to run tests locally
run_local_tests() {
    echo "Running tests locally..."
    
    # Check if test database is running
    if ! docker-compose -f docker-compose.test.yml ps postgres-test | grep -q "Up"; then
        echo "Starting test database..."
        docker-compose -f docker-compose.test.yml up -d postgres-test redis-test qdrant-test
        
        # Wait for database to be ready
        echo "Waiting for database to be ready..."
        sleep 10
    fi
    
    # Run tests locally
    cd backend
    python -m pytest -v --tb=short
    cd ..
}

# Parse command line arguments
case "${1:-docker}" in
    "docker")
        run_docker_tests
        ;;
    "local")
        run_local_tests
        ;;
    "cleanup")
        echo "Cleaning up test services..."
        docker-compose -f docker-compose.test.yml down -v
        ;;
    *)
        echo "Usage: $0 [docker|local|cleanup]"
        echo "  docker  - Run tests in Docker containers (default)"
        echo "  local   - Run tests locally with Docker database"
        echo "  cleanup - Stop and remove test services"
        exit 1
        ;;
esac

echo "Done!"