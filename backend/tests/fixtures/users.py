"""
User test fixtures and factories.
"""
from typing import Dict, Any
from app.models.user import User
from app.core.security import get_password_hash


class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "testpassword",
        full_name: str = "Test User",
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create user data dictionary."""
        return {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "is_active": is_active
        }
    
    @staticmethod
    def create_user(
        db_session,
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "testpassword",
        full_name: str = "Test User",
        is_active: bool = True
    ) -> User:
        """Create a user in the database."""
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            is_active=is_active
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @staticmethod
    def create_multiple_users(db_session, count: int = 3):
        """Create multiple test users."""
        users = []
        for i in range(count):
            user = UserFactory.create_user(
                db_session,
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}"
            )
            users.append(user)
        return users


# Common user data
SAMPLE_USERS = [
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "alicepassword",
        "full_name": "Alice Johnson",
        "is_active": True
    },
    {
        "username": "bob",
        "email": "bob@example.com",
        "password": "bobpassword",
        "full_name": "Bob Smith",
        "is_active": True
    },
    {
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "charliepassword",
        "full_name": "Charlie Brown",
        "is_active": False
    }
]