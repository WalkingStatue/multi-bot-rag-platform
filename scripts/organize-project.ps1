#!/usr/bin/env pwsh
# Project Organization Script
# This script reorganizes the project structure for better maintainability

Write-Host "🔧 Starting project reorganization..." -ForegroundColor Green

# Create new directory structure
$directories = @(
    "scripts",
    "tests/integration",
    "tests/e2e", 
    "tests/performance",
    "docs/development",
    "docs/deployment",
    "docs/api",
    "docs/architecture",
    ".github/workflows",
    "tools/dev",
    "tools/deployment"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "✅ Created directory: $dir" -ForegroundColor Yellow
    }
}

Write-Host "🎯 Project structure reorganized successfully!" -ForegroundColor Green
Write-Host "📁 New directories created for better organization" -ForegroundColor Cyan