"""
Integration tests for chat RAG pipeline.
"""
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserAPIKey
from app.models.bot import Bot, BotPermission
from app.models.conversation import ConversationSession
from app.schemas.conversation import ChatResponse


class TestChatRAGIntegration:
    """Integration tests for chat RAG pipeline."""
    
    @patch('app.services.chat_service.LLMProviderService')
    @patch('app.services.chat_service.EmbeddingProviderService')
    @patch('app.services.chat_service.VectorService')
    @patch('app.services.chat_service.UserService')
    def test_chat_with_bot_success(
        self, 
        mock_user_service_class,
        mock_vector_service_class,
        mock_embedding_service_class,
        mock_llm_service_class,
        client: TestClient, 
        db_session: Session, 
        sample_user: User, 
        sample_bot: Bot, 
        sample_auth_headers
    ):
        """Test successful chat with bot through RAG pipeline."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create API key for the user
        api_key = UserAPIKey(
            user_id=sample_user.id,
            provider="openai",
            api_key_encrypted="encrypted_test_key",
            is_active=True
        )
        db_session.add(api_key)
        db_session.commit()
        
        # Mock services
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user_api_key.return_value = "test_api_key"
        
        mock_vector_service = Mock()
        mock_vector_service_class.return_value = mock_vector_service
        mock_vector_service.search_relevant_chunks = AsyncMock(return_value=[
            {
                "id": "chunk_1",
                "text": "This is relevant context from documents",
                "score": 0.9
            }
        ])
        
        mock_embedding_service = Mock()
        mock_embedding_service_class.return_value = mock_embedding_service
        mock_embedding_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        mock_llm_service.generate_response = AsyncMock(return_value="Hello! I'm here to help you.")
        
        # Prepare chat request
        chat_request = {
            "message": "Hello, how can you help me?",
            "session_id": None
        }
        
        # Execute request
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request,
            headers=sample_auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello! I'm here to help you."
        assert "session_id" in data
        assert "processing_time" in data
        assert "metadata" in data
        
        # Verify services were called
        mock_user_service.get_user_api_key.assert_called_once()
        mock_embedding_service.generate_single_embedding.assert_called_once()
        mock_vector_service.search_relevant_chunks.assert_called_once()
        mock_llm_service.generate_response.assert_called_once()
    
    @patch('app.services.chat_service.LLMProviderService')
    @patch('app.services.chat_service.EmbeddingProviderService')
    @patch('app.services.chat_service.VectorService')
    @patch('app.services.chat_service.UserService')
    def test_chat_with_existing_session(
        self, 
        mock_user_service_class,
        mock_vector_service_class,
        mock_embedding_service_class,
        mock_llm_service_class,
        client: TestClient, 
        db_session: Session, 
        sample_user: User, 
        sample_bot: Bot, 
        sample_auth_headers
    ):
        """Test chat with existing session."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create existing session
        session = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Existing Session"
        )
        db_session.add(session)
        
        # Create API key for the user
        api_key = UserAPIKey(
            user_id=sample_user.id,
            provider="openai",
            api_key_encrypted="encrypted_test_key",
            is_active=True
        )
        db_session.add(api_key)
        db_session.commit()
        
        # Mock services
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user_api_key.return_value = "test_api_key"
        
        mock_vector_service = Mock()
        mock_vector_service_class.return_value = mock_vector_service
        mock_vector_service.search_relevant_chunks = AsyncMock(return_value=[])
        
        mock_embedding_service = Mock()
        mock_embedding_service_class.return_value = mock_embedding_service
        mock_embedding_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        mock_llm_service.generate_response = AsyncMock(return_value="This is a follow-up response.")
        
        # Prepare chat request with existing session
        chat_request = {
            "message": "Follow-up question",
            "session_id": str(session.id)
        }
        
        # Execute request
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request,
            headers=sample_auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "This is a follow-up response."
        assert data["session_id"] == str(session.id)
    
    def test_chat_without_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test chat without bot permission."""
        # Don't create any permission for the user
        
        chat_request = {
            "message": "Hello",
            "session_id": None
        }
        
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 403
        assert "User does not have permission to chat with this bot" in response.json()["detail"]
    
    def test_chat_with_nonexistent_bot(self, client: TestClient, db_session: Session, sample_user: User, sample_auth_headers):
        """Test chat with non-existent bot."""
        non_existent_bot_id = uuid.uuid4()
        
        chat_request = {
            "message": "Hello",
            "session_id": None
        }
        
        response = client.post(
            f"/api/conversations/bots/{non_existent_bot_id}/chat",
            json=chat_request,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 404
        assert "Bot not found" in response.json()["detail"]
    
    def test_chat_without_authentication(self, client: TestClient, sample_bot: Bot):
        """Test chat without authentication."""
        chat_request = {
            "message": "Hello",
            "session_id": None
        }
        
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request
        )
        
        assert response.status_code == 403
    
    def test_chat_with_invalid_message(self, client: TestClient, sample_bot: Bot, sample_auth_headers):
        """Test chat with invalid message."""
        chat_request = {
            "message": "",  # Empty message
            "session_id": None
        }
        
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.chat_service.LLMProviderService')
    @patch('app.services.chat_service.EmbeddingProviderService')
    @patch('app.services.chat_service.VectorService')
    @patch('app.services.chat_service.UserService')
    def test_chat_without_api_key(
        self, 
        mock_user_service_class,
        mock_vector_service_class,
        mock_embedding_service_class,
        mock_llm_service_class,
        client: TestClient, 
        db_session: Session, 
        sample_user: User, 
        sample_bot: Bot, 
        sample_auth_headers
    ):
        """Test chat without API key configured."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        # Mock user service to return None for API key
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user_api_key.return_value = None
        
        chat_request = {
            "message": "Hello",
            "session_id": None
        }
        
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 400
        assert "No API key configured" in response.json()["detail"]
    
    def test_create_bot_session_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful bot session creation."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/sessions",
            params={"title": "New Bot Session"},
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_id"] == str(sample_bot.id)
        assert data["title"] == "New Bot Session"
        assert data["user_id"] == str(sample_user.id)
    
    def test_create_bot_session_without_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test bot session creation without permission."""
        # Don't create any permission for the user
        
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/sessions",
            params={"title": "Unauthorized Session"},
            headers=sample_auth_headers
        )
        
        assert response.status_code == 403
        assert "User does not have permission to create sessions for this bot" in response.json()["detail"]