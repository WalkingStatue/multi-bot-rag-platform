# Test Organization

## Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── services/           # Service layer tests
│   ├── models/             # Database model tests
│   ├── utils/              # Utility function tests
│   └── core/               # Core functionality tests
├── integration/            # Integration tests
│   ├── api/                # API endpoint tests
│   ├── database/           # Database integration tests
│   └── external/           # External service integration tests
├── e2e/                    # End-to-end tests
│   ├── workflows/          # Complete user workflows
│   └── scenarios/          # Complex business scenarios
├── fixtures/               # Test data and fixtures
├── conftest.py             # Pytest configuration and fixtures
└── README.md               # This file
```

## Test Categories

### Unit Tests (`unit/`)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution
- High coverage of business logic

### Integration Tests (`integration/`)
- Test component interactions
- Use real database connections
- Test API endpoints with full request/response cycle
- Verify service integrations

### End-to-End Tests (`e2e/`)
- Test complete user workflows
- Simulate real user interactions
- Test across multiple services
- Verify business scenarios

## Running Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test categories
docker-compose exec backend pytest tests/unit/
docker-compose exec backend pytest tests/integration/
docker-compose exec backend pytest tests/e2e/

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec backend pytest tests/unit/services/test_auth_service.py

# Run tests matching pattern
docker-compose exec backend pytest -k "test_auth"
```

## Test Naming Conventions

- Test files: `test_[module_name].py`
- Test classes: `Test[ClassName]`
- Test methods: `test_[functionality]_[expected_outcome]`

Example:
```python
class TestAuthService:
    def test_login_with_valid_credentials_returns_token(self):
        pass
    
    def test_login_with_invalid_credentials_raises_exception(self):
        pass
```

## Fixtures and Test Data

- Common fixtures in `conftest.py`
- Test-specific fixtures in individual test files
- Test data in `fixtures/` directory
- Use factories for creating test objects

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe what they test
3. **Speed**: Unit tests should be fast, integration tests can be slower
4. **Coverage**: Aim for high test coverage but focus on critical paths
5. **Maintenance**: Keep tests simple and maintainable