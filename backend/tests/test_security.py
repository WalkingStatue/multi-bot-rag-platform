"""
Unit tests for security utilities.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
    generate_password_reset_token,
    create_password_reset_token,
    verify_password_reset_token
)


class TestSecurity:
    """Test cases for security utilities."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        # Arrange
        password = "testpassword123"
        
        # Act
        hashed = get_password_hash(password)
        
        # Assert
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self):
        """Test access token creation."""
        # Arrange
        data = {"sub": "testuser"}
        
        # Act
        token = create_access_token(data)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = verify_token(token, token_type="access")
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"
    
    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        # Arrange
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        
        # Act
        token = create_access_token(data, expires_delta)
        
        # Assert
        payload = verify_token(token, token_type="access")
        assert payload is not None
        assert payload["sub"] == "testuser"
        
        # Check expiry is approximately correct (within 5 minute tolerance)
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        assert abs((exp_time - expected_exp).total_seconds()) < 300  # 5 minutes tolerance
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        # Arrange
        data = {"sub": "testuser"}
        
        # Act
        token = create_refresh_token(data)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = verify_token(token, token_type="refresh")
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"
    
    def test_verify_token_valid_access(self):
        """Test token verification with valid access token."""
        # Arrange
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Act
        payload = verify_token(token, token_type="access")
        
        # Assert
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"
    
    def test_verify_token_valid_refresh(self):
        """Test token verification with valid refresh token."""
        # Arrange
        data = {"sub": "testuser"}
        token = create_refresh_token(data)
        
        # Act
        payload = verify_token(token, token_type="refresh")
        
        # Assert
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"
    
    def test_verify_token_wrong_type(self):
        """Test token verification with wrong token type."""
        # Arrange
        data = {"sub": "testuser"}
        access_token = create_access_token(data)
        
        # Act
        payload = verify_token(access_token, token_type="refresh")
        
        # Assert
        assert payload is None
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act
        payload = verify_token(invalid_token, token_type="access")
        
        # Assert
        assert payload is None
    
    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        # Arrange
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta)
        
        # Act
        payload = verify_token(token, token_type="access")
        
        # Assert
        assert payload is None
    
    def test_generate_password_reset_token(self):
        """Test password reset token generation."""
        # Act
        token1 = generate_password_reset_token()
        token2 = generate_password_reset_token()
        
        # Assert
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        assert len(token1) == 32
        assert len(token2) == 32
        assert token1 != token2  # Should be unique
    
    def test_create_password_reset_token(self):
        """Test password reset JWT token creation."""
        # Arrange
        email = "test@example.com"
        
        # Act
        token = create_password_reset_token(email)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded_email = verify_password_reset_token(token)
        assert decoded_email == email
    
    def test_verify_password_reset_token_valid(self):
        """Test password reset token verification with valid token."""
        # Arrange
        email = "test@example.com"
        token = create_password_reset_token(email)
        
        # Act
        result = verify_password_reset_token(token)
        
        # Assert
        assert result == email
    
    def test_verify_password_reset_token_invalid(self):
        """Test password reset token verification with invalid token."""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act
        result = verify_password_reset_token(invalid_token)
        
        # Assert
        assert result is None
    
    def test_verify_password_reset_token_wrong_type(self):
        """Test password reset token verification with wrong token type."""
        # Arrange
        data = {"sub": "testuser"}
        access_token = create_access_token(data)
        
        # Act
        result = verify_password_reset_token(access_token)
        
        # Assert
        assert result is None
    
    @patch('app.core.security.datetime')
    def test_verify_password_reset_token_expired(self, mock_datetime):
        """Test password reset token verification with expired token."""
        # Arrange
        email = "test@example.com"
        
        # Mock current time for token creation
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        token = create_password_reset_token(email)
        
        # Mock current time for verification (2 hours later, token expires in 1 hour)
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 14, 0, 0)
        
        # Act
        result = verify_password_reset_token(token)
        
        # Assert
        assert result is None