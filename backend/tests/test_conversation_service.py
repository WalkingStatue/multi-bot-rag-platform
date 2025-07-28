"""
Unit tests for conversation service.
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.services.conversation_service import ConversationService
from app.models.conversation import ConversationSession, Message
from app.models.bot import Bot
from app.models.user import User
from app.schemas.conversation import ConversationSessionCreate, MessageCreate


class TestConversationService:
    """Test cases for ConversationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = Mock(spec=Session)
        self.permission_service = Mock()
        self.service = ConversationService(self.db)
        self.service.permission_service = self.permission_service
        
        # Test data
        self.user_id = uuid.uuid4()
        self.bot_id = uuid.uuid4()
        self.session_id = uuid.uuid4()
        self.message_id = uuid.uuid4()
    
    def test_create_session_success(self):
        """Test successful session creation."""
        # Arrange
        self.permission_service.check_bot_permission.return_value = True
        session_data = ConversationSessionCreate(
            bot_id=self.bot_id,
            title="Test Session"
        )
        
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        self.db.add = Mock()
        self.db.commit = Mock()
        self.db.refresh = Mock()
        
        # Act
        result = self.service.create_session(self.user_id, session_data)
        
        # Assert
        self.permission_service.check_bot_permission.assert_called_once_with(
            self.user_id, self.bot_id, "view_conversations"
        )
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        assert result.bot_id == self.bot_id
        assert result.user_id == self.user_id
        assert result.title == "Test Session"
    
    def test_create_session_no_permission(self):
        """Test session creation without permission."""
        # Arrange
        self.permission_service.check_bot_permission.return_value = False
        session_data = ConversationSessionCreate(
            bot_id=self.bot_id,
            title="Test Session"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="User does not have permission to access this bot"):
            self.service.create_session(self.user_id, session_data)
    
    def test_get_session_success(self):
        """Test successful session retrieval."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.return_value = True
        
        # Act
        result = self.service.get_session(self.session_id, self.user_id)
        
        # Assert
        assert result == mock_session
        self.permission_service.check_bot_permission.assert_called_once_with(
            self.user_id, self.bot_id, "view_conversations"
        )
    
    def test_get_session_not_found(self):
        """Test session retrieval when session doesn't exist."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.service.get_session(self.session_id, self.user_id)
        
        # Assert
        assert result is None
    
    def test_get_session_no_permission(self):
        """Test session retrieval without permission."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.return_value = False
        
        # Act
        result = self.service.get_session(self.session_id, self.user_id)
        
        # Assert
        assert result is None
    
    def test_list_user_sessions_success(self):
        """Test successful session listing."""
        # Arrange
        accessible_bot_ids = [self.bot_id, uuid.uuid4()]
        self.permission_service.get_user_accessible_bot_ids.return_value = accessible_bot_ids
        
        mock_sessions = [
            ConversationSession(id=uuid.uuid4(), bot_id=self.bot_id, user_id=self.user_id),
            ConversationSession(id=uuid.uuid4(), bot_id=self.bot_id, user_id=self.user_id)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_sessions
        
        self.db.query.return_value = mock_query
        
        # Act
        result = self.service.list_user_sessions(self.user_id, limit=10, offset=0)
        
        # Assert
        assert result == mock_sessions
        self.permission_service.get_user_accessible_bot_ids.assert_called_once_with(self.user_id)
    
    def test_list_user_sessions_no_accessible_bots(self):
        """Test session listing when user has no accessible bots."""
        # Arrange
        self.permission_service.get_user_accessible_bot_ids.return_value = []
        
        # Act
        result = self.service.list_user_sessions(self.user_id)
        
        # Assert
        assert result == []
    
    def test_update_session_success(self):
        """Test successful session update."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Old Title"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.side_effect = [True, True]  # First for get_session, second for edit permission
        self.db.commit = Mock()
        self.db.refresh = Mock()
        
        # Act
        result = self.service.update_session(
            self.session_id, self.user_id, title="New Title", is_shared=True
        )
        
        # Assert
        assert result.title == "New Title"
        assert result.is_shared == True
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
    
    def test_update_session_no_permission(self):
        """Test session update without permission."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Old Title"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.side_effect = [True, False]  # First for get_session, second for edit permission
        
        # Act & Assert
        with pytest.raises(ValueError, match="User does not have permission to edit this session"):
            self.service.update_session(self.session_id, self.user_id, title="New Title")
    
    def test_delete_session_success_as_owner(self):
        """Test successful session deletion as session owner."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.return_value = True
        self.db.delete = Mock()
        self.db.commit = Mock()
        
        # Act
        result = self.service.delete_session(self.session_id, self.user_id)
        
        # Assert
        assert result == True
        self.db.delete.assert_called_once_with(mock_session)
        self.db.commit.assert_called_once()
    
    def test_delete_session_success_as_admin(self):
        """Test successful session deletion as bot admin."""
        # Arrange
        other_user_id = uuid.uuid4()
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=other_user_id,
            title="Test Session"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.return_value = True
        self.permission_service.check_bot_role.return_value = True
        self.db.delete = Mock()
        self.db.commit = Mock()
        
        # Act
        result = self.service.delete_session(self.session_id, self.user_id)
        
        # Assert
        assert result == True
        self.db.delete.assert_called_once_with(mock_session)
        self.db.commit.assert_called_once()
    
    def test_delete_session_no_permission(self):
        """Test session deletion without permission."""
        # Arrange
        other_user_id = uuid.uuid4()
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=other_user_id,
            title="Test Session"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.return_value = True
        self.permission_service.check_bot_role.return_value = False
        
        # Act & Assert
        with pytest.raises(ValueError, match="User does not have permission to delete this session"):
            self.service.delete_session(self.session_id, self.user_id)
    
    def test_add_message_success(self):
        """Test successful message addition."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        message_data = MessageCreate(
            session_id=self.session_id,
            role="user",
            content="Hello, bot!"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.return_value = True
        self.db.add = Mock()
        self.db.commit = Mock()
        self.db.refresh = Mock()
        
        # Act
        result = self.service.add_message(self.user_id, message_data)
        
        # Assert
        assert result.session_id == self.session_id
        assert result.bot_id == self.bot_id
        assert result.user_id == self.user_id
        assert result.role == "user"
        assert result.content == "Hello, bot!"
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
    
    def test_add_message_session_not_found(self):
        """Test message addition when session doesn't exist."""
        # Arrange
        message_data = MessageCreate(
            session_id=self.session_id,
            role="user",
            content="Hello, bot!"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            self.service.add_message(self.user_id, message_data)
    
    def test_get_session_messages_success(self):
        """Test successful message retrieval."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session"
        )
        
        mock_messages = [
            Message(id=uuid.uuid4(), session_id=self.session_id, role="user", content="Hello"),
            Message(id=uuid.uuid4(), session_id=self.session_id, role="assistant", content="Hi there!")
        ]
        
        # Mock get_session call
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        self.permission_service.check_bot_permission.return_value = True
        
        # Mock messages query
        mock_messages_query = Mock()
        mock_messages_query.filter.return_value = mock_messages_query
        mock_messages_query.order_by.return_value = mock_messages_query
        mock_messages_query.offset.return_value = mock_messages_query
        mock_messages_query.limit.return_value = mock_messages_query
        mock_messages_query.all.return_value = mock_messages
        
        self.db.query.side_effect = [
            Mock(return_value=Mock(filter=Mock(return_value=Mock(first=Mock(return_value=mock_session))))),
            mock_messages_query
        ]
        
        # Act
        result = self.service.get_session_messages(self.session_id, self.user_id, limit=10, offset=0)
        
        # Assert
        assert result == mock_messages
    
    def test_search_conversations_success(self):
        """Test successful conversation search."""
        # Arrange
        accessible_bot_ids = [self.bot_id, uuid.uuid4()]
        self.permission_service.get_user_accessible_bot_ids.return_value = accessible_bot_ids
        
        mock_results = [
            (
                Message(id=self.message_id, content="Test message", role="user", created_at=datetime.utcnow()),
                "Test Session",
                "Test Bot"
            )
        ]
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_results
        
        self.db.query.return_value = mock_query
        
        # Act
        result = self.service.search_conversations(self.user_id, "test", limit=10, offset=0)
        
        # Assert
        assert len(result) == 1
        assert result[0]["content"] == "Test message"
        assert result[0]["session_title"] == "Test Session"
        assert result[0]["bot_name"] == "Test Bot"
    
    def test_search_conversations_no_accessible_bots(self):
        """Test conversation search when user has no accessible bots."""
        # Arrange
        self.permission_service.get_user_accessible_bot_ids.return_value = []
        
        # Act
        result = self.service.search_conversations(self.user_id, "test")
        
        # Assert
        assert result == []
    
    def test_export_conversations_success(self):
        """Test successful conversation export."""
        # Arrange
        accessible_bot_ids = [self.bot_id]
        self.permission_service.get_user_accessible_bot_ids.return_value = accessible_bot_ids
        
        mock_session = ConversationSession(
            id=self.session_id,
            bot_id=self.bot_id,
            user_id=self.user_id,
            title="Test Session",
            is_shared=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_message = Message(
            id=self.message_id,
            session_id=self.session_id,
            role="user",
            content="Test message",
            message_metadata={"test": "data"},
            created_at=datetime.utcnow()
        )
        
        # Mock sessions query
        mock_sessions_query = Mock()
        mock_sessions_query.filter.return_value = mock_sessions_query
        mock_sessions_query.order_by.return_value = mock_sessions_query
        mock_sessions_query.all.return_value = [mock_session]
        
        # Mock messages query
        mock_messages_query = Mock()
        mock_messages_query.filter.return_value = mock_messages_query
        mock_messages_query.order_by.return_value = mock_messages_query
        mock_messages_query.all.return_value = [mock_message]
        
        self.db.query.side_effect = [mock_sessions_query, mock_messages_query]
        
        # Act
        result = self.service.export_conversations(self.user_id)
        
        # Assert
        assert "conversations" in result
        assert "metadata" in result
        assert result["metadata"]["total_sessions"] == 1
        assert result["metadata"]["total_messages"] == 1
        assert len(result["conversations"]) == 1
        assert result["conversations"][0]["title"] == "Test Session"
        assert len(result["conversations"][0]["messages"]) == 1
    
    def test_get_conversation_analytics_success(self):
        """Test successful conversation analytics retrieval."""
        # Arrange
        accessible_bot_ids = [self.bot_id]
        self.permission_service.get_user_accessible_bot_ids.return_value = accessible_bot_ids
        
        # Mock session count query
        mock_session_count_query = Mock()
        mock_session_count_query.filter.return_value = mock_session_count_query
        mock_session_count_query.count.return_value = 5
        
        # Mock message count query
        mock_message_count_query = Mock()
        mock_message_count_query.filter.return_value = mock_message_count_query
        mock_message_count_query.count.return_value = 25
        
        # Mock recent sessions query
        mock_recent_sessions_query = Mock()
        mock_recent_sessions_query.filter.return_value = mock_recent_sessions_query
        mock_recent_sessions_query.order_by.return_value = mock_recent_sessions_query
        mock_recent_sessions_query.limit.return_value = mock_recent_sessions_query
        mock_recent_sessions_query.all.return_value = [
            ConversationSession(
                id=self.session_id,
                bot_id=self.bot_id,
                title="Recent Session",
                updated_at=datetime.utcnow()
            )
        ]
        
        # Mock bot usage query
        mock_bot_usage_query = Mock()
        mock_bot_usage_query.outerjoin.return_value = mock_bot_usage_query
        mock_bot_usage_query.filter.return_value = mock_bot_usage_query
        mock_bot_usage_query.group_by.return_value = mock_bot_usage_query
        mock_bot_usage_query.all.return_value = [
            (self.bot_id, "Test Bot", 5, 25)
        ]
        
        self.db.query.side_effect = [
            mock_session_count_query,
            mock_message_count_query,
            mock_recent_sessions_query,
            mock_bot_usage_query
        ]
        
        # Act
        result = self.service.get_conversation_analytics(self.user_id)
        
        # Assert
        assert result["total_sessions"] == 5
        assert result["total_messages"] == 25
        assert len(result["recent_activity"]) == 1
        assert len(result["bot_usage"]) == 1
        assert result["bot_usage"][0]["bot_name"] == "Test Bot"
        assert result["bot_usage"][0]["session_count"] == 5
        assert result["bot_usage"][0]["message_count"] == 25