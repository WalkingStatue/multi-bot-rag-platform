"""
Tests for bot management API endpoints.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.services.auth_service import AuthService


class TestBotsAPI:
    """Test cases for bot management API endpoints."""
    
    def test_create_bot(self, client: TestClient, db_session: Session, test_user: User, auth_headers):
        """Test creating a new bot."""
        bot_data = {
            "name": "Test Bot",
            "description": "A test bot",
            "system_prompt": "You are a helpful assistant",
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Bot"
        assert data["description"] == "A test bot"
        assert data["system_prompt"] == "You are a helpful assistant"
        assert data["owner_id"] == str(test_user.id)
        assert data["llm_provider"] == "openai"
        assert data["temperature"] == 0.7
    
    def test_create_bot_unauthorized(self, client: TestClient):
        """Test creating bot without authentication."""
        bot_data = {
            "name": "Test Bot",
            "system_prompt": "You are a helpful assistant"
        }
        
        response = client.post("/api/bots/", json=bot_data)
        assert response.status_code == 403
    
    def test_create_bot_invalid_data(self, client: TestClient, auth_headers):
        """Test creating bot with invalid data."""
        bot_data = {
            "name": "",  # Empty name
            "system_prompt": "You are a helpful assistant"
        }
        
        response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_list_user_bots(self, client: TestClient, db_session: Session, sample_user: User, sample_auth_headers):
        """Test listing user's accessible bots."""
        # Create a bot with owner permission
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=sample_user.id
        )
        db_session.add(bot)
        db_session.flush()
        
        permission = BotPermission(
            bot_id=bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        response = client.get("/api/bots/", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["bot"]["name"] == "Test Bot"
        assert data[0]["role"] == "owner"
    
    def test_get_bot_with_access(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test getting bot details when user has access."""
        # Create viewer permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        response = client.get(f"/api/bots/{sample_bot.id}", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_bot.id)
        assert data["name"] == sample_bot.name
    
    def test_get_bot_without_access(self, client: TestClient, sample_bot: Bot, auth_headers):
        """Test getting bot details when user has no access."""
        response = client.get(f"/api/bots/{sample_bot.id}", headers=auth_headers)
        assert response.status_code == 403
    
    def test_get_bot_nonexistent(self, client: TestClient, auth_headers):
        """Test getting nonexistent bot."""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/bots/{fake_id}", headers=auth_headers)
        assert response.status_code == 403  # Access denied comes first
    
    def test_update_bot_with_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test updating bot when user has edit permission."""
        # Create admin permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        update_data = {
            "name": "Updated Bot Name",
            "temperature": 0.8
        }
        
        response = client.put(f"/api/bots/{sample_bot.id}", json=update_data, headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Bot Name"
        assert data["temperature"] == 0.8
    
    def test_update_bot_without_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test updating bot when user lacks edit permission."""
        # Create viewer permission (cannot edit)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        update_data = {"name": "Updated Bot Name"}
        
        response = client.put(f"/api/bots/{sample_bot.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 403
    
    def test_delete_bot_as_owner(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test deleting bot as owner."""
        # Create owner permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        response = client.delete(f"/api/bots/{sample_bot.id}", headers=sample_auth_headers)
        assert response.status_code == 204
        
        # Verify bot is deleted
        deleted_bot = db_session.query(Bot).filter(Bot.id == sample_bot.id).first()
        assert deleted_bot is None
    
    def test_delete_bot_without_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test deleting bot without owner permission."""
        # Create admin permission (not owner)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        response = client.delete(f"/api/bots/{sample_bot.id}", headers=auth_headers)
        assert response.status_code == 403
    
    def test_transfer_ownership(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test transferring bot ownership."""
        # Create owner permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create new owner
        new_owner = User(
            username="newowner",
            email="newowner@example.com",
            password_hash="hashed_password"
        )
        db_session.add(new_owner)
        db_session.commit()
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/transfer",
            json={"new_owner_id": str(new_owner.id)},
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "transferred successfully" in data["message"]
        
        # Verify ownership changed
        db_session.refresh(sample_bot)
        assert sample_bot.owner_id == new_owner.id
    
    def test_transfer_ownership_not_owner(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test transferring ownership when not owner."""
        # Create admin permission (not owner)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        new_owner_id = uuid.uuid4()
        response = client.post(
            f"/api/bots/{sample_bot.id}/transfer",
            json={"new_owner_id": str(new_owner_id)},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_get_bot_analytics(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test getting bot analytics."""
        # Create viewer permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        response = client.get(f"/api/bots/{sample_bot.id}/analytics", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_id"] == str(sample_bot.id)
        assert data["bot_name"] == sample_bot.name
        assert data["user_role"] == "viewer"
        assert "collaborator_count" in data
        assert "conversation_count" in data
    
    def test_get_bot_analytics_without_access(self, client: TestClient, sample_bot: Bot, auth_headers):
        """Test getting bot analytics without access."""
        response = client.get(f"/api/bots/{sample_bot.id}/analytics", headers=auth_headers)
        assert response.status_code == 403
    
    def test_create_bot_multi_llm_providers(self, client: TestClient, auth_headers):
        """Test creating bots with different LLM providers."""
        providers_data = [
            {
                "name": "OpenAI Bot",
                "system_prompt": "You are an OpenAI assistant",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-large"
            },
            {
                "name": "Anthropic Bot", 
                "system_prompt": "You are a Claude assistant",
                "llm_provider": "anthropic",
                "llm_model": "claude-3-sonnet-20240229",
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-small"
            },
            {
                "name": "Gemini Bot",
                "system_prompt": "You are a Gemini assistant", 
                "llm_provider": "gemini",
                "llm_model": "gemini-pro",
                "embedding_provider": "gemini",
                "embedding_model": "embedding-001"
            },
            {
                "name": "OpenRouter Bot",
                "system_prompt": "You are an OpenRouter assistant",
                "llm_provider": "openrouter", 
                "llm_model": "anthropic/claude-3-haiku",
                "embedding_provider": "local",
                "embedding_model": "all-MiniLM-L6-v2"
            }
        ]
        
        for bot_data in providers_data:
            response = client.post("/api/bots/", json=bot_data, headers=auth_headers)
            assert response.status_code == 201
            
            data = response.json()
            assert data["name"] == bot_data["name"]
            assert data["llm_provider"] == bot_data["llm_provider"]
            assert data["llm_model"] == bot_data["llm_model"]
            assert data["embedding_provider"] == bot_data["embedding_provider"]
            assert data["embedding_model"] == bot_data["embedding_model"]
    
    def test_update_bot_llm_configuration(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test updating bot LLM and embedding configuration."""
        # Create admin permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        # Update LLM configuration
        update_data = {
            "llm_provider": "anthropic",
            "llm_model": "claude-3-opus-20240229",
            "embedding_provider": "gemini",
            "embedding_model": "embedding-001",
            "temperature": 0.5,
            "max_tokens": 2000
        }
        
        response = client.put(f"/api/bots/{sample_bot.id}", json=update_data, headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["llm_provider"] == "anthropic"
        assert data["llm_model"] == "claude-3-opus-20240229"
        assert data["embedding_provider"] == "gemini"
        assert data["embedding_model"] == "embedding-001"
        assert data["temperature"] == 0.5
        assert data["max_tokens"] == 2000