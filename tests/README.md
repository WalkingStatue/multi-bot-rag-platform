# Tests

## Structure

- `integration/` - Integration tests that test API endpoints and cross-service functionality
- Backend unit tests are located in `backend/tests/`

## Running Tests

```powershell
# All tests
.\scripts\test-runner.ps1

# Backend only
.\scripts\test-runner.ps1 -TestType backend

# Frontend only  
.\scripts\test-runner.ps1 -TestType frontend

# With coverage
.\scripts\test-runner.ps1 -Coverage
```

## Test Files

Integration tests cover:
- API endpoints with authentication
- RAG functionality with document processing
- WebSocket real-time features
- Database operations
- Multi-LLM provider integration