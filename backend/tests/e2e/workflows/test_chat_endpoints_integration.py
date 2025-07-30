"""
Integration tests for chat and conversation endpoints.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.models.conversation import ConversationSession, Message


class TestChatEndpointsIntegration:
    """Integration tests for chat and conversation endpoints."""
    
    def test_create_session_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the session creation endpoint."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        session_data = {
            "bot_id": str(sample_bot.id),
            "title": "Integration Test Session"
        }
        
        response = client.post(
            "/api/conversations/sessions",
            json=session_data,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_id"] == str(sample_bot.id)
        assert data["title"] == "Integration Test Session"
        assert data["user_id"] == str(sample_user.id)
        
        # Verify session was created in database
        session = db_session.query(ConversationSession).filter(
            ConversationSession.id == data["id"]
        ).first()
        assert session is not None
        assert session.title == "Integration Test Session"
    
    def test_list_sessions_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the session listing endpoint."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test sessions
        session1 = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Session 1"
        )
        session2 = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Session 2"
        )
        db_session.add(session1)
        db_session.add(session2)
        db_session.commit()
        
        response = client.get("/api/conversations/sessions", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Verify both sessions are returned
        titles = [session["title"] for session in data]
        assert "Session 1" in titles
        assert "Session 2" in titles
    
    def test_add_message_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the message addition endpoint."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test session
        session = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Test Session"
        )
        db_session.add(session)
        db_session.commit()
        
        message_data = {
            "session_id": str(session.id),
            "role": "user",
            "content": "Hello, this is a test message!"
        }
        
        response = client.post(
            "/api/conversations/messages",
            json=message_data,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello, this is a test message!"
        assert data["role"] == "user"
        assert data["session_id"] == str(session.id)
        
        # Verify message was created in database
        message = db_session.query(Message).filter(
            Message.id == data["id"]
        ).first()
        assert message is not None
        assert message.content == "Hello, this is a test message!"
    
    def test_get_session_messages_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the session messages retrieval endpoint."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test session
        session = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Test Session"
        )
        db_session.add(session)
        db_session.flush()
        
        # Create test messages
        message1 = Message(
            session_id=session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="First message"
        )
        message2 = Message(
            session_id=session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="assistant",
            content="Second message"
        )
        db_session.add(message1)
        db_session.add(message2)
        db_session.commit()
        
        response = client.get(f"/api/conversations/sessions/{session.id}/messages", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Messages are ordered by created_at
        assert data[0]["content"] == "First message"
        assert data[1]["content"] == "Second message"
    
    def test_search_conversations_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the conversation search endpoint."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test session
        session = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Searchable Session"
        )
        db_session.add(session)
        db_session.flush()
        
        # Create test message with searchable content
        message = Message(
            session_id=session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="This message contains searchable keywords for testing"
        )
        db_session.add(message)
        db_session.commit()
        
        response = client.get("/api/conversations/search?q=searchable", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "searchable"
        assert len(data["results"]) == 1
        assert "searchable" in data["results"][0]["content"].lower()
    
    def test_export_conversations_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the conversation export endpoint."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test session
        session = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Export Test Session"
        )
        db_session.add(session)
        db_session.flush()
        
        # Create test message
        message = Message(
            session_id=session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="Export test message"
        )
        db_session.add(message)
        db_session.commit()
        
        response = client.get("/api/conversations/export", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "metadata" in data
        assert data["metadata"]["total_sessions"] == 1
        assert data["metadata"]["total_messages"] == 1
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["title"] == "Export Test Session"
        assert len(data["conversations"][0]["messages"]) == 1
    
    def test_conversation_analytics_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the conversation analytics endpoint."""
        # Create viewer permission for the user
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test sessions and messages
        session1 = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Analytics Session 1"
        )
        session2 = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Analytics Session 2"
        )
        db_session.add(session1)
        db_session.add(session2)
        db_session.flush()
        
        # Create test messages
        message1 = Message(
            session_id=session1.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="Analytics message 1"
        )
        message2 = Message(
            session_id=session2.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="Analytics message 2"
        )
        db_session.add(message1)
        db_session.add(message2)
        db_session.commit()
        
        response = client.get("/api/conversations/analytics", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 2
        assert data["total_messages"] == 2
        assert "recent_activity" in data
        assert "bot_usage" in data
        assert len(data["bot_usage"]) >= 1
    
    def test_create_bot_session_endpoint(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test the bot-specific session creation endpoint."""
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
            params={"title": "Bot Session Test"},
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_id"] == str(sample_bot.id)
        assert data["title"] == "Bot Session Test"
        assert data["user_id"] == str(sample_user.id)
    
    def test_unauthorized_access(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test that endpoints require authentication."""
        session_data = {
            "bot_id": str(sample_bot.id),
            "title": "Unauthorized Test"
        }
        
        # Test without auth headers
        response = client.post("/api/conversations/sessions", json=session_data)
        assert response.status_code == 403
        
        response = client.get("/api/conversations/sessions")
        assert response.status_code == 403
        
        response = client.get("/api/conversations/search?q=test")
        assert response.status_code == 403
        
        response = client.get("/api/conversations/export")
        assert response.status_code == 403
        
        response = client.get("/api/conversations/analytics")
        assert response.status_code == 403
    
    def test_permission_denied_access(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test that endpoints respect bot permissions."""
        # Don't create any permission for the user
        
        session_data = {
            "bot_id": str(sample_bot.id),
            "title": "Permission Denied Test"
        }
        
        response = client.post("/api/conversations/sessions", json=session_data, headers=sample_auth_headers)
        assert response.status_code == 403
        assert "User does not have permission to access this bot" in response.json()["detail"]