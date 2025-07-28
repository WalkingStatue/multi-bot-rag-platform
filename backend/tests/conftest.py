"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from sqlalchemy import create_engine
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
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@postgres-test:5432/multi_bot_rag_test"
else:
    # Local environment - use localhost with mapped port
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5434/multi_bot_rag_test"

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


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


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