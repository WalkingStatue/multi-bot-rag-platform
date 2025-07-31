# Testing API Keys Management

## Issue Analysis

The "Failed to load API keys and providers" error is likely due to authentication issues. Here's how to test and resolve it:

## Backend Status ✅

The backend API is working correctly:
- ✅ Health endpoint: `http://localhost:8000/health`
- ✅ Providers endpoint: `http://localhost:8000/api/users/api-keys/providers` (requires auth)
- ✅ API keys endpoint: `http://localhost:8000/api/users/api-keys` (requires auth)

## Frontend Testing Steps

### 1. Access the Application
1. Open your browser and go to `http://localhost:3000`
2. You should be redirected to the login page if not authenticated

### 2. Create a Test Account
1. Click "create a new account" on the login page
2. Fill in the registration form:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `testpassword123`
   - Full Name: `Test User`
3. Click "Register"

### 3. Access API Keys Management
1. After successful registration/login, you should be on the dashboard
2. Click "API Keys" in the navigation menu, or
3. Click the "API Keys" quick action button, or
4. Navigate directly to `http://localhost:3000/dashboard?view=api-keys`

### 4. Expected Behavior
- ✅ You should see the API Keys Management page
- ✅ You should see "No API Keys" message initially
- ✅ You should see an "Add API Key" button
- ✅ Available providers should be listed: OpenAI, Anthropic, OpenRouter, Gemini

## Troubleshooting

### If you see "Failed to load API keys and providers":

1. **Check Authentication**:
   - Open browser developer tools (F12)
   - Go to Application/Storage tab
   - Check if `access_token` and `refresh_token` are in localStorage
   - If missing, you're not logged in

2. **Check Network Requests**:
   - Open Network tab in developer tools
   - Look for failed requests to `/api/users/api-keys/providers`
   - Check if you get 401/403 errors (authentication issues)

3. **Check Console Errors**:
   - Look for JavaScript errors in the Console tab
   - Common issues: CORS errors, network timeouts, authentication failures

### Manual API Test (PowerShell)

Run the test script to verify backend functionality:
```powershell
./test-api-keys.ps1
```

This script will:
1. Register a test user
2. Login and get tokens
3. Test the providers endpoint
4. Test the API keys endpoint

## Common Solutions

### 1. Clear Browser Storage
```javascript
// Run in browser console
localStorage.clear();
sessionStorage.clear();
location.reload();
```

### 2. Restart Services
```bash
cd multi-bot-rag-platform
docker-compose restart frontend backend
```

### 3. Check Service Logs
```bash
# Backend logs
docker-compose logs backend --tail=50

# Frontend logs  
docker-compose logs frontend --tail=50
```

## Expected API Responses

### Providers Endpoint Response:
```json
{
  "providers": {
    "openai": {
      "name": "openai",
      "models": ["gpt-4", "gpt-3.5-turbo", ...]
    },
    "anthropic": {
      "name": "anthropic", 
      "models": ["claude-3-opus", "claude-3-sonnet", ...]
    },
    "openrouter": {
      "name": "openrouter",
      "models": ["openai/gpt-4", "anthropic/claude-3-opus", ...]
    },
    "gemini": {
      "name": "gemini",
      "models": ["gemini-pro", "gemini-pro-vision", ...]
    }
  },
  "total": 4
}
```

### API Keys Endpoint Response:
```json
[]
```
(Empty array initially, since no API keys are configured)

## Next Steps

Once you can access the API Keys Management page:
1. Click "Add API Key"
2. Select a provider (e.g., OpenAI)
3. Enter your API key
4. Click "Validate" to test the key
5. Click "Add API Key" to save

The system will encrypt and store your API key securely.