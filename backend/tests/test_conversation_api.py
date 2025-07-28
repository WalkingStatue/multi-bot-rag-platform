"""
Integration tests for conversation API endpoints.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import uuid
from datetime import datetime

from main import app
from app.models.conversation import ConversationSession, Message
from app.models.user import User
from app.schemas.conversation import ConversationSessionCreate, MessageCreate


class TestConversationAPI:
    """Test cases for conversation API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.user_id = uuid.uuid4()
        self.bot_id = uuid.uuid4()
        self.session_id = uuid.uuid4()
        
        # Mock user for authentication
        self.mock_user = User(
            id=self.user_id,
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_create_session_success(self, mock_get_db, mock_get_current_user):
        """Test successful session creation via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.create_session.return_value = mock_session
            
            # Act
            response = self.client.post(
                "/api/conversations/sessions",
                json={
                    "bot_id": str(self.bot_id),
                    "title": "Test Session"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(self.session_id)
            assert data["bot_id"] == str(self.bot_id)
            assert data["title"] == "Test Session"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_create_session_no_permission(self, mock_get_db, mock_get_current_user):
        """Test session creation without permission."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.create_session.side_effect = ValueError("User does not have permission to access this bot")
            
            # Act
            response = self.client.post(
                "/api/conversations/sessions",
                json={
                    "bot_id": str(self.bot_id),
                    "title": "Test Session"
                }
            )
            
            # Assert
            assert response.status_code == 403
            assert "User does not have permission to access this bot" in response.json()["detail"]
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_list_sessions_success(self, mock_get_db, mock_get_current_user):
        """Test successful session listing via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_sessions = [
            ConversationSession(id=uuid.uuid4(), bot_id=self.bot_id, user_id=self.user_id, title="Session 1"),
            ConversationSession(id=uuid.uuid4(), bot_id=self.bot_id, user_id=self.user_id, title="Session 2")
        ]
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.list_user_sessions.return_value = mock_sessions
            
            # Act
            response = self.client.get("/api/conversations/sessions")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "Session 1"
            assert data[1]["title"] == "Session 2"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_get_session_success(self, mock_get_db, mock_get_current_user):
        """Test successful session retrieval via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_session.return_value = mock_session
            
            # Act
            response = self.client.get(f"/api/conversations/sessions/{self.session_id}")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(self.session_id)
            assert data["title"] == "Test Session"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_get_session_not_found(self, mock_get_db, mock_get_current_user):
        """Test session retrieval when session doesn't exist."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_session.return_value = None
            
            # Act
            response = self.client.get(f"/api/conversations/sessions/{self.session_id}")
            
            # Assert
            assert response.status_code == 404
            assert "Session not found or access denied" in response.json()["detail"]
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_update_session_success(self, mock_get_db, mock_get_current_user):
        """Test successful session update via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Updated Session"
        )
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.update_session.return_value = mock_session
            
            # Act
            response = self.client.put(
                f"/api/conversations/sessions/{self.session_id}",
                params={"title": "Updated Session", "is_shared": True}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Session"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_delete_session_success(self, mock_get_db, mock_get_current_user):
        """Test successful session deletion via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.delete_session.return_value = True
            
            # Act
            response = self.client.delete(f"/api/conversations/sessions/{self.session_id}")
            
            # Assert
            assert response.status_code == 200
            assert response.json()["message"] == "Session deleted successfully"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_add_message_success(self, mock_get_db, mock_get_current_user):
        """Test successful message addition via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        message_id = uuid.uuid4()
        mock_message = Message(
            id=message_id,
            session_id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            role="user",
            content="Hello, bot!",
            created_at=datetime.utcnow()
        )
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.add_message.return_value = mock_message
            
            # Act
            response = self.client.post(
                "/api/conversations/messages",
                json={
                    "session_id": str(self.session_id),
                    "role": "user",
                    "content": "Hello, bot!"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(message_id)
            assert data["content"] == "Hello, bot!"
            assert data["role"] == "user"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_get_session_messages_success(self, mock_get_db, mock_get_current_user):
        """Test successful message retrieval via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_messages = [
            Message(id=uuid.uuid4(), session_id=self.session_id, role="user", content="Hello"),
            Message(id=uuid.uuid4(), session_id=self.session_id, role="assistant", content="Hi there!")
        ]
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_session_messages.return_value = mock_messages
            
            # Act
            response = self.client.get(f"/api/conversations/sessions/{self.session_id}/messages")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["content"] == "Hello"
            assert data[1]["content"] == "Hi there!"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_search_conversations_success(self, mock_get_db, mock_get_current_user):
        """Test successful conversation search via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_results = [
            {
                "message_id": str(uuid.uuid4()),
                "session_id": str(self.session_id),
                "bot_id": str(self.bot_id),
                "bot_name": "Test Bot",
                "session_title": "Test Session",
                "role": "user",
                "content": "Test message",
                "created_at": datetime.utcnow(),
                "metadata": None
            }
        ]
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.search_conversations.return_value = mock_results
            
            # Act
            response = self.client.get("/api/conversations/search?q=test")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test"
            assert len(data["results"]) == 1
            assert data["results"][0]["content"] == "Test message"
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_export_conversations_success(self, mock_get_db, mock_get_current_user):
        """Test successful conversation export via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_export_data = {
            "conversations": [
                {
                    "session_id": str(self.session_id),
                    "bot_id": str(self.bot_id),
                    "title": "Test Session",
                    "messages": [
                        {
                            "message_id": str(uuid.uuid4()),
                            "role": "user",
                            "content": "Hello",
                            "created_at": datetime.utcnow().isoformat()
                        }
                    ]
                }
            ],
            "metadata": {
                "total_sessions": 1,
                "total_messages": 1,
                "export_timestamp": datetime.utcnow().isoformat(),
                "format": "json"
            }
        }
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.export_conversations.return_value = mock_export_data
            
            # Act
            response = self.client.get("/api/conversations/export")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "conversations" in data
            assert "metadata" in data
            assert data["metadata"]["total_sessions"] == 1
            assert data["metadata"]["total_messages"] == 1
    
    @patch('app.api.conversations.get_current_user')
    @patch('app.api.conversations.get_db')
    def test_get_conversation_analytics_success(self, mock_get_db, mock_get_current_user):
        """Test successful conversation analytics via API."""
        # Arrange
        mock_get_current_user.return_value = self.mock_user
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_analytics = {
            "total_sessions": 5,
            "total_messages": 25,
            "recent_activity": [
                {
                    "session_id": str(self.session_id),
                    "bot_id": str(self.bot_id),
                    "title": "Recent Session",
                    "updated_at": datetime.utcnow().isoformat()
                }
            ],
            "bot_usage": [
                {
                    "bot_id": str(self.bot_id),
                    "bot_name": "Test Bot",
                    "session_count": 5,
                    "message_count": 25
                }
            ]
        }
        
        with patch('app.services.conversation_service.ConversationService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_conversation_analytics.return_value = mock_analytics
            
            # Act
            response = self.client.get("/api/conversations/analytics")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["total_sessions"] == 5
            assert data["total_messages"] == 25
            assert len(data["recent_activity"]) == 1
            assert len(data["bot_usage"]) == 1