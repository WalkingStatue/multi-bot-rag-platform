"""
Integration tests for user management API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from main import app
from app.models.user import User


class TestUsersAPI:
    """Test cases for user management API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.mock_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_active=True
        )
    
    @patch('app.api.users.get_current_active_user')
    def test_get_profile_success(self, mock_get_user):
        """Test successful profile retrieval."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        
        # Act
        response = self.client.get(
            "/api/users/profile",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
    
    def test_get_profile_unauthorized(self):
        """Test profile retrieval without authentication."""
        # Act
        response = self.client.get("/api/users/profile")
        
        # Assert
        assert response.status_code == 403
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_update_profile_success(self, mock_get_service, mock_get_user):
        """Test successful profile update."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        updated_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="testuser",
            email="test@example.com",
            full_name="Updated Name",
            is_active=True
        )
        mock_service.update_user_profile.return_value = updated_user
        
        update_data = {
            "full_name": "Updated Name",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        
        # Act
        response = self.client.put(
            "/api/users/profile",
            json=update_data,
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        mock_service.update_user_profile.assert_called_once()
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.core.dependencies.get_db')
    def test_change_password_success(self, mock_get_db, mock_get_user):
        """Test successful password change."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123"
        }
        
        with patch('app.services.auth_service.AuthService') as mock_auth_service:
            mock_service_instance = Mock()
            mock_auth_service.return_value = mock_service_instance
            mock_service_instance.change_password.return_value = True
            
            # Act
            response = self.client.post(
                "/api/users/change-password",
                json=password_data,
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "Password changed successfully" in data["message"]
            mock_service_instance.change_password.assert_called_once()
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_search_users_success(self, mock_get_service, mock_get_user):
        """Test successful user search."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        search_results = [
            {
                "id": "user1",
                "username": "testuser1",
                "full_name": "Test User 1",
                "avatar_url": None
            },
            {
                "id": "user2",
                "username": "testuser2",
                "full_name": "Test User 2",
                "avatar_url": None
            }
        ]
        mock_service.search_users.return_value = search_results
        
        # Act
        response = self.client.get(
            "/api/users/search?q=test&limit=10",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["username"] == "testuser1"
        assert data[1]["username"] == "testuser2"
        mock_service.search_users.assert_called_once_with("test", 10)
    
    @patch('app.api.users.get_current_active_user')
    def test_search_users_invalid_query(self, mock_get_user):
        """Test user search with invalid query."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        
        # Act
        response = self.client.get(
            "/api/users/search?q=a",  # Too short
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 422
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_get_api_keys_success(self, mock_get_service, mock_get_user):
        """Test successful API keys retrieval."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        api_keys = [
            {
                "id": "key1",
                "provider": "openai",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": "key2",
                "provider": "anthropic",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        mock_service.get_user_api_keys.return_value = api_keys
        
        # Act
        response = self.client.get(
            "/api/users/api-keys",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["provider"] == "openai"
        assert data[1]["provider"] == "anthropic"
        mock_service.get_user_api_keys.assert_called_once_with(self.mock_user)
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_add_api_key_success(self, mock_get_service, mock_get_user):
        """Test successful API key addition."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        created_key = {
            "id": "key1",
            "provider": "openai",
            "is_active": True,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        mock_service.add_api_key.return_value = created_key
        
        api_key_data = {
            "provider": "openai",
            "api_key": "sk-test123456789abcdef"
        }
        
        # Act
        response = self.client.post(
            "/api/users/api-keys",
            json=api_key_data,
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "openai"
        assert data["is_active"] is True
        mock_service.add_api_key.assert_called_once()
    
    @patch('app.api.users.get_current_active_user')
    def test_add_api_key_invalid_provider(self, mock_get_user):
        """Test API key addition with invalid provider."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        
        api_key_data = {
            "provider": "invalid_provider",
            "api_key": "sk-test123456789abcdef"
        }
        
        # Act
        response = self.client.post(
            "/api/users/api-keys",
            json=api_key_data,
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 422
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_update_api_key_success(self, mock_get_service, mock_get_user):
        """Test successful API key update."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        updated_key = {
            "id": "key1",
            "provider": "openai",
            "is_active": True,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        mock_service.update_api_key.return_value = updated_key
        
        api_key_data = {
            "api_key": "sk-new123456789abcdef",
            "is_active": True
        }
        
        # Act
        response = self.client.put(
            "/api/users/api-keys/openai",
            json=api_key_data,
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        mock_service.update_api_key.assert_called_once()
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_update_api_key_not_found(self, mock_get_service, mock_get_user):
        """Test API key update when key not found."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        from fastapi import HTTPException
        mock_service.update_api_key.side_effect = HTTPException(
            status_code=404,
            detail="API key not found for this provider"
        )
        
        api_key_data = {
            "api_key": "sk-new123456789abcdef"
        }
        
        # Act
        response = self.client.put(
            "/api/users/api-keys/openai",
            json=api_key_data,
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "API key not found" in data["detail"]
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_delete_api_key_success(self, mock_get_service, mock_get_user):
        """Test successful API key deletion."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_service.delete_api_key.return_value = True
        
        # Act
        response = self.client.delete(
            "/api/users/api-keys/openai",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 204
        mock_service.delete_api_key.assert_called_once_with(self.mock_user, "openai")
    
    @patch('app.api.users.get_current_active_user')
    @patch('app.api.users.get_user_service')
    def test_delete_api_key_not_found(self, mock_get_service, mock_get_user):
        """Test API key deletion when key not found."""
        # Arrange
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        from fastapi import HTTPException
        mock_service.delete_api_key.side_effect = HTTPException(
            status_code=404,
            detail="API key not found for this provider"
        )
        
        # Act
        response = self.client.delete(
            "/api/users/api-keys/openai",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "API key not found" in data["detail"]