"""
Tests for conversation data isolation between bots.
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
import uuid

from app.services.conversation_service import ConversationService
from app.models.conversation import ConversationSession, Message
from app.schemas.conversation import ConversationSessionCreate, MessageCreate


class TestConversationDataIsolation:
    """Test cases for conversation data isolation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = Mock(spec=Session)
        self.permission_service = Mock()
        self.service = ConversationService(self.db)
        self.service.permission_service = self.permission_service
        
        # Test data for two different users and bots
        self.user1_id = uuid.uuid4()
        self.user2_id = uuid.uuid4()
        self.bot1_id = uuid.uuid4()
        self.bot2_id = uuid.uuid4()
        self.session1_id = uuid.uuid4()
        self.session2_id = uuid.uuid4()
    
    def test_user_can_only_see_accessible_bot_sessions(self):
        """Test that users can only see sessions from bots they have access to."""
        # Arrange
        # User 1 has access to bot1 only
        self.permission_service.get_user_accessible_bot_ids.return_value = [self.bot1_id]
        
        # Mock sessions from both bots
        all_sessions = [
            ConversationSession(id=self.session1_id, bot_id=self.bot1_id, user_id=self.user1_id),
            ConversationSession(id=self.session2_id, bot_id=self.bot2_id, user_id=self.user2_id)
        ]
        
        # Mock query to return only sessions from accessible bots
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [all_sessions[0]]  # Only bot1 session
        
        self.db.query.return_value = mock_query
        
        # Act
        result = self.service.list_user_sessions(self.user1_id)
        
        # Assert
        assert len(result) == 1
        assert result[0].bot_id == self.bot1_id
        self.permission_service.get_user_accessible_bot_ids.assert_called_once_with(self.user1_id)
    
    def test_search_only_searches_accessible_bots(self):
        """Test that conversation search only searches in accessible bots."""
        # Arrange
        # User 1 has access to bot1 only
        self.permission_service.get_user_accessible_bot_ids.return_value = [self.bot1_id]
        
        # Mock search results from accessible bot only
        mock_results = [
            (
                Message(id=uuid.uuid4(), bot_id=self.bot1_id, content="Test message", role="user"),
                "Test Session",
                "Test Bot 1"
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
        result = self.service.search_conversations(self.user1_id, "test")
        
        # Assert
        assert len(result) == 1
        assert result[0]["bot_name"] == "Test Bot 1"
        self.permission_service.get_user_accessible_bot_ids.assert_called_once_with(self.user1_id)
        
        # Verify that the query filters by accessible bot IDs
        # The filter call should include bot_id.in_([self.bot1_id])
        mock_query.filter.assert_called()
    
    def test_export_only_exports_accessible_bot_conversations(self):
        """Test that conversation export only includes accessible bot conversations."""
        # Arrange
        # User 1 has access to bot1 only
        self.permission_service.get_user_accessible_bot_ids.return_value = [self.bot1_id]
        
        # Mock session from accessible bot
        from datetime import datetime
        mock_session = ConversationSession(
            id=self.session1_id,
            bot_id=self.bot1_id,
            user_id=self.user1_id,
            title="Accessible Session",
            is_shared=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_message = Message(
            id=uuid.uuid4(),
            session_id=self.session1_id,
            bot_id=self.bot1_id,
            role="user",
            content="Test message",
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
        result = self.service.export_conversations(self.user1_id)
        
        # Assert
        assert "conversations" in result
        assert len(result["conversations"]) == 1
        assert result["conversations"][0]["bot_id"] == str(self.bot1_id)
        assert result["conversations"][0]["title"] == "Accessible Session"
        self.permission_service.get_user_accessible_bot_ids.assert_called_once_with(self.user1_id)
    
    def test_analytics_only_includes_accessible_bots(self):
        """Test that conversation analytics only includes accessible bots."""
        # Arrange
        # User 1 has access to bot1 only
        self.permission_service.get_user_accessible_bot_ids.return_value = [self.bot1_id]
        
        # Mock session count query
        mock_session_count_query = Mock()
        mock_session_count_query.filter.return_value = mock_session_count_query
        mock_session_count_query.count.return_value = 3
        
        # Mock message count query
        mock_message_count_query = Mock()
        mock_message_count_query.filter.return_value = mock_message_count_query
        mock_message_count_query.count.return_value = 15
        
        # Mock recent sessions query
        mock_recent_sessions_query = Mock()
        mock_recent_sessions_query.filter.return_value = mock_recent_sessions_query
        mock_recent_sessions_query.order_by.return_value = mock_recent_sessions_query
        mock_recent_sessions_query.limit.return_value = mock_recent_sessions_query
        from datetime import datetime
        mock_recent_sessions_query.all.return_value = [
            ConversationSession(
                id=self.session1_id, 
                bot_id=self.bot1_id, 
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
            (self.bot1_id, "Accessible Bot", 3, 15)
        ]
        
        self.db.query.side_effect = [
            mock_session_count_query,
            mock_message_count_query,
            mock_recent_sessions_query,
            mock_bot_usage_query
        ]
        
        # Act
        result = self.service.get_conversation_analytics(self.user1_id)
        
        # Assert
        assert result["total_sessions"] == 3
        assert result["total_messages"] == 15
        assert len(result["bot_usage"]) == 1
        assert result["bot_usage"][0]["bot_name"] == "Accessible Bot"
        self.permission_service.get_user_accessible_bot_ids.assert_called_once_with(self.user1_id)
    
    def test_session_access_requires_bot_permission(self):
        """Test that accessing a session requires permission to the associated bot."""
        # Arrange
        mock_session = ConversationSession(
            id=self.session1_id,
            bot_id=self.bot1_id,
            user_id=self.user1_id,
            title="Test Session"
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_session
        
        # User does not have permission to access the bot
        self.permission_service.check_bot_permission.return_value = False
        
        # Act
        result = self.service.get_session(self.session1_id, self.user2_id)
        
        # Assert
        assert result is None
        self.permission_service.check_bot_permission.assert_called_once_with(
            self.user2_id, self.bot1_id, "view_conversations"
        )
    
    def test_message_addition_requires_session_access(self):
        """Test that adding a message requires access to the session's bot."""
        # Arrange
        message_data = MessageCreate(
            session_id=self.session1_id,
            role="user",
            content="Hello, bot!"
        )
        
        # Session exists but user doesn't have access
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            self.service.add_message(self.user2_id, message_data)
    
    def test_no_cross_bot_data_leakage_in_search(self):
        """Test that search results don't leak data from inaccessible bots."""
        # Arrange
        # User has no accessible bots
        self.permission_service.get_user_accessible_bot_ids.return_value = []
        
        # Act
        result = self.service.search_conversations(self.user1_id, "test")
        
        # Assert
        assert result == []
        self.permission_service.get_user_accessible_bot_ids.assert_called_once_with(self.user1_id)
    
    def test_no_cross_bot_data_leakage_in_export(self):
        """Test that export doesn't leak data from inaccessible bots."""
        # Arrange
        # User has no accessible bots
        self.permission_service.get_user_accessible_bot_ids.return_value = []
        
        # Act
        result = self.service.export_conversations(self.user1_id)
        
        # Assert
        assert result["conversations"] == []
        assert result["metadata"]["total_sessions"] == 0
        assert result["metadata"]["total_messages"] == 0
        self.permission_service.get_user_accessible_bot_ids.assert_called_once_with(self.user1_id)