"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.config import settings


# Create test database engine - using PostgreSQL for testing
# Use the same database as development but with a different database name for isolation
import os

# Check if we're running in Docker or locally
if os.getenv("DOCKER_ENV") == "true":
    # Docker environment - use service names
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@postgres:5432/multi_bot_rag_test"
else:
    # Local environment - use localhost
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/multi_bot_rag_test"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def cleanup_test_data(session):
    """Clean up test data from all tables."""
    try:
        # Delete in reverse dependency order to avoid foreign key constraints
        session.execute(text("DELETE FROM document_chunks"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM activity_logs"))
        session.execute(text("DELETE FROM documents"))
        session.execute(text("DELETE FROM conversation_sessions"))
        session.execute(text("DELETE FROM bot_permissions"))
        session.execute(text("DELETE FROM bots"))
        session.execute(text("DELETE FROM user_api_keys"))
        session.execute(text("DELETE FROM user_settings"))
        session.execute(text("DELETE FROM users"))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error cleaning up test data: {e}")


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Use the migrated database - simple session without transactions
    session = TestingSessionLocal()
    
    # Clean up any existing test data before the test
    cleanup_test_data(session)
    
    try:
        yield session
    finally:
        # Clean up test data after the test
        cleanup_test_data(session)
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def persistent_test_user():
    """
    Get the persistent test user from the actual database.
    
    This fixture returns the test user that was created using the
    setup_test_user.py script. This user persists across test runs
    and should be used for integration tests that need a stable user.
    """
    from tests.fixtures.test_user_setup import TestUserManager
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        manager = TestUserManager(db)
        user = manager.get_test_user()
        if not user:
            # If no persistent test user exists, create one
            test_data = manager.setup_complete_test_environment()
            user = test_data['user']
        return user
    finally:
        db.close()


@pytest.fixture(scope="function")
def persistent_test_user_auth():
    """Get authentication credentials for the persistent test user."""
    from tests.fixtures.test_user_setup import TestUserManager
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        manager = TestUserManager(db)
        return manager.get_test_user_credentials()
    finally:
        db.close()


@pytest.fixture(scope="function")
def persistent_test_environment():
    """
    Get the complete persistent test environment.
    
    Returns a dictionary with user, bot, conversation, messages, etc.
    that persists across test runs.
    """
    from tests.fixtures.test_user_setup import TestUserManager
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        manager = TestUserManager(db)
        user = manager.get_test_user()
        if not user:
            # Create complete environment if it doesn't exist
            return manager.setup_complete_test_environment()
        
        # Return existing environment
        return {
            "user": user,
            "settings": user.settings,
            "api_keys": {key.provider: key for key in user.api_keys},
            "bot": user.owned_bots[0] if user.owned_bots else None,
            "conversation": user.conversation_sessions[0] if user.conversation_sessions else None,
            "messages": user.conversation_sessions[0].messages if user.conversation_sessions and user.conversation_sessions[0].messages else []
        }
    finally:
        db.close()


@pytest.fixture(scope="function")
def sample_user(db_session):
    """Create a sample user for testing."""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        username="sampleuser",
        email="sample@example.com",
        password_hash=get_password_hash("samplepassword"),
        full_name="Sample User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_bot(db_session, sample_user):
    """Create a sample bot for testing."""
    from app.models.bot import Bot
    
    bot = Bot(
        name="Sample Bot",
        description="A sample bot for testing",
        system_prompt="You are a helpful assistant",
        owner_id=sample_user.id,
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=1000
    )
    db_session.add(bot)
    db_session.commit()
    db_session.refresh(bot)
    return bot


@pytest.fixture(scope="function")
def sample_bot_with_permission(db_session, sample_user, sample_bot):
    """Create a sample bot with owner permission for testing."""
    from app.models.bot import BotPermission
    
    # Create owner permission
    owner_permission = BotPermission(
        bot_id=sample_bot.id,
        user_id=sample_user.id,
        role="owner",
        granted_by=sample_user.id
    )
    db_session.add(owner_permission)
    db_session.commit()
    
    return sample_bot


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """Create authentication headers for test requests."""
    # Login to get token
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def sample_auth_headers(client, sample_user):
    """Create authentication headers for sample user test requests."""
    # Login to get token
    login_data = {
        "username": "sampleuser",
        "password": "samplepassword"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def sample_session(db_session, sample_user, sample_bot_with_permission):
    """Create a sample conversation session for testing."""
    from app.models.conversation import ConversationSession
    
    session = ConversationSession(
        bot_id=sample_bot_with_permission.id,
        user_id=sample_user.id,
        title="Sample Session",
        is_shared=False
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session