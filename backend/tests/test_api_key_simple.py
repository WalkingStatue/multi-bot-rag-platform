"""
Simple tests for API key management functionality.
"""
import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserAPIKey
from app.schemas.user import APIKeyCreate
from app.services.user_service import UserService
from app.utils.encryption import encrypt_api_key, decrypt_api_key


class TestAPIKeyBasics:
    """Basic tests for API key management."""
    
    def test_add_api_key_basic(self, db_session: Session, test_user: User):
        """Test basic API key addition."""
        # Arrange
        user_service = UserService(db_session)
        api_key_data = APIKeyCreate(provider="openai", api_key="sk-test123456789")
        
        # Act
        result = user_service.add_api_key(test_user, api_key_data)
        
        # Assert
        assert result.provider == "openai"
        assert result.is_active is True
        assert result.id is not None
        
        # Verify in database
        db_api_key = db_session.query(UserAPIKey).filter(
            UserAPIKey.user_id == test_user.id,
            UserAPIKey.provider == "openai"
        ).first()
        assert db_api_key is not None
        assert decrypt_api_key(db_api_key.api_key_encrypted) == "sk-test123456789"
    
    def test_get_api_key_basic(self, db_session: Session, test_user: User):
        """Test basic API key retrieval."""
        # Arrange
        user_service = UserService(db_session)
        api_key_data = APIKeyCreate(provider="openai", api_key="sk-secret123")
        user_service.add_api_key(test_user, api_key_data)
        
        # Act
        result = user_service.get_api_key(test_user, "openai")
        
        # Assert
        assert result == "sk-secret123"
    
    def test_delete_api_key_basic(self, db_session: Session, test_user: User):
        """Test basic API key deletion."""
        # Arrange
        user_service = UserService(db_session)
        api_key_data = APIKeyCreate(provider="openai", api_key="sk-test123")
        user_service.add_api_key(test_user, api_key_data)
        
        # Act
        result = user_service.delete_api_key(test_user, "openai")
        
        # Assert
        assert result is True
        
        # Verify deletion
        db_api_key = db_session.query(UserAPIKey).filter(
            UserAPIKey.user_id == test_user.id,
            UserAPIKey.provider == "openai"
        ).first()
        assert db_api_key is None