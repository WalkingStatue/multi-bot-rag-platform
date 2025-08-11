#!/usr/bin/env pwsh
# Simple Test Runner
# Runs tests using the single Docker Compose setup

param(
    [ValidateSet("all", "unit", "integration", "backend", "frontend")]
    [string]$TestType = "all",
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$Pattern = ""
)

Write-Host "🧪 Running Tests" -ForegroundColor Green
Write-Host "================" -ForegroundColor Green

# Ensure services are running
function Ensure-ServicesRunning {
    Write-Host "🔍 Checking if services are running..." -ForegroundColor Yellow
    
    $running = docker compose ps --services --filter "status=running"
    if (!$running -or $running.Count -lt 3) {
        Write-Host "⚠️ Services not running. Starting them..." -ForegroundColor Yellow
        docker compose up -d
        Start-Sleep -Seconds 15
    }
    
    Write-Host "✅ Services are ready" -ForegroundColor Green
}

# Run backend tests
function Run-BackendTests {
    Write-Host "🐍 Running backend tests..." -ForegroundColor Yellow

    $args = @("exec", "backend", "python", "-m", "pytest", "tests/")

    switch ($TestType) {
        "unit" { $args = @("exec", "backend", "python", "-m", "pytest", "tests/unit/") }
        # Integration tests at repo root are handled separately in Run-IntegrationTests
        "backend" { $args = @("exec", "backend", "python", "-m", "pytest", "tests/") }
        "all" { $args = @("exec", "backend", "python", "-m", "pytest", "tests/") }
    }

    if ($Coverage) { $args += "--cov=app", "--cov-report=html:/app/coverage" }
    if ($Verbose) { $args += "-v" }
    if ($Pattern) { $args += "-k", $Pattern }

    docker compose $args

    return $LASTEXITCODE -eq 0
}

function Run-IntegrationTests {
    if ($TestType -in @("integration", "all")) {
        Write-Host "🌐 Running repo-level integration tests..." -ForegroundColor Yellow

        $srcTests = (Resolve-Path "$PSScriptRoot/../tests").Path
        $destTests = (Resolve-Path "$PSScriptRoot/../backend").Path + "\repo-tests"

        if (Test-Path $destTests) { Remove-Item -Recurse -Force $destTests }
        Copy-Item -Recurse -Force $srcTests $destTests

        $args = @("exec", "backend", "python", "-m", "pytest", "repo-tests/integration/")
        if ($Verbose) { $args += "-v" }
        if ($Pattern) { $args += "-k", $Pattern }

        docker compose $args

        return $LASTEXITCODE -eq 0
    }

    return $true
}

# Run frontend tests
function Run-FrontendTests {
    Write-Host "⚛️ Running frontend tests..." -ForegroundColor Yellow
    
    $args = @("exec", "frontend", "npm", "test", "--", "--run")
    if ($Coverage) { $args += "--coverage" }
    
    docker compose $args
    
    return $LASTEXITCODE -eq 0
}

# Main execution
Ensure-ServicesRunning

$success = $true

if ($TestType -in @("all", "unit", "backend", "integration")) {
    $success = (Run-BackendTests) -and $success
}

if ($TestType -in @("all", "integration")) {
    $success = (Run-IntegrationTests) -and $success
}

if ($TestType -in @("all", "frontend")) {
    $success = (Run-FrontendTests) -and $success
}

if ($success) {
    Write-Host ""
    Write-Host "🎉 All tests passed!" -ForegroundColor Green
    
    if ($Coverage) {
        if (Test-Path "backend/coverage/index.html") {
            Write-Host "📊 Backend coverage: backend/coverage/index.html" -ForegroundColor Cyan
        }
        if (Test-Path "frontend/coverage/index.html") {
            Write-Host "📊 Frontend coverage: frontend/coverage/index.html" -ForegroundColor Cyan
        }
    }
    
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ Some tests failed" -ForegroundColor Red
    exit 1
}