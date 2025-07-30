"""
Unit tests for chat API endpoints.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
import uuid
import json

from main import app
from app.models.user import User
from app.models.bot import Bot
from app.models.conversation import ConversationSession
from app.schemas.conversation import ChatResponse
from app.core.dependencies import get_current_user
from tests.test_auth_helper import mock_authentication, create_mock_user


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )


@pytest.fixture
def sample_bot():
    """Sample bot for testing."""
    return Bot(
        id=uuid.uuid4(),
        name="Test Bot",
        description="A test bot",
        system_prompt="You are a helpful assistant.",
        owner_id=uuid.uuid4(),
        llm_provider="openai",
        llm_model="gpt-3.5-turbo"
    )


@pytest.fixture
def sample_session():
    """Sample conversation session."""
    return ConversationSession(
        id=uuid.uuid4(),
        bot_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Test Session"
    )


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token"}


class TestChatAPI:
    """Test cases for chat API endpoints."""
    
    @patch('app.services.chat_service.ChatService')
    @patch('app.services.permission_service.PermissionService')
    def test_chat_with_bot_success(self, mock_permission_service_class, mock_chat_service_class, client, sample_user, sample_bot, auth_headers):
        """Test successful chat with bot."""
        
        # Setup permission service mock
        mock_permission_service = Mock()
        mock_permission_service_class.return_value = mock_permission_service
        mock_permission_service.check_bot_permission.return_value = True
        
        # Setup chat service mock
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        # Mock chat response
        expected_response = ChatResponse(
            message="Hello! How can I help you today?",
            session_id=uuid.uuid4(),
            chunks_used=["Relevant context chunk"],
            processing_time=0.5,
            metadata={
                "user_message_id": str(uuid.uuid4()),
                "assistant_message_id": str(uuid.uuid4()),
                "chunks_count": 1,
                "llm_provider": "openai",
                "llm_model": "gpt-3.5-turbo"
            }
        )
        
        mock_chat_service.process_message = AsyncMock(return_value=expected_response)
        
        with mock_authentication(sample_user):
            # Prepare request
            chat_request = {
                "message": "Hello, how are you?",
                "session_id": None
            }
            
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/chat",
                json=chat_request,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            
            assert response_data["message"] == expected_response.message
            assert response_data["chunks_used"] == expected_response.chunks_used
            assert response_data["processing_time"] == expected_response.processing_time
            assert "metadata" in response_data
            
            # Verify service was called correctly
            mock_chat_service.process_message.assert_called_once()
            call_args = mock_chat_service.process_message.call_args
            assert call_args[1]["bot_id"] == sample_bot.id
            assert call_args[1]["user_id"] == sample_user.id
    
    @patch('app.services.chat_service.ChatService')
    def test_chat_with_bot_with_session_id(self, mock_chat_service_class, client, sample_user, sample_bot, sample_session, auth_headers):
        """Test chat with existing session ID."""
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        expected_response = ChatResponse(
            message="This is a follow-up response.",
            session_id=sample_session.id,
            chunks_used=[],
            processing_time=0.3,
            metadata={"chunks_count": 0}
        )
        
        mock_chat_service.process_message = AsyncMock(return_value=expected_response)
        
        with mock_authentication(sample_user):
            # Prepare request with session ID
            chat_request = {
                "message": "Follow-up question",
                "session_id": str(sample_session.id)
            }
            
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/chat",
                json=chat_request,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["session_id"] == str(sample_session.id)
            assert response_data["message"] == "This is a follow-up response."
    
    @patch('app.services.chat_service.ChatService')
    def test_chat_with_bot_permission_denied(self, mock_chat_service_class, client, sample_user, sample_bot, auth_headers):
        """Test chat with permission denied."""
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        # Mock permission denied exception
        from fastapi import HTTPException
        mock_chat_service.process_message = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to chat with this bot"
            )
        )
        
        with mock_authentication(sample_user):
            # Prepare request
            chat_request = {
                "message": "Hello",
                "session_id": None
            }
            
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/chat",
                json=chat_request,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "permission" in response.json()["detail"].lower()
    
    @patch('app.services.chat_service.ChatService')
    def test_chat_with_bot_not_found(self, mock_chat_service_class, client, sample_user, auth_headers):
        """Test chat with non-existent bot."""
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        # Mock bot not found exception
        from fastapi import HTTPException
        mock_chat_service.process_message = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        )
        
        with mock_authentication(sample_user):
            # Prepare request
            chat_request = {
                "message": "Hello",
                "session_id": None
            }
            
            non_existent_bot_id = uuid.uuid4()
            
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{non_existent_bot_id}/chat",
                json=chat_request,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"].lower()
    
    def test_chat_with_invalid_message(self, client, sample_user, sample_bot, auth_headers):
        """Test chat with invalid message format."""
        with mock_authentication(sample_user):
            # Test empty message
            chat_request = {
                "message": "",  # Empty message should be invalid
                "session_id": None
            }
        
        # Execute request
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_with_very_long_message(self, client, sample_user, sample_bot, auth_headers):
        """Test chat with message exceeding length limit."""
        with mock_authentication(sample_user):
            # Create very long message (exceeding 10000 character limit)
            long_message = "This is a very long message. " * 500  # Should exceed 10000 chars
            
            chat_request = {
                "message": long_message,
                "session_id": None
            }
        
        # Execute request
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.services.chat_service.ChatService')
    def test_create_bot_session_success(self, mock_chat_service_class, client, sample_user, sample_bot, auth_headers):
        """Test successful bot session creation."""
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        expected_session = ConversationSession(
            id=uuid.uuid4(),
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Custom Session Title"
        )
        
        mock_chat_service.create_session = AsyncMock(return_value=expected_session)
        
        with mock_authentication(sample_user):
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/sessions",
                params={"title": "Custom Session Title"},
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["bot_id"] == str(sample_bot.id)
            assert response_data["user_id"] == str(sample_user.id)
            assert response_data["title"] == "Custom Session Title"
            
            # Verify service was called correctly
            mock_chat_service.create_session.assert_called_once_with(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                title="Custom Session Title"
            )
    
    @patch('app.services.chat_service.ChatService')
    def test_create_bot_session_without_title(self, mock_chat_service_class, client, sample_user, sample_bot, auth_headers):
        """Test bot session creation without custom title."""
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        expected_session = ConversationSession(
            id=uuid.uuid4(),
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="New Conversation"  # Default title
        )
        
        mock_chat_service.create_session = AsyncMock(return_value=expected_session)
        
        with mock_authentication(sample_user):
            # Execute request without title parameter
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/sessions",
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            
            # Verify service was called with None title (will use default)
            mock_chat_service.create_session.assert_called_once_with(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                title=None
            )
    
    @patch('app.services.chat_service.ChatService')
    def test_create_bot_session_permission_denied(self, mock_chat_service_class, client, sample_user, sample_bot, auth_headers):
        """Test bot session creation with permission denied."""
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        # Mock permission denied exception
        from fastapi import HTTPException
        mock_chat_service.create_session = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to create sessions for this bot"
            )
        )
        
        with mock_authentication(sample_user):
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/sessions",
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "permission" in response.json()["detail"].lower()
    
    @patch('app.core.dependencies.get_current_user')
    def test_chat_without_authentication(self, mock_get_user, client, sample_bot):
        """Test chat endpoint without authentication."""
        # Don't set up authentication mock
        mock_get_user.side_effect = Exception("Authentication required")
        
        chat_request = {
            "message": "Hello",
            "session_id": None
        }
        
        # Execute request without auth headers
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            json=chat_request
        )
        
        # Should return authentication error
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.chat_service.ChatService')
    def test_chat_with_malformed_json(self, mock_chat_service_class, mock_get_user, client, sample_user, sample_bot, auth_headers):
        """Test chat endpoint with malformed JSON."""
        # Setup mocks
        mock_get_user.return_value = sample_user
        
        # Execute request with malformed JSON
        response = client.post(
            f"/api/conversations/bots/{sample_bot.id}/chat",
            content="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_with_invalid_bot_id(self, client, sample_user, auth_headers):
        """Test chat endpoint with invalid bot ID format."""
        with mock_authentication(sample_user):
            chat_request = {
                "message": "Hello",
                "session_id": None
            }
            
            # Execute request with invalid UUID format
            response = client.post(
                "/api/conversations/bots/invalid-uuid/chat",
                json=chat_request,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_with_invalid_session_id(self, client, sample_user, sample_bot, auth_headers):
        """Test chat endpoint with invalid session ID format."""
        with mock_authentication(sample_user):
            chat_request = {
                "message": "Hello",
                "session_id": "invalid-uuid"  # Invalid UUID format
            }
            
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/chat",
                json=chat_request,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.services.chat_service.ChatService')
    def test_chat_service_internal_error(self, mock_chat_service_class, client, sample_user, sample_bot, auth_headers):
        """Test chat endpoint with internal service error."""
        mock_chat_service = Mock()
        mock_chat_service_class.return_value = mock_chat_service
        
        # Mock internal service error
        mock_chat_service.process_message = AsyncMock(
            side_effect=Exception("Internal service error")
        )
        
        with mock_authentication(sample_user):
            chat_request = {
                "message": "Hello",
                "session_id": None
            }
            
            # Execute request
            response = client.post(
                f"/api/conversations/bots/{sample_bot.id}/chat",
                json=chat_request,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "failed to process" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__])