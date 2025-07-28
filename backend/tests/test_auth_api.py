"""
Integration tests for authentication API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from main import app
from app.models.user import User
from app.core.security import get_password_hash


class TestAuthAPI:
    """Test cases for authentication API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    @patch('app.api.auth.get_auth_service')
    def test_register_success(self, mock_get_service):
        """Test successful user registration."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        created_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_active=True
        )
        mock_service.register_user.return_value = created_user
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        
        # Act
        response = self.client.post("/api/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "password" not in data
        mock_service.register_user.assert_called_once()
    
    @patch('app.api.auth.get_auth_service')
    def test_register_validation_error(self, mock_get_service):
        """Test registration with validation errors."""
        # Arrange
        invalid_data = {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid email
            "password": "123"  # Too short
        }
        
        # Act
        response = self.client.post("/api/auth/register", json=invalid_data)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @patch('app.api.auth.get_auth_service')
    def test_login_success(self, mock_get_service):
        """Test successful user login."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        user = User(username="testuser", email="test@example.com")
        tokens = {
            "access_token": "access_token_value",
            "refresh_token": "refresh_token_value",
            "token_type": "bearer"
        }
        mock_service.authenticate_user.return_value = (user, tokens)
        
        credentials = {
            "username": "testuser",
            "password": "password123"
        }
        
        # Act
        response = self.client.post("/api/auth/login", json=credentials)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token_value"
        assert data["refresh_token"] == "refresh_token_value"
        assert data["token_type"] == "bearer"
        mock_service.authenticate_user.assert_called_once()
    
    @patch('app.api.auth.get_auth_service')
    def test_login_invalid_credentials(self, mock_get_service):
        """Test login with invalid credentials."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        from fastapi import HTTPException
        mock_service.authenticate_user.side_effect = HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
        
        credentials = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        # Act
        response = self.client.post("/api/auth/login", json=credentials)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "Incorrect username or password" in data["detail"]
    
    @patch('app.api.auth.get_auth_service')
    def test_refresh_token_success(self, mock_get_service):
        """Test successful token refresh."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        from app.schemas.user import Token
        new_tokens = Token(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            token_type="bearer"
        )
        mock_service.refresh_token.return_value = new_tokens
        
        refresh_data = {
            "refresh_token": "valid_refresh_token"
        }
        
        # Act
        response = self.client.post("/api/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"
        mock_service.refresh_token.assert_called_once_with("valid_refresh_token")
    
    @patch('app.api.auth.get_auth_service')
    def test_refresh_token_invalid(self, mock_get_service):
        """Test token refresh with invalid token."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        from fastapi import HTTPException
        mock_service.refresh_token.side_effect = HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )
        
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        
        # Act
        response = self.client.post("/api/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "Invalid refresh token" in data["detail"]
    
    @patch('app.api.auth.get_auth_service')
    def test_forgot_password_success(self, mock_get_service):
        """Test successful password reset request."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_service.request_password_reset.return_value = "reset_token_123"
        
        reset_request = {
            "email": "test@example.com"
        }
        
        # Act
        response = self.client.post("/api/auth/forgot-password", json=reset_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Password reset token generated" in data["message"]
        assert data["reset_token"] == "reset_token_123"
        mock_service.request_password_reset.assert_called_once_with("test@example.com")
    
    @patch('app.api.auth.get_auth_service')
    def test_forgot_password_user_not_found(self, mock_get_service):
        """Test password reset request for non-existent user."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        from fastapi import HTTPException
        mock_service.request_password_reset.side_effect = HTTPException(
            status_code=404,
            detail="User with this email not found"
        )
        
        reset_request = {
            "email": "nonexistent@example.com"
        }
        
        # Act
        response = self.client.post("/api/auth/forgot-password", json=reset_request)
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "User with this email not found" in data["detail"]
    
    @patch('app.api.auth.get_auth_service')
    def test_reset_password_success(self, mock_get_service):
        """Test successful password reset."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_service.reset_password.return_value = True
        
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "newpassword123"
        }
        
        # Act
        response = self.client.post("/api/auth/reset-password", json=reset_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Password reset successfully" in data["message"]
        mock_service.reset_password.assert_called_once()
    
    @patch('app.api.auth.get_auth_service')
    def test_reset_password_invalid_token(self, mock_get_service):
        """Test password reset with invalid token."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        from fastapi import HTTPException
        mock_service.reset_password.side_effect = HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
        
        reset_data = {
            "token": "invalid_token",
            "new_password": "newpassword123"
        }
        
        # Act
        response = self.client.post("/api/auth/reset-password", json=reset_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired reset token" in data["detail"]
    
    def test_change_password_not_implemented(self):
        """Test change password endpoint returns not implemented."""
        # Arrange
        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123"
        }
        
        # Act
        response = self.client.post("/api/auth/change-password", json=password_data)
        
        # Assert
        assert response.status_code == 501
        data = response.json()
        assert "Change password requires authentication" in data["detail"]
    
    def test_logout_success(self):
        """Test logout endpoint."""
        # Act
        response = self.client.post("/api/auth/logout")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Logged out successfully" in data["message"]