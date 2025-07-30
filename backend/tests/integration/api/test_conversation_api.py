"""
Integration tests for conversation API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.conversation import ConversationSession, Message
from app.models.user import User
from app.models.bot import Bot, BotPermission


class TestConversationAPI:
    """Test cases for conversation API endpoints."""
    
    def test_create_session_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful session creation via API."""
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
            "title": "Test Session"
        }
        
        response = client.post(
            "/api/conversations/sessions",
            json=session_data,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_id"] == str(sample_bot.id)
        assert data["title"] == "Test Session"
        assert data["user_id"] == str(sample_user.id)
    
    def test_create_session_no_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test session creation without permission."""
        # Don't create any permission for the user
        
        session_data = {
            "bot_id": str(sample_bot.id),
            "title": "Test Session"
        }
        
        response = client.post(
            "/api/conversations/sessions",
            json=session_data,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 403
        assert "User does not have permission to access this bot" in response.json()["detail"]
    
    def test_list_sessions_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful session listing via API."""
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
        # Sessions are ordered by updated_at desc, so newest first
        assert data[0]["title"] in ["Session 1", "Session 2"]
        assert data[1]["title"] in ["Session 1", "Session 2"]
    
    def test_get_session_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful session retrieval via API."""
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
        
        response = client.get(f"/api/conversations/sessions/{session.id}", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(session.id)
        assert data["title"] == "Test Session"
    
    def test_get_session_not_found(self, client: TestClient, db_session: Session, sample_user: User, sample_auth_headers):
        """Test session retrieval when session doesn't exist."""
        non_existent_session_id = uuid.uuid4()
        
        response = client.get(f"/api/conversations/sessions/{non_existent_session_id}", headers=sample_auth_headers)
        
        assert response.status_code == 404
        assert "Session not found or access denied" in response.json()["detail"]
    
    def test_update_session_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful session update via API."""
        # Create editor permission for the user (needed to edit sessions)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test session
        session = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Original Session"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.put(
            f"/api/conversations/sessions/{session.id}",
            params={"title": "Updated Session", "is_shared": True},
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Session"
    
    def test_delete_session_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful session deletion via API."""
        # Create admin permission for the user (needed to delete sessions)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create test session
        session = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Session to Delete"
        )
        db_session.add(session)
        db_session.commit()
        
        response = client.delete(f"/api/conversations/sessions/{session.id}", headers=sample_auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Session deleted successfully"
    
    def test_add_message_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful message addition via API."""
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
            "content": "Hello, bot!"
        }
        
        response = client.post(
            "/api/conversations/messages",
            json=message_data,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello, bot!"
        assert data["role"] == "user"
        assert data["session_id"] == str(session.id)
    
    def test_get_session_messages_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful message retrieval via API."""
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
            content="Hello"
        )
        message2 = Message(
            session_id=session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="assistant",
            content="Hi there!"
        )
        db_session.add(message1)
        db_session.add(message2)
        db_session.commit()
        
        response = client.get(f"/api/conversations/sessions/{session.id}/messages", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Messages are ordered by created_at, so first message first
        assert data[0]["content"] == "Hello"
        assert data[1]["content"] == "Hi there!"
    
    def test_search_conversations_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful conversation search via API."""
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
        
        # Create test message with searchable content
        message = Message(
            session_id=session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="This is a test message for searching"
        )
        db_session.add(message)
        db_session.commit()
        
        response = client.get("/api/conversations/search?q=test", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert len(data["results"]) == 1
        assert "test" in data["results"][0]["content"].lower()
    
    def test_export_conversations_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful conversation export via API."""
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
        
        # Create test message
        message = Message(
            session_id=session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="Hello"
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
        assert data["conversations"][0]["title"] == "Test Session"
    
    def test_get_conversation_analytics_success(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test successful conversation analytics via API."""
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
            title="Session 1"
        )
        session2 = ConversationSession(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Session 2"
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
            content="Hello 1"
        )
        message2 = Message(
            session_id=session2.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content="Hello 2"
        )
        db_session.add(message1)
        db_session.add(message2)
        db_session.commit()
        
        response = client.get("/api/conversations/analytics", headers=sample_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 2
        assert data["total_messages"] == 2
        assert len(data["recent_activity"]) <= 10  # Limited to 10 recent sessions
        assert len(data["bot_usage"]) >= 1