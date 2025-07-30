"""
Authentication helper utilities for testing.
"""
import uuid
from contextlib import contextmanager
from unittest.mock import patch, Mock
from datetime import datetime
from typing import Optional

from app.models.user import User
from app.core.dependencies import get_current_user, get_current_active_user


def create_mock_user(
    user_id: Optional[str] = None,
    username: str = "testuser",
    email: str = "test@example.com",
    full_name: str = "Test User",
    is_active: bool = True,
    persist_to_db: bool = False,
    db_session = None
) -> User:
    """
    Create a mock user for testing.
    
    Args:
        user_id: User ID (generates UUID if not provided)
        username: Username
        email: Email address
        full_name: Full name
        is_active: Whether user is active
        persist_to_db: Whether to persist the user to the database
        db_session: Database session for persistence
        
    Returns:
        Mock User object
    """
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    user = User(
        id=user_id,
        username=username,
        email=email,
        full_name=full_name,
        is_active=is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Persist to database if requested
    if persist_to_db and db_session:
        from app.core.security import get_password_hash
        user.password_hash = get_password_hash("testpassword")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    return user


@contextmanager
def mock_authentication(user: User, mock_permissions: bool = True):
    """
    Context manager to mock authentication for a specific user.
    
    Args:
        user: User object to authenticate as
        mock_permissions: Whether to also mock permission checks
        
    Yields:
        The user object
    """
    from main import app
    from app.core.dependencies import get_current_user, get_current_active_user
    
    def mock_get_current_user():
        return user
    
    def mock_get_current_active_user():
        return user
    
    # Override FastAPI dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    
    # Optionally mock permission service to always return True
    permission_patch = None
    if mock_permissions:
        permission_patch = patch('app.services.permission_service.PermissionService.check_bot_permission', return_value=True)
        permission_patch.start()
    
    try:
        yield user
    finally:
        # Clean up dependency overrides
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        if get_current_active_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_active_user]
        
        # Clean up permission mock
        if permission_patch:
            permission_patch.stop()


@contextmanager
def mock_authentication_with_db(user: User, db_session, bot_id: str = None, role: str = "owner"):
    """
    Context manager to mock authentication with database persistence.
    
    Args:
        user: User object to authenticate as
        db_session: Database session for persistence
        bot_id: Bot ID to create permission for
        role: Role to assign to user for the bot
        
    Yields:
        The user object
    """
    from main import app
    from app.core.dependencies import get_current_user, get_current_active_user
    from app.models.bot import BotPermission
    from app.core.security import get_password_hash
    
    # Ensure user exists in database
    if not hasattr(user, 'password_hash') or not user.password_hash:
        user.password_hash = get_password_hash("testpassword")
    
    # Check if user already exists in database
    existing_user = db_session.query(User).filter(User.id == user.id).first()
    if not existing_user:
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    # Create bot permission if bot_id is provided
    if bot_id:
        existing_permission = db_session.query(BotPermission).filter(
            BotPermission.user_id == user.id,
            BotPermission.bot_id == bot_id
        ).first()
        
        if not existing_permission:
            permission = BotPermission(
                bot_id=bot_id,
                user_id=user.id,
                role=role,
                granted_by=user.id
            )
            db_session.add(permission)
            db_session.commit()
    
    def mock_get_current_user():
        return user
    
    def mock_get_current_active_user():
        return user
    
    # Override FastAPI dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    
    try:
        yield user
    finally:
        # Clean up dependency overrides
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        if get_current_active_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_active_user]


class AuthTestHelper:
    """Helper class for authentication testing."""
    
    def __init__(self, client):
        """
        Initialize auth test helper.
        
        Args:
            client: FastAPI test client
        """
        self.client = client
    
    def login_user(self, username: str = "testuser", password: str = "testpassword") -> dict:
        """
        Login a user and return authentication headers.
        
        Args:
            username: Username to login with
            password: Password to login with
            
        Returns:
            Dictionary with Authorization header
        """
        login_data = {
            "username": username,
            "password": password
        }
        response = self.client.post("/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            return {"Authorization": f"Bearer {access_token}"}
        else:
            raise Exception(f"Login failed with status {response.status_code}: {response.text}")
    
    def create_authenticated_headers(self, user: User) -> dict:
        """
        Create authentication headers for a user without actual login.
        
        Args:
            user: User to create headers for
            
        Returns:
            Dictionary with Authorization header
        """
        # For testing, we'll use a mock token
        return {"Authorization": f"Bearer mock_token_{user.username}"}
    
    @contextmanager
    def authenticate_as(self, user: User):
        """
        Context manager to authenticate as a specific user.
        
        Args:
            user: User to authenticate as
            
        Yields:
            Authentication headers
        """
        from main import app
        from app.core.dependencies import get_current_user, get_current_active_user
        
        def mock_get_current_user():
            return user
        
        def mock_get_current_active_user():
            return user
        
        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        
        try:
            headers = self.create_authenticated_headers(user)
            yield headers
        finally:
            # Clean up dependency overrides
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]
            if get_current_active_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_active_user]
    
    def mock_current_user(self, user: User):
        """
        Mock the current user dependency.
        
        Args:
            user: User to mock as current user
            
        Returns:
            Mock patch object
        """
        return patch('app.core.dependencies.get_current_user', return_value=user)
    
    def mock_current_active_user(self, user: User):
        """
        Mock the current active user dependency.
        
        Args:
            user: User to mock as current active user
            
        Returns:
            Mock patch object
        """
        return patch('app.core.dependencies.get_current_active_user', return_value=user)