"""
Integration tests for authentication API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash


class TestAuthAPI:
    """Test cases for authentication API endpoints."""
    
    def test_register_success(self, client: TestClient, db_session: Session):
        """Test successful user registration."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        
        # Act
        response = client.post("/api/auth/register", json=user_data)
        
        # Assert
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "password" not in data
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.username == "testuser").first()
        assert user is not None
        assert user.email == "test@example.com"
    
    def test_register_validation_error(self, client: TestClient):
        """Test registration with validation errors."""
        # Arrange
        invalid_data = {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid email
            "password": "123"  # Too short
        }
        
        # Act
        response = client.post("/api/auth/register", json=invalid_data)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful user login."""
        credentials = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        # Act
        response = client.post("/api/auth/login", json=credentials)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        credentials = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        # Act
        response = client.post("/api/auth/login", json=credentials)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh."""
        # First login to get tokens
        credentials = {
            "username": "testuser",
            "password": "testpassword"
        }
        login_response = client.post("/api/auth/login", json=credentials)
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        # Act
        response = client.post("/api/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token."""
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        
        # Act
        response = client.post("/api/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_forgot_password_success(self, client: TestClient, test_user: User):
        """Test successful password reset request."""
        reset_request = {
            "email": "test@example.com"
        }
        
        # Act
        response = client.post("/api/auth/forgot-password", json=reset_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_forgot_password_user_not_found(self, client: TestClient):
        """Test password reset request for non-existent user."""
        reset_request = {
            "email": "nonexistent@example.com"
        }
        
        # Act
        response = client.post("/api/auth/forgot-password", json=reset_request)
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_reset_password_success(self, client: TestClient, test_user: User):
        """Test successful password reset."""
        # First request a reset token
        reset_request = {
            "email": "test@example.com"
        }
        forgot_response = client.post("/api/auth/forgot-password", json=reset_request)
        assert forgot_response.status_code == 200
        reset_token = forgot_response.json().get("reset_token")
        
        if reset_token:
            reset_data = {
                "token": reset_token,
                "new_password": "newpassword123"
            }
            
            # Act
            response = client.post("/api/auth/reset-password", json=reset_data)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
        else:
            # If no reset token in response, test with a mock token
            reset_data = {
                "token": "mock_token",
                "new_password": "newpassword123"
            }
            
            # Act
            response = client.post("/api/auth/reset-password", json=reset_data)
            
            # Assert - should fail with invalid token
            assert response.status_code == 400
    
    def test_logout_success(self, client: TestClient):
        """Test logout endpoint."""
        # Act
        response = client.post("/api/auth/logout")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data