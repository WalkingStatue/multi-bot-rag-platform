"""
Integration tests for authentication API endpoints.
Tests the complete authentication flow with real database operations.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash, verify_password, verify_token


class TestAuthenticationIntegration:
    """Integration tests for authentication endpoints."""
    
    def test_user_registration_flow(self, client: TestClient, db_session: Session):
        """Test complete user registration flow."""
        # Test user registration
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "password" not in data
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert verify_password("password123", user.password_hash)
    
    def test_user_registration_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",  # Same as test_user
            "email": "different@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_user_registration_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email."""
        user_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Same as test_user
            "password": "password123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_user_registration_validation_errors(self, client: TestClient):
        """Test registration with validation errors."""
        # Test short username
        user_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
        
        # Test invalid email
        user_data = {
            "username": "validuser",
            "email": "invalid-email",  # Invalid format
            "password": "password123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
        
        # Test short password
        user_data = {
            "username": "validuser",
            "email": "valid@example.com",
            "password": "123"  # Too short
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_user_login_flow(self, client: TestClient, test_user: User):
        """Test complete user login flow."""
        # Test login with username
        credentials = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        response = client.post("/api/auth/login", json=credentials)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify tokens are valid
        access_payload = verify_token(data["access_token"], "access")
        refresh_payload = verify_token(data["refresh_token"], "refresh")
        
        assert access_payload is not None
        assert refresh_payload is not None
        assert access_payload["sub"] == "testuser"
        assert refresh_payload["sub"] == "testuser"
    
    def test_user_login_with_email(self, client: TestClient, test_user: User):
        """Test login using email instead of username."""
        credentials = {
            "username": "test@example.com",  # Using email as username
            "password": "testpassword"
        }
        
        response = client.post("/api/auth/login", json=credentials)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_user_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials."""
        # Wrong password
        credentials = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=credentials)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
        
        # Non-existent user
        credentials = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = client.post("/api/auth/login", json=credentials)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_token_refresh_flow(self, client: TestClient, test_user: User):
        """Test token refresh flow."""
        # First login to get tokens
        credentials = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        login_response = client.post("/api/auth/login", json=credentials)
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Use refresh token to get new tokens
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        response = client.post("/api/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify new tokens are valid (they may be the same if generated at same time)
        # This is expected behavior for JWT tokens with same payload and expiration
        
        new_access_payload = verify_token(data["access_token"], "access")
        new_refresh_payload = verify_token(data["refresh_token"], "refresh")
        
        assert new_access_payload is not None
        assert new_refresh_payload is not None
        assert new_access_payload["sub"] == "testuser"
        assert new_refresh_payload["sub"] == "testuser"
    
    def test_token_refresh_invalid_token(self, client: TestClient):
        """Test token refresh with invalid token."""
        refresh_data = {
            "refresh_token": "invalid_token"
        }
        
        response = client.post("/api/auth/refresh", json=refresh_data)
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
    
    def test_password_reset_flow(self, client: TestClient, test_user: User, db_session: Session):
        """Test complete password reset flow."""
        # Request password reset
        reset_request = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/auth/forgot-password", json=reset_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "Password reset token generated" in data["message"]
        assert "reset_token" in data
        
        reset_token = data["reset_token"]
        
        # Use reset token to change password
        reset_data = {
            "token": reset_token,
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/auth/reset-password", json=reset_data)
        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]
        
        # Verify password was changed in database
        db_session.refresh(test_user)
        assert verify_password("newpassword123", test_user.password_hash)
        assert not verify_password("testpassword", test_user.password_hash)
        
        # Verify can login with new password
        credentials = {
            "username": "testuser",
            "password": "newpassword123"
        }
        
        login_response = client.post("/api/auth/login", json=credentials)
        assert login_response.status_code == 200
    
    def test_password_reset_invalid_email(self, client: TestClient):
        """Test password reset with invalid email."""
        reset_request = {
            "email": "nonexistent@example.com"
        }
        
        response = client.post("/api/auth/forgot-password", json=reset_request)
        assert response.status_code == 404
        assert "User with this email not found" in response.json()["detail"]
    
    def test_password_reset_invalid_token(self, client: TestClient):
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid_token",
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/auth/reset-password", json=reset_data)
        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]
    
    def test_logout_endpoint(self, client: TestClient):
        """Test logout endpoint."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]
    
    def test_change_password_not_implemented(self, client: TestClient):
        """Test change password endpoint returns not implemented."""
        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/auth/change-password", json=password_data)
        assert response.status_code == 501
        assert "Change password requires authentication" in response.json()["detail"]
    
    def test_inactive_user_login(self, client: TestClient, db_session: Session):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Inactive User",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        credentials = {
            "username": "inactiveuser",
            "password": "password123"
        }
        
        response = client.post("/api/auth/login", json=credentials)
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
    
    def test_inactive_user_password_reset(self, client: TestClient, db_session: Session):
        """Test password reset with inactive user."""
        # Create inactive user
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Inactive User",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        reset_request = {
            "email": "inactive@example.com"
        }
        
        response = client.post("/api/auth/forgot-password", json=reset_request)
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
    
    def test_complete_authentication_workflow(self, client: TestClient, db_session: Session):
        """Test complete authentication workflow from registration to logout."""
        # 1. Register new user
        user_data = {
            "username": "workflowuser",
            "email": "workflow@example.com",
            "password": "password123",
            "full_name": "Workflow User"
        }
        
        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login with new user
        credentials = {
            "username": "workflowuser",
            "password": "password123"
        }
        
        login_response = client.post("/api/auth/login", json=credentials)
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # 3. Refresh token
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        refresh_response = client.post("/api/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200
        
        # 4. Request password reset
        reset_request = {
            "email": "workflow@example.com"
        }
        
        forgot_response = client.post("/api/auth/forgot-password", json=reset_request)
        assert forgot_response.status_code == 200
        
        reset_token = forgot_response.json()["reset_token"]
        
        # 5. Reset password
        reset_data = {
            "token": reset_token,
            "new_password": "newpassword123"
        }
        
        reset_response = client.post("/api/auth/reset-password", json=reset_data)
        assert reset_response.status_code == 200
        
        # 6. Login with new password
        new_credentials = {
            "username": "workflowuser",
            "password": "newpassword123"
        }
        
        new_login_response = client.post("/api/auth/login", json=new_credentials)
        assert new_login_response.status_code == 200
        
        # 7. Logout
        logout_response = client.post("/api/auth/logout")
        assert logout_response.status_code == 200
        
        # Verify user exists in database with correct data
        user = db_session.query(User).filter(User.username == "workflowuser").first()
        assert user is not None
        assert user.email == "workflow@example.com"
        assert user.full_name == "Workflow User"
        assert user.is_active is True
        assert verify_password("newpassword123", user.password_hash)