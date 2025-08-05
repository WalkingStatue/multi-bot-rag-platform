#!/usr/bin/env pwsh
# Multi-Bot RAG Platform Setup Script
# Single unified setup for development, testing, and production

param(
    [switch]$Clean,
    [switch]$Build,
    [switch]$Migrate,
    [switch]$Seed,
    [switch]$Test,
    [switch]$Verbose
)

Write-Host "🚀 Multi-Bot RAG Platform Setup" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

# Check prerequisites
function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    try {
        $dockerVersion = docker --version
        Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
        exit 1
    }
    
    try {
        $composeVersion = docker compose version
        Write-Host "✅ Docker Compose: $composeVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker Compose not found." -ForegroundColor Red
        exit 1
    }
}

# Clean environment
function Clean-Environment {
    if ($Clean) {
        Write-Host "🧹 Cleaning environment..." -ForegroundColor Yellow
        docker compose down --volumes --remove-orphans
        docker system prune -f
        Write-Host "✅ Environment cleaned" -ForegroundColor Green
    }
}

# Setup environment
function Setup-Environment {
    Write-Host "⚙️ Setting up environment..." -ForegroundColor Yellow
    
    if (!(Test-Path ".env")) {
        if (Test-Path "config/.env.example") {
            Copy-Item "config/.env.example" ".env"
        } elseif (Test-Path ".env.dev") {
            Copy-Item ".env.dev" ".env"
        } else {
            Write-Host "❌ No environment template found" -ForegroundColor Red
            exit 1
        }
        Write-Host "✅ Created .env file" -ForegroundColor Green
    }
}

# Start services
function Start-Services {
    Write-Host "🐳 Starting services..." -ForegroundColor Yellow
    
    $composeArgs = @("up")
    if ($Build) { $composeArgs += "--build" }
    if (!$Verbose) { $composeArgs += "-d" }
    
    & docker compose $composeArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Services started successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to start services" -ForegroundColor Red
        exit 1
    }
}

# Run database migrations
function Run-Migrations {
    if ($Migrate) {
        Write-Host "🗃️ Running database migrations..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        docker compose exec backend alembic upgrade head
        Write-Host "✅ Database migrations completed" -ForegroundColor Green
    }
}

# Seed database
function Seed-Database {
    if ($Seed) {
        Write-Host "🌱 Seeding database..." -ForegroundColor Yellow
        docker compose exec backend python -c "
import sys
sys.path.append('/app')
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

# Create sample user
db = next(get_db())
if not db.query(User).filter(User.email == 'admin@example.com').first():
    user = User(
        email='admin@example.com',
        username='admin',
        hashed_password=get_password_hash('admin123'),
        is_active=True
    )
    db.add(user)
    db.commit()
    print('Sample user created: admin@example.com / admin123')
else:
    print('Sample user already exists')
"
        Write-Host "✅ Database seeded" -ForegroundColor Green
    }
}

# Run tests
function Run-Tests {
    if ($Test) {
        Write-Host "🧪 Running tests..." -ForegroundColor Yellow
        docker compose exec backend python -m pytest tests/ -v
        Write-Host "✅ Tests completed" -ForegroundColor Green
    }
}

# Display service information
function Show-ServiceInfo {
    Write-Host ""
    Write-Host "🎉 Platform is ready!" -ForegroundColor Green
    Write-Host "=====================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 Frontend:      http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 Backend API:   http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 API Docs:      http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "🗃️ Database:      localhost:5432 (postgres/postgres)" -ForegroundColor Cyan
    Write-Host "🔴 Redis:         localhost:6379" -ForegroundColor Cyan
    Write-Host "🔍 Qdrant:        http://localhost:6333" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Useful commands:" -ForegroundColor Yellow
    Write-Host "  docker compose logs -f          # View all logs" -ForegroundColor White
    Write-Host "  docker compose logs -f backend  # View backend logs" -ForegroundColor White
    Write-Host "  docker compose restart backend  # Restart backend" -ForegroundColor White
    Write-Host "  docker compose down             # Stop all services" -ForegroundColor White
    Write-Host ""
}

# Main execution
Test-Prerequisites
Clean-Environment
Setup-Environment
Start-Services
Run-Migrations
Seed-Database
Run-Tests
Show-ServiceInfo