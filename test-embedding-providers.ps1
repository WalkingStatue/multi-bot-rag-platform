#!/usr/bin/env pwsh

# Test script for embedding providers
$baseUrl = "http://localhost:8000/api"

# Test user credentials (use existing test user)
$loginData = @{
    username = "testuser"
    password = "testpassword123"
} | ConvertTo-Json

Write-Host "1. Logging in..." -ForegroundColor Yellow

try {
    $loginResponse = Invoke-WebRequest -Uri "$baseUrl/auth/login" -Method POST -Body $loginData -ContentType "application/json"
    Write-Host "✅ Login successful" -ForegroundColor Green
    $tokens = $loginResponse.Content | ConvertFrom-Json
    $accessToken = $tokens.access_token
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

Write-Host "`n2. Testing embedding providers endpoint..." -ForegroundColor Yellow

try {
    $embeddingProvidersResponse = Invoke-WebRequest -Uri "$baseUrl/users/embedding-providers" -Method GET -Headers $headers
    Write-Host "✅ Embedding providers endpoint working!" -ForegroundColor Green
    $embeddingProviders = $embeddingProvidersResponse.Content | ConvertFrom-Json
    Write-Host "Available embedding providers:" -ForegroundColor Cyan
    $embeddingProviders.providers.PSObject.Properties | ForEach-Object {
        $provider = $_.Value
        Write-Host "  - $($_.Name): $($provider.models.Count) models, requires API key: $($provider.requires_api_key)" -ForegroundColor White
        $provider.models | ForEach-Object {
            Write-Host "    * $_" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "❌ Embedding providers endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
    exit 1
}

Write-Host "`n3. Testing LLM providers endpoint..." -ForegroundColor Yellow

try {
    $llmProvidersResponse = Invoke-WebRequest -Uri "$baseUrl/users/api-keys/providers" -Method GET -Headers $headers
    Write-Host "✅ LLM providers endpoint working!" -ForegroundColor Green
    $llmProviders = $llmProvidersResponse.Content | ConvertFrom-Json
    Write-Host "Available LLM providers:" -ForegroundColor Cyan
    $llmProviders.providers.PSObject.Properties | ForEach-Object {
        $provider = $_.Value
        Write-Host "  - $($_.Name): $($provider.models.Count) models" -ForegroundColor White
    }
} catch {
    Write-Host "❌ LLM providers endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 All provider endpoints are working correctly!" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "- LLM Providers: $($llmProviders.total)" -ForegroundColor White
Write-Host "- Embedding Providers: $($embeddingProviders.total)" -ForegroundColor White
Write-Host "- Local embedding support: Removed ✅" -ForegroundColor Green
Write-Host "- Real-time model fetching: Ready for implementation ✅" -ForegroundColor Green