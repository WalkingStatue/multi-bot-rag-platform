"""
Unit tests for authentication service.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, PasswordResetConfirm
from app.core.security import get_password_hash, verify_password


class TestAuthService:
    """Test cases for AuthService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.auth_service = AuthService(self.mock_db)
    
    def test_register_user_success(self):
        """Test successful user registration."""
        # Arrange
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock user creation
        created_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed_password",
            is_active=True
        )
        
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('app.services.auth_service.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            # Act
            result = self.auth_service.register_user(user_data)
            
            # Assert
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
            mock_hash.assert_called_once_with("password123")
    
    def test_register_user_username_exists(self):
        """Test registration with existing username."""
        # Arrange
        user_data = UserCreate(
            username="existinguser",
            email="test@example.com",
            password="password123"
        )
        
        existing_user = User(username="existinguser", email="other@example.com")
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "Username already registered" in str(exc_info.value.detail)
    
    def test_register_user_email_exists(self):
        """Test registration with existing email."""
        # Arrange
        user_data = UserCreate(
            username="testuser",
            email="existing@example.com",
            password="password123"
        )
        
        existing_user = User(username="otheruser", email="existing@example.com")
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Arrange
        credentials = UserLogin(username="testuser", password="password123")
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            is_active=True
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        with patch('app.services.auth_service.verify_password') as mock_verify, \
             patch('app.services.auth_service.create_access_token') as mock_access, \
             patch('app.services.auth_service.create_refresh_token') as mock_refresh:
            
            mock_verify.return_value = True
            mock_access.return_value = "access_token"
            mock_refresh.return_value = "refresh_token"
            
            # Act
            result_user, tokens = self.auth_service.authenticate_user(credentials)
            
            # Assert
            assert result_user == user
            assert tokens.access_token == "access_token"
            assert tokens.refresh_token == "refresh_token"
            assert tokens.token_type == "bearer"
    
    def test_authenticate_user_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        # Arrange
        credentials = UserLogin(username="testuser", password="wrongpassword")
        
        user = User(
            username="testuser",
            password_hash=get_password_hash("password123"),
            is_active=True
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        with patch('app.services.auth_service.verify_password') as mock_verify:
            mock_verify.return_value = False
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                self.auth_service.authenticate_user(credentials)
            
            assert exc_info.value.status_code == 401
            assert "Incorrect username or password" in str(exc_info.value.detail)
    
    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user."""
        # Arrange
        credentials = UserLogin(username="nonexistent", password="password123")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.authenticate_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect username or password" in str(exc_info.value.detail)
    
    def test_authenticate_user_inactive(self):
        """Test authentication with inactive user."""
        # Arrange
        credentials = UserLogin(username="testuser", password="password123")
        
        user = User(
            username="testuser",
            password_hash=get_password_hash("password123"),
            is_active=False
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        with patch('app.services.auth_service.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                self.auth_service.authenticate_user(credentials)
            
            assert exc_info.value.status_code == 400
            assert "Inactive user" in str(exc_info.value.detail)
    
    def test_refresh_token_success(self):
        """Test successful token refresh."""
        # Arrange
        refresh_token = "valid_refresh_token"
        
        user = User(username="testuser", is_active=True)
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        with patch('app.services.auth_service.verify_token') as mock_verify, \
             patch('app.services.auth_service.create_access_token') as mock_access, \
             patch('app.services.auth_service.create_refresh_token') as mock_refresh:
            
            mock_verify.return_value = {"sub": "testuser", "type": "refresh"}
            mock_access.return_value = "new_access_token"
            mock_refresh.return_value = "new_refresh_token"
            
            # Act
            tokens = self.auth_service.refresh_token(refresh_token)
            
            # Assert
            assert tokens.access_token == "new_access_token"
            assert tokens.refresh_token == "new_refresh_token"
            assert tokens.token_type == "bearer"
    
    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        # Arrange
        refresh_token = "invalid_refresh_token"
        
        with patch('app.services.auth_service.verify_token') as mock_verify:
            mock_verify.return_value = None
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                self.auth_service.refresh_token(refresh_token)
            
            assert exc_info.value.status_code == 401
            assert "Invalid refresh token" in str(exc_info.value.detail)
    
    def test_get_current_user_success(self):
        """Test successful current user retrieval."""
        # Arrange
        token = "valid_access_token"
        
        user = User(username="testuser", is_active=True)
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        with patch('app.services.auth_service.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "testuser", "type": "access"}
            
            # Act
            result = self.auth_service.get_current_user(token)
            
            # Assert
            assert result == user
    
    def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        # Arrange
        token = "invalid_token"
        
        with patch('app.services.auth_service.verify_token') as mock_verify:
            mock_verify.return_value = None
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                self.auth_service.get_current_user(token)
            
            assert exc_info.value.status_code == 401
            assert "Could not validate credentials" in str(exc_info.value.detail)
    
    def test_request_password_reset_success(self):
        """Test successful password reset request."""
        # Arrange
        email = "test@example.com"
        
        user = User(email=email, is_active=True)
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        
        with patch('app.services.auth_service.create_password_reset_token') as mock_token:
            mock_token.return_value = "reset_token"
            
            # Act
            result = self.auth_service.request_password_reset(email)
            
            # Assert
            assert result == "reset_token"
            mock_token.assert_called_once_with(email)
    
    def test_request_password_reset_user_not_found(self):
        """Test password reset request for non-existent user."""
        # Arrange
        email = "nonexistent@example.com"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.request_password_reset(email)
        
        assert exc_info.value.status_code == 404
        assert "User with this email not found" in str(exc_info.value.detail)
    
    def test_reset_password_success(self):
        """Test successful password reset."""
        # Arrange
        reset_data = PasswordResetConfirm(
            token="valid_reset_token",
            new_password="newpassword123"
        )
        
        user = User(email="test@example.com")
        self.mock_db.query.return_value.filter.return_value.first.return_value = user
        self.mock_db.commit = Mock()
        
        with patch('app.services.auth_service.verify_password_reset_token') as mock_verify, \
             patch('app.services.auth_service.get_password_hash') as mock_hash:
            
            mock_verify.return_value = "test@example.com"
            mock_hash.return_value = "hashed_new_password"
            
            # Act
            result = self.auth_service.reset_password(reset_data)
            
            # Assert
            assert result is True
            assert user.password_hash == "hashed_new_password"
            self.mock_db.commit.assert_called_once()
    
    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token."""
        # Arrange
        reset_data = PasswordResetConfirm(
            token="invalid_token",
            new_password="newpassword123"
        )
        
        with patch('app.services.auth_service.verify_password_reset_token') as mock_verify:
            mock_verify.return_value = None
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                self.auth_service.reset_password(reset_data)
            
            assert exc_info.value.status_code == 400
            assert "Invalid or expired reset token" in str(exc_info.value.detail)
    
    def test_change_password_success(self):
        """Test successful password change."""
        # Arrange
        user = User(password_hash=get_password_hash("oldpassword"))
        current_password = "oldpassword"
        new_password = "newpassword123"
        
        self.mock_db.commit = Mock()
        
        with patch('app.services.auth_service.verify_password') as mock_verify, \
             patch('app.services.auth_service.get_password_hash') as mock_hash:
            
            mock_verify.return_value = True
            mock_hash.return_value = "hashed_new_password"
            
            # Act
            result = self.auth_service.change_password(user, current_password, new_password)
            
            # Assert
            assert result is True
            assert user.password_hash == "hashed_new_password"
            self.mock_db.commit.assert_called_once()
    
    def test_change_password_incorrect_current(self):
        """Test password change with incorrect current password."""
        # Arrange
        user = User(password_hash=get_password_hash("oldpassword"))
        current_password = "wrongpassword"
        new_password = "newpassword123"
        
        with patch('app.services.auth_service.verify_password') as mock_verify:
            mock_verify.return_value = False
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                self.auth_service.change_password(user, current_password, new_password)
            
            assert exc_info.value.status_code == 400
            assert "Incorrect current password" in str(exc_info.value.detail)