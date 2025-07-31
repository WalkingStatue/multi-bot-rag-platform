#!/usr/bin/env pwsh

# Test script for API keys management
$baseUrl = "http://localhost:8000/api"

# Test user data
$userData = @{
    username = "testuser"
    email = "test@example.com"
    password = "testpassword123"
    full_name = "Test User"
} | ConvertTo-Json

Write-Host "1. Registering test user..." -ForegroundColor Yellow

try {
    $registerResponse = Invoke-WebRequest -Uri "$baseUrl/auth/register" -Method POST -Body $userData -ContentType "application/json"
    Write-Host "✅ User registered successfully" -ForegroundColor Green
    $user = $registerResponse.Content | ConvertFrom-Json
    Write-Host "User ID: $($user.id)" -ForegroundColor Cyan
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "⚠️  User might already exist, trying to login..." -ForegroundColor Yellow
    } else {
        Write-Host "❌ Registration failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n2. Logging in..." -ForegroundColor Yellow

$loginData = @{
    username = "testuser"
    password = "testpassword123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-WebRequest -Uri "$baseUrl/auth/login" -Method POST -Body $loginData -ContentType "application/json"
    Write-Host "✅ Login successful" -ForegroundColor Green
    $tokens = $loginResponse.Content | ConvertFrom-Json
    $accessToken = $tokens.access_token
    Write-Host "Access token obtained" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n3. Testing API keys providers endpoint..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

try {
    $providersResponse = Invoke-WebRequest -Uri "$baseUrl/users/api-keys/providers" -Method GET -Headers $headers
    Write-Host "✅ Providers endpoint working!" -ForegroundColor Green
    $providers = $providersResponse.Content | ConvertFrom-Json
    Write-Host "Available providers:" -ForegroundColor Cyan
    $providers.providers.PSObject.Properties | ForEach-Object {
        Write-Host "  - $($_.Name): $($_.Value.models.Count) models" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Providers endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
    exit 1
}

Write-Host "`n4. Testing API keys list endpoint..." -ForegroundColor Yellow

try {
    $apiKeysResponse = Invoke-WebRequest -Uri "$baseUrl/users/api-keys" -Method GET -Headers $headers
    Write-Host "✅ API keys endpoint working!" -ForegroundColor Green
    $apiKeys = $apiKeysResponse.Content | ConvertFrom-Json
    Write-Host "Current API keys count: $($apiKeys.Count)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ API keys endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 All API endpoints are working correctly!" -ForegroundColor Green
Write-Host "The 'Failed to load API keys and providers' error is likely a frontend issue." -ForegroundColor Yellow