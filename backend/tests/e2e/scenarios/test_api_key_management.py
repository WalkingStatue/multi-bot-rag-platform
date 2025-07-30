"""
Unit tests for API key management functionality.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserAPIKey
from app.schemas.user import APIKeyCreate, APIKeyUpdate
from app.services.user_service import UserService
from app.utils.encryption import encrypt_api_key, decrypt_api_key


class TestAPIKeyManagement:
    """Test cases for API key management."""
    
    def test_add_api_key_success(self, db_session: Session, test_user: User):
        """Test successful API key addition."""
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
    
    def test_add_api_key_update_existing(self, db_session: Session, test_user: User):
        """Test updating existing API key."""
        # Arrange
        user_service = UserService(db_session)
        
        # Add initial key
        initial_data = APIKeyCreate(provider="openai", api_key="sk-old123456789")
        initial_result = user_service.add_api_key(test_user, initial_data)
        
        # Update with new key
        update_data = APIKeyCreate(provider="openai", api_key="sk-new456789012")
        
        # Act
        result = user_service.add_api_key(test_user, update_data)
        
        # Assert
        assert result.id == initial_result.id  # Same record
        assert result.provider == "openai"
        assert result.is_active is True
        
        # Verify updated key in database
        db_api_key = db_session.query(UserAPIKey).filter(
            UserAPIKey.user_id == test_user.id,
            UserAPIKey.provider == "openai"
        ).first()
        assert decrypt_api_key(db_api_key.api_key_encrypted) == "sk-new456789012"
    
    def test_get_user_api_keys(self, db_session: Session, test_user: User):
        """Test getting user's API keys."""
        # Arrange
        user_service = UserService(db_session)
        
        # Add multiple API keys
        providers = ["openai", "anthropic", "gemini"]
        for provider in providers:
            api_key_data = APIKeyCreate(provider=provider, api_key=f"key-{provider}")
            user_service.add_api_key(test_user, api_key_data)
        
        # Act
        result = user_service.get_user_api_keys(test_user)
        
        # Assert
        assert len(result) == 3
        result_providers = {key.provider for key in result}
        assert result_providers == set(providers)
        
        # Verify no actual keys are returned
        for key in result:
            assert not hasattr(key, 'api_key_encrypted')
    
    def test_get_api_key_decrypted(self, db_session: Session, test_user: User):
        """Test getting decrypted API key."""
        # Arrange
        user_service = UserService(db_session)
        api_key_data = APIKeyCreate(provider="openai", api_key="sk-secret123")
        user_service.add_api_key(test_user, api_key_data)
        
        # Act
        result = user_service.get_api_key(test_user, "openai")
        
        # Assert
        assert result == "sk-secret123"
    
    def test_get_api_key_not_found(self, db_session: Session, test_user: User):
        """Test getting API key that doesn't exist."""
        # Arrange
        user_service = UserService(db_session)
        
        # Act
        result = user_service.get_api_key(test_user, "nonexistent")
        
        # Assert
        assert result is None
    
    def test_get_api_key_inactive(self, db_session: Session, test_user: User):
        """Test getting inactive API key."""
        # Arrange
        user_service = UserService(db_session)
        api_key_data = APIKeyCreate(provider="openai", api_key="sk-test123")
        user_service.add_api_key(test_user, api_key_data)
        
        # Deactivate the key
        db_api_key = db_session.query(UserAPIKey).filter(
            UserAPIKey.user_id == test_user.id,
            UserAPIKey.provider == "openai"
        ).first()
        db_api_key.is_active = False
        db_session.commit()
        
        # Act
        result = user_service.get_api_key(test_user, "openai")
        
        # Assert
        assert result is None
    
    def test_update_api_key_success(self, db_session: Session, test_user: User):
        """Test successful API key update."""
        # Arrange
        user_service = UserService(db_session)
        
        # Add initial key
        initial_data = APIKeyCreate(provider="openai", api_key="sk-old123456789")
        user_service.add_api_key(test_user, initial_data)
        
        # Update key
        update_data = APIKeyUpdate(api_key="sk-new456789012", is_active=True)
        
        # Act
        result = user_service.update_api_key(test_user, "openai", update_data)
        
        # Assert
        assert result.provider == "openai"
        assert result.is_active is True
        
        # Verify updated key
        decrypted_key = user_service.get_api_key(test_user, "openai")
        assert decrypted_key == "sk-new456789012"
    
    def test_update_api_key_not_found(self, db_session: Session, test_user: User):
        """Test updating non-existent API key."""
        # Arrange
        user_service = UserService(db_session)
        update_data = APIKeyUpdate(api_key="sk-new456789012")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            user_service.update_api_key(test_user, "nonexistent", update_data)
        
        assert "not found" in str(exc_info.value)
    
    def test_delete_api_key_success(self, db_session: Session, test_user: User):
        """Test successful API key deletion."""
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
    
    def test_delete_api_key_not_found(self, db_session: Session, test_user: User):
        """Test deleting non-existent API key."""
        # Arrange
        user_service = UserService(db_session)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            user_service.delete_api_key(test_user, "nonexistent")
        
        assert "not found" in str(exc_info.value)


class TestAPIKeyEndpoints:
    """Test cases for API key management endpoints."""
    
    def test_get_api_keys_endpoint(self, client: TestClient, auth_headers: dict):
        """Test GET /users/api-keys endpoint."""
        # Act
        response = client.get("/api/users/api-keys", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_api_key_endpoint(self, client: TestClient, auth_headers: dict):
        """Test POST /users/api-keys endpoint."""
        # Arrange
        payload = {
            "provider": "openai",
            "api_key": "sk-test123456789"
        }
        
        # Act
        response = client.post("/api/users/api-keys", json=payload, headers=auth_headers)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "openai"
        assert data["is_active"] is True
        assert "id" in data
    
    def test_add_api_key_invalid_provider(self, client: TestClient, auth_headers: dict):
        """Test adding API key with invalid provider."""
        # Arrange
        payload = {
            "provider": "invalid_provider",
            "api_key": "sk-test123"
        }
        
        # Act
        response = client.post("/api/users/api-keys", json=payload, headers=auth_headers)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_update_api_key_endpoint(self, client: TestClient, auth_headers: dict):
        """Test PUT /users/api-keys/{provider} endpoint."""
        # Arrange - first add an API key
        add_payload = {
            "provider": "openai",
            "api_key": "sk-old123456789"
        }
        client.post("/api/users/api-keys", json=add_payload, headers=auth_headers)
        
        # Update payload
        update_payload = {
            "api_key": "sk-new456789012",
            "is_active": True
        }
        
        # Act
        response = client.put("/api/users/api-keys/openai", json=update_payload, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["is_active"] is True
    
    def test_delete_api_key_endpoint(self, client: TestClient, auth_headers: dict):
        """Test DELETE /users/api-keys/{provider} endpoint."""
        # Arrange - first add an API key
        add_payload = {
            "provider": "openai",
            "api_key": "sk-test123456789"
        }
        client.post("/api/users/api-keys", json=add_payload, headers=auth_headers)
        
        # Act
        response = client.delete("/api/users/api-keys/openai", headers=auth_headers)
        
        # Assert
        assert response.status_code == 204
    
    @patch('app.api.users.LLMProviderService')
    def test_validate_api_key_endpoint(self, mock_llm_service, client: TestClient, auth_headers: dict):
        """Test POST /users/api-keys/{provider}/validate endpoint."""
        # Arrange
        mock_service_instance = AsyncMock()
        mock_service_instance.validate_api_key.return_value = True
        mock_llm_service.return_value = mock_service_instance
        
        payload = {
            "provider": "openai",
            "api_key": "sk-test123456789"
        }
        
        # Act
        response = client.post("/api/users/api-keys/openai/validate", json=payload, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["provider"] == "openai"
        assert "message" in data
    
    @patch('app.api.users.LLMProviderService')
    def test_validate_api_key_invalid(self, mock_llm_service, client: TestClient, auth_headers: dict):
        """Test API key validation with invalid key."""
        # Arrange
        mock_service_instance = AsyncMock()
        mock_service_instance.validate_api_key.return_value = False
        mock_llm_service.return_value = mock_service_instance
        
        payload = {
            "provider": "openai",
            "api_key": "invalid-key123456"
        }
        
        # Act
        response = client.post("/api/users/api-keys/openai/validate", json=payload, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["provider"] == "openai"
    
    def test_validate_api_key_provider_mismatch(self, client: TestClient, auth_headers: dict):
        """Test API key validation with provider mismatch."""
        # Arrange
        payload = {
            "provider": "anthropic",  # Different from URL
            "api_key": "sk-test123456789"
        }
        
        # Act
        response = client.post("/api/users/api-keys/openai/validate", json=payload, headers=auth_headers)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "must match" in data["detail"]
    
    @patch('app.api.users.LLMProviderService')
    def test_get_supported_providers_endpoint(self, mock_llm_service, client: TestClient, auth_headers: dict):
        """Test GET /users/api-keys/providers endpoint."""
        # Arrange
        mock_service_instance = AsyncMock()
        mock_service_instance.get_supported_providers.return_value = ["openai", "anthropic"]
        mock_service_instance.get_available_models.side_effect = lambda provider: {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet"]
        }.get(provider, [])
        mock_llm_service.return_value = mock_service_instance
        
        # Act
        response = client.get("/api/users/api-keys/providers", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "total" in data
        assert data["total"] == 2
        assert "openai" in data["providers"]
        assert "anthropic" in data["providers"]
        assert "models" in data["providers"]["openai"]
    
    def test_api_key_endpoints_require_auth(self, client: TestClient):
        """Test that API key endpoints require authentication."""
        endpoints = [
            ("GET", "/api/users/api-keys"),
            ("POST", "/api/users/api-keys"),
            ("PUT", "/api/users/api-keys/openai"),
            ("DELETE", "/api/users/api-keys/openai"),
            ("POST", "/api/users/api-keys/openai/validate"),
            ("GET", "/api/users/api-keys/providers"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code in [401, 403]  # Either unauthorized or forbidden