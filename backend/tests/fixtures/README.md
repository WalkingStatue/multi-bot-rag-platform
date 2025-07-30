# Test User Setup

This directory contains utilities for creating and managing a persistent test user in your database for testing purposes.

## Overview

The test user setup provides a way to create a dedicated test user with all necessary data (bots, conversations, API keys, etc.) that persists across test runs. This ensures that:

1. Your real database data is protected during testing
2. Tests have consistent, predictable data to work with
3. Integration tests can use real database operations without side effects

## Files

- `test_user_setup.py` - Core utilities for creating and managing test users
- `README.md` - This documentation file

## Quick Start

### 1. Set up the test user in your database

```bash
# From the backend directory
python scripts/setup_test_user.py
```

This will create:
- A test user with username `test_user_automated`
- User settings and preferences
- API keys for all supported providers (with test values)
- A test bot owned by the user
- A sample conversation with messages

### 2. Use the test user in your tests

```python
def test_something(persistent_test_user):
    """Test using the persistent test user."""
    assert persistent_test_user.username == "test_user_automated"
    # Your test code here...

def test_with_auth(client, persistent_test_user_auth):
    """Test with authentication."""
    login_data = {
        "username": persistent_test_user_auth["username"],
        "password": persistent_test_user_auth["password"]
    }
    response = client.post("/api/auth/login", json=login_data)
    # Your test code here...

def test_complete_environment(persistent_test_environment):
    """Test with complete test environment."""
    env = persistent_test_environment
    user = env["user"]
    bot = env["bot"]
    conversation = env["conversation"]
    # Your test code here...
```

## Available Fixtures

### `persistent_test_user`
Returns the persistent test user object from the database.

### `persistent_test_user_auth`
Returns authentication credentials for the test user:
```python
{
    "username": "test_user_automated",
    "password": "TestPassword123!"
}
```

### `persistent_test_environment`
Returns a complete test environment with all related objects:
```python
{
    "user": User,           # The test user
    "settings": UserSettings, # User preferences
    "api_keys": dict,       # API keys by provider
    "bot": Bot,            # Test bot owned by user
    "conversation": ConversationSession, # Sample conversation
    "messages": list       # Sample messages
}
```

## Test User Details

The persistent test user has these characteristics:

- **Username**: `test_user_automated`
- **Email**: `test.automated@example.com`
- **Password**: `TestPassword123!`
- **Full Name**: `Automated Test User`
- **ID**: `550e8400-e29b-41d4-a716-446655440000` (fixed UUID)

### Associated Data

- **Bot**: "Test Bot Automated" with OpenAI GPT-3.5-turbo
- **API Keys**: Test keys for OpenAI, Anthropic, Gemini, and OpenRouter
- **Settings**: Default preferences with test mode enabled
- **Conversation**: Sample conversation with 4 messages

## Management Commands

### View test user information
```bash
python scripts/setup_test_user.py --info
```

### Reset the test user (delete and recreate)
```bash
python scripts/setup_test_user.py --reset
```

### Clean up the test user
```bash
python scripts/setup_test_user.py --cleanup
```

## Using TestUserManager Directly

For more advanced use cases, you can use the `TestUserManager` class directly:

```python
from tests.fixtures.test_user_setup import TestUserManager

def test_custom_setup(db_session):
    manager = TestUserManager(db_session)
    
    # Create just a user
    user = manager.create_test_user()
    
    # Create custom bot
    bot = manager.create_test_bot(user, {
        "name": "Custom Test Bot",
        "llm_provider": "anthropic",
        "llm_model": "claude-3-sonnet"
    })
    
    # Create custom conversation
    conversation = manager.create_test_conversation(bot, user, {
        "title": "Custom Test Conversation"
    })
```

## Best Practices

### 1. Use persistent fixtures for integration tests
```python
def test_api_endpoint(client, persistent_test_user_auth):
    """Integration test using persistent test user."""
    # This test uses real database operations
    pass
```

### 2. Use regular fixtures for unit tests
```python
def test_service_logic(test_user):
    """Unit test using temporary test user."""
    # This test uses isolated test database
    pass
```

### 3. Clean up after test runs
```python
# In CI/CD pipeline or after test suite
python scripts/setup_test_user.py --cleanup
```

### 4. Reset when test data gets corrupted
```python
# If test data becomes inconsistent
python scripts/setup_test_user.py --reset
```

## Safety Features

- **Isolated Data**: Test user has distinctive username/email to prevent conflicts
- **Fixed IDs**: Uses predictable UUIDs for consistent testing
- **Cascade Deletion**: Cleaning up removes all associated data
- **Test-Only Keys**: API keys are clearly marked as test values

## Troubleshooting

### Test user already exists
If you see "Test user already exists", you can:
- Use `--info` to see current state
- Use `--reset` to recreate
- Use `--cleanup` to remove

### Database connection issues
Ensure your database is running and the connection string in `config.py` is correct.

### Missing dependencies
Make sure all required packages are installed:
```bash
pip install -r requirements.txt
```

### Permission errors
Ensure the database user has CREATE, INSERT, UPDATE, DELETE permissions.

## Example Test

See `test_persistent_user_example.py` for complete examples of how to use the persistent test user in your tests.