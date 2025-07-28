#!/usr/bin/env pwsh

Write-Host "Testing PostgreSQL Containers..." -ForegroundColor Cyan
Write-Host ""

function Test-PostgresContainer {
    param(
        [string]$ContainerName,
        [string]$ComposeFile,
        [string]$DatabaseName,
        [int]$Port,
        [string]$Description
    )
    
    Write-Host "================================" -ForegroundColor Yellow
    Write-Host "Testing $Description (Port $Port)" -ForegroundColor Yellow
    Write-Host "================================" -ForegroundColor Yellow
    
    # Check if container is running
    if ($ComposeFile) {
        $status = docker-compose -f $ComposeFile ps $ContainerName 2>$null
    } else {
        $status = docker-compose ps $ContainerName 2>$null
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Container $ContainerName is not running" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Container Status:" -ForegroundColor Green
    Write-Host $status
    Write-Host ""
    
    # Test health check
    Write-Host "Checking if $ContainerName is healthy..." -ForegroundColor Blue
    if ($ComposeFile) {
        $healthCheck = docker-compose -f $ComposeFile exec $ContainerName pg_isready -U postgres 2>$null
    } else {
        $healthCheck = docker-compose exec $ContainerName pg_isready -U postgres 2>$null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $Description is healthy" -ForegroundColor Green
        Write-Host ""
        
        # Test database connection
        Write-Host "Testing database connection..." -ForegroundColor Blue
        if ($ComposeFile) {
            docker-compose -f $ComposeFile exec $ContainerName psql -U postgres -d $DatabaseName -c "SELECT version();" 2>$null
        } else {
            docker-compose exec $ContainerName psql -U postgres -d $DatabaseName -c "SELECT version();" 2>$null
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "Testing table operations..." -ForegroundColor Blue
            
            $testTable = "test_" + (Get-Random -Maximum 1000)
            
            # Create test table
            if ($ComposeFile) {
                docker-compose -f $ComposeFile exec $ContainerName psql -U postgres -d $DatabaseName -c "CREATE TABLE IF NOT EXISTS $testTable (id SERIAL PRIMARY KEY, name VARCHAR(50), created_at TIMESTAMP DEFAULT NOW());" 2>$null
                docker-compose -f $ComposeFile exec $ContainerName psql -U postgres -d $DatabaseName -c "INSERT INTO $testTable (name) VALUES ('test_data_$(Get-Date -Format 'HHmmss')');" 2>$null
                docker-compose -f $ComposeFile exec $ContainerName psql -U postgres -d $DatabaseName -c "SELECT * FROM $testTable;" 2>$null
                docker-compose -f $ComposeFile exec $ContainerName psql -U postgres -d $DatabaseName -c "DROP TABLE $testTable;" 2>$null
            } else {
                docker-compose exec $ContainerName psql -U postgres -d $DatabaseName -c "CREATE TABLE IF NOT EXISTS $testTable (id SERIAL PRIMARY KEY, name VARCHAR(50), created_at TIMESTAMP DEFAULT NOW());" 2>$null
                docker-compose exec $ContainerName psql -U postgres -d $DatabaseName -c "INSERT INTO $testTable (name) VALUES ('test_data_$(Get-Date -Format 'HHmmss')');" 2>$null
                docker-compose exec $ContainerName psql -U postgres -d $DatabaseName -c "SELECT * FROM $testTable;" 2>$null
                docker-compose exec $ContainerName psql -U postgres -d $DatabaseName -c "DROP TABLE $testTable;" 2>$null
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ $Description operations successful" -ForegroundColor Green
                return $true
            } else {
                Write-Host "✗ $Description table operations failed" -ForegroundColor Red
                return $false
            }
        } else {
            Write-Host "✗ $Description database connection failed" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "✗ $Description is not healthy" -ForegroundColor Red
        return $false
    }
}

# Test main platform PostgreSQL
$mainResult = Test-PostgresContainer -ContainerName "postgres" -ComposeFile $null -DatabaseName "multi_bot_rag" -Port 5433 -Description "Main Platform PostgreSQL"

Write-Host ""

# Test test environment PostgreSQL
$testResult = Test-PostgresContainer -ContainerName "postgres-test" -ComposeFile "docker-compose.test.yml" -DatabaseName "multi_bot_rag_test" -Port 5434 -Description "Test PostgreSQL"

Write-Host ""
Write-Host "================================" -ForegroundColor Yellow
Write-Host "Connection Summary" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow

if ($mainResult) {
    Write-Host "✓ Main Platform DB: localhost:5433 (multi_bot_rag)" -ForegroundColor Green
} else {
    Write-Host "✗ Main Platform DB: localhost:5433 (multi_bot_rag)" -ForegroundColor Red
}

if ($testResult) {
    Write-Host "✓ Test DB: localhost:5434 (multi_bot_rag_test)" -ForegroundColor Green
} else {
    Write-Host "✗ Test DB: localhost:5434 (multi_bot_rag_test)" -ForegroundColor Red
}

Write-Host ""
Write-Host "External Connection Commands:" -ForegroundColor Cyan
Write-Host "psql -h localhost -p 5433 -U postgres -d multi_bot_rag" -ForegroundColor White
Write-Host "psql -h localhost -p 5434 -U postgres -d multi_bot_rag_test" -ForegroundColor White
Write-Host ""

if ($mainResult -and $testResult) {
    Write-Host "🎉 Both PostgreSQL containers are working correctly!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Some PostgreSQL containers have issues. Check the output above." -ForegroundColor Yellow
    exit 1
}