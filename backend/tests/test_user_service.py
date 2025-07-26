"""
Unit tests for user service.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.user_service import UserService
from app.models.user import User, UserAPIKey
from app.schemas.user import UserUpdate, APIKeyCreate, APIKeyUpdate


class TestUserService:
    """Test cases for UserService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.user_service = UserService(self.mock_db)
    
    def test_get_user_profile_success(self):
        """Test successful user profile retrieval."""
        # Arrange
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        user = User(id=user_id, username="testuser", email="test@example.com")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        # Act
        result = self.user_service.get_user_profile(user_id)
        
        # Assert
        assert result == user
    
    def test_get_user_profile_not_found(self):
        """Test user profile retrieval for non-existent user."""
        # Arrange
        user_id = "nonexistent-id"
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.user_service.get_user_profile(user_id)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    def test_update_user_profile_success(self):
        """Test successful user profile update."""
        # Arrange
        user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="testuser",
            email="test@example.com",
            full_name="Old Name"
        )
        
        updates = UserUpdate(
            full_name="New Name",
            avatar_url="https://example.com/avatar.jpg"
        )
        
        # Mock no conflicts
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Act
        result = self.user_service.update_user_profile(user, updates)
        
        # Assert
        assert user.full_name == "New Name"
        assert user.avatar_url == "https://example.com/avatar.jpg"
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(user)
    
    def test_update_user_profile_username_conflict(self):
        """Test profile update with conflicting username."""
        # Arrange
        user = User(id="user1", username="testuser", email="test@example.com")
        updates = UserUpdate(username="existinguser")
        
        # Mock existing user with same username
        existing_user = User(id="user2", username="existinguser")
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.user_service.update_user_profile(user, updates)
        
        assert exc_info.value.status_code == 400
        assert "Username already taken" in str(exc_info.value.detail)
    
    def test_update_user_profile_email_conflict(self):
        """Test profile update with conflicting email."""
        # Arrange
        user = User(id="user1", username="testuser", email="test@example.com")
        updates = UserUpdate(email="existing@example.com")
        
        # Mock existing user with same email
        existing_user = User(id="user2", email="existing@example.com")
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.user_service.update_user_profile(user, updates)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    def test_search_users_success(self):
        """Test successful user search."""
        # Arrange
        query = "test"
        users = [
            User(id="123e4567-e89b-12d3-a456-426614174001", username="testuser1", full_name="Test User 1"),
            User(id="123e4567-e89b-12d3-a456-426614174002", username="testuser2", full_name="Test User 2")
        ]
        
        self.mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = users
        
        # Act
        results = self.user_service.search_users(query)
        
        # Assert
        assert len(results) == 2
        assert results[0].username == "testuser1"
        assert results[1].username == "testuser2"
    
    def test_search_users_empty_query(self):
        """Test user search with empty query."""
        # Arrange
        query = ""
        
        # Act
        results = self.user_service.search_users(query)
        
        # Assert
        assert results == []
    
    def test_search_users_short_query(self):
        """Test user search with too short query."""
        # Arrange
        query = "a"
        
        # Act
        results = self.user_service.search_users(query)
        
        # Assert
        assert results == []
    
    def test_get_user_by_username_success(self):
        """Test successful user retrieval by username."""
        # Arrange
        username = "testuser"
        user = User(username=username, email="test@example.com")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        # Act
        result = self.user_service.get_user_by_username(username)
        
        # Assert
        assert result == user
    
    def test_get_user_by_username_not_found(self):
        """Test user retrieval by username when not found."""
        # Arrange
        username = "nonexistent"
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.user_service.get_user_by_username(username)
        
        # Assert
        assert result is None
    
    def test_get_user_by_email_success(self):
        """Test successful user retrieval by email."""
        # Arrange
        email = "test@example.com"
        user = User(username="testuser", email=email)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        # Act
        result = self.user_service.get_user_by_email(email)
        
        # Assert
        assert result == user
    
    def test_get_user_by_email_not_found(self):
        """Test user retrieval by email when not found."""
        # Arrange
        email = "nonexistent@example.com"
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.user_service.get_user_by_email(email)
        
        # Assert
        assert result is None
    
    # API Key Management Tests
    
    def test_add_api_key_new(self):
        """Test adding new API key."""
        # Arrange
        user = User(id="123e4567-e89b-12d3-a456-426614174000", username="testuser")
        api_key_data = APIKeyCreate(provider="openai", api_key="sk-test123456789abcdef")
        
        # Mock no existing key
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('app.services.user_service.encrypt_api_key') as mock_encrypt, \
             patch('app.services.user_service.APIKeyResponse') as mock_response:
            
            mock_encrypt.return_value = "encrypted_key"
            mock_response.model_validate.return_value = {"id": "key1", "provider": "openai"}
            
            # Act
            result = self.user_service.add_api_key(user, api_key_data)
            
            # Assert
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
            mock_encrypt.assert_called_once_with("sk-test123456789abcdef")
    
    def test_add_api_key_update_existing(self):
        """Test updating existing API key."""
        # Arrange
        user = User(id="123e4567-e89b-12d3-a456-426614174000", username="testuser")
        api_key_data = APIKeyCreate(provider="openai", api_key="sk-test456789abcdef")
        
        existing_key = UserAPIKey(
            user_id="user1",
            provider="openai",
            api_key_encrypted="old_encrypted_key"
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_key
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('app.services.user_service.encrypt_api_key') as mock_encrypt, \
             patch('app.services.user_service.APIKeyResponse') as mock_response:
            
            mock_encrypt.return_value = "new_encrypted_key"
            mock_response.model_validate.return_value = {"id": "key1", "provider": "openai"}
            
            # Act
            result = self.user_service.add_api_key(user, api_key_data)
            
            # Assert
            assert existing_key.api_key_encrypted == "new_encrypted_key"
            assert existing_key.is_active is True
            self.mock_db.commit.assert_called_once()
            mock_encrypt.assert_called_once_with("sk-test456789abcdef")
    
    def test_get_user_api_keys(self):
        """Test retrieving user's API keys."""
        # Arrange
        user = User(id="123e4567-e89b-12d3-a456-426614174000", username="testuser")
        api_keys = [
            UserAPIKey(id="123e4567-e89b-12d3-a456-426614174001", provider="openai", is_active=True, created_at="2023-01-01T00:00:00", updated_at="2023-01-01T00:00:00"),
            UserAPIKey(id="123e4567-e89b-12d3-a456-426614174002", provider="anthropic", is_active=True, created_at="2023-01-01T00:00:00", updated_at="2023-01-01T00:00:00")
        ]
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = api_keys
        
        with patch('app.services.user_service.APIKeyResponse') as mock_response:
            mock_response.model_validate.side_effect = [
                {"id": "key1", "provider": "openai"},
                {"id": "key2", "provider": "anthropic"}
            ]
            
            # Act
            results = self.user_service.get_user_api_keys(user)
            
            # Assert
            assert len(results) == 2
    
    def test_get_api_key_success(self):
        """Test successful API key retrieval."""
        # Arrange
        user = User(id="user1", username="testuser")
        provider = "openai"
        
        api_key = UserAPIKey(
            user_id="user1",
            provider="openai",
            api_key_encrypted="encrypted_key",
            is_active=True
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = api_key
        
        with patch('app.services.user_service.decrypt_api_key') as mock_decrypt:
            mock_decrypt.return_value = "sk-test123"
            
            # Act
            result = self.user_service.get_api_key(user, provider)
            
            # Assert
            assert result == "sk-test123"
            mock_decrypt.assert_called_once_with("encrypted_key")
    
    def test_get_api_key_not_found(self):
        """Test API key retrieval when not found."""
        # Arrange
        user = User(id="user1", username="testuser")
        provider = "openai"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.user_service.get_api_key(user, provider)
        
        # Assert
        assert result is None
    
    def test_get_api_key_decryption_error(self):
        """Test API key retrieval with decryption error."""
        # Arrange
        user = User(id="user1", username="testuser")
        provider = "openai"
        
        api_key = UserAPIKey(
            user_id="user1",
            provider="openai",
            api_key_encrypted="corrupted_key",
            is_active=True
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = api_key
        
        with patch('app.services.user_service.decrypt_api_key') as mock_decrypt:
            mock_decrypt.side_effect = Exception("Decryption failed")
            
            # Act
            result = self.user_service.get_api_key(user, provider)
            
            # Assert
            assert result is None
    
    def test_update_api_key_success(self):
        """Test successful API key update."""
        # Arrange
        user = User(id="user1", username="testuser")
        provider = "openai"
        api_key_data = APIKeyUpdate(api_key="sk-new123456789abcdef", is_active=True)
        
        existing_key = UserAPIKey(
            user_id="user1",
            provider="openai",
            api_key_encrypted="old_encrypted_key"
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_key
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('app.services.user_service.encrypt_api_key') as mock_encrypt:
            mock_encrypt.return_value = "new_encrypted_key"
            
            # Act
            result = self.user_service.update_api_key(user, provider, api_key_data)
            
            # Assert
            assert existing_key.api_key_encrypted == "new_encrypted_key"
            assert existing_key.is_active is True
            self.mock_db.commit.assert_called_once()
    
    def test_update_api_key_not_found(self):
        """Test API key update when key not found."""
        # Arrange
        user = User(id="user1", username="testuser")
        provider = "openai"
        api_key_data = APIKeyUpdate(api_key="sk-new123456789abcdef")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.user_service.update_api_key(user, provider, api_key_data)
        
        assert exc_info.value.status_code == 404
        assert "API key not found" in str(exc_info.value.detail)
    
    def test_delete_api_key_success(self):
        """Test successful API key deletion."""
        # Arrange
        user = User(id="user1", username="testuser")
        provider = "openai"
        
        api_key = UserAPIKey(user_id="user1", provider="openai")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = api_key
        self.mock_db.delete = Mock()
        self.mock_db.commit = Mock()
        
        # Act
        result = self.user_service.delete_api_key(user, provider)
        
        # Assert
        assert result is True
        self.mock_db.delete.assert_called_once_with(api_key)
        self.mock_db.commit.assert_called_once()
    
    def test_delete_api_key_not_found(self):
        """Test API key deletion when key not found."""
        # Arrange
        user = User(id="user1", username="testuser")
        provider = "openai"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.user_service.delete_api_key(user, provider)
        
        assert exc_info.value.status_code == 404
        assert "API key not found" in str(exc_info.value.detail)