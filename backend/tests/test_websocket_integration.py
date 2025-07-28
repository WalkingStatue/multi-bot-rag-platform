"""
Integration tests for WebSocket functionality.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import uuid

from app.services.websocket_service import ConnectionManager, WebSocketService
from app.models.user import User
from app.models.bot import Bot


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_complete_websocket_workflow(self):
        """Test complete WebSocket workflow from connection to notification."""
        # Create connection manager
        manager = ConnectionManager()
        
        # Mock WebSocket connections
        user1_ws = Mock()
        user1_ws.accept = AsyncMock()
        user1_ws.send_text = AsyncMock()
        
        user2_ws = Mock()
        user2_ws.accept = AsyncMock()
        user2_ws.send_text = AsyncMock()
        
        # Test data
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        bot_id = str(uuid.uuid4())
        
        # Step 1: Connect users to bot
        conn1_id = await manager.connect(user1_ws, user1_id, bot_id)
        conn2_id = await manager.connect(user2_ws, user2_id, bot_id)
        
        # Verify connections
        assert manager.get_user_connection_count(user1_id) == 1
        assert manager.get_user_connection_count(user2_id) == 1
        assert len(manager.get_bot_subscribers(bot_id)) == 2
        
        # Step 2: Send chat message notification
        chat_message = {
            "type": "chat_message",
            "bot_id": bot_id,
            "data": {
                "message_id": str(uuid.uuid4()),
                "content": "Hello from user1",
                "user_id": user1_id,
                "username": "user1"
            }
        }
        
        sent_count = await manager.broadcast_to_bot_collaborators(
            bot_id=bot_id,
            message=chat_message,
            exclude_user=user1_id
        )
        
        # Verify broadcast (should reach user2 but not user1)
        assert sent_count == 1
        user2_ws.send_text.assert_called_once_with(json.dumps(chat_message))
        user1_ws.send_text.assert_not_called()
        
        # Step 3: Send notification to specific user
        notification_sent = await manager.send_notification(
            user_id=user2_id,
            notification_type="permission_change",
            data={"bot_id": bot_id, "action": "granted", "role": "editor"}
        )
        
        assert notification_sent is True
        
        # Step 4: Disconnect users
        manager.disconnect(conn1_id)
        manager.disconnect(conn2_id)
        
        # Verify cleanup
        assert manager.get_user_connection_count(user1_id) == 0
        assert manager.get_user_connection_count(user2_id) == 0
        assert len(manager.get_bot_subscribers(bot_id)) == 0
    
    @pytest.mark.asyncio
    async def test_websocket_service_with_permission_checking(self):
        """Test WebSocket service with permission checking."""
        # Mock database session
        mock_db = Mock()
        
        # Create WebSocket service
        service = WebSocketService(mock_db)
        
        # Mock user and bot
        mock_user = Mock(spec=User)
        mock_user.id = uuid.uuid4()
        mock_user.username = "testuser"
        mock_user.is_active = True
        
        mock_bot = Mock(spec=Bot)
        mock_bot.id = uuid.uuid4()
        mock_bot.name = "Test Bot"
        
        # Mock permission service
        service.permission_service.check_bot_permission = Mock(return_value=True)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
        
        # Test bot access verification
        result = await service.verify_bot_access(mock_user, str(mock_bot.id))
        
        assert result == mock_bot
        service.permission_service.check_bot_permission.assert_called_once_with(
            mock_user.id, mock_bot.id, "view_bot"
        )
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling and connection cleanup."""
        manager = ConnectionManager()
        
        # Create mock WebSocket that fails on send
        failing_ws = Mock()
        failing_ws.accept = AsyncMock()
        failing_ws.send_text = AsyncMock(side_effect=Exception("Connection failed"))
        
        user_id = str(uuid.uuid4())
        bot_id = str(uuid.uuid4())
        
        # Connect user
        conn_id = await manager.connect(failing_ws, user_id, bot_id)
        
        # Verify connection exists
        assert manager.get_user_connection_count(user_id) == 1
        
        # Try to send message (should fail and clean up connection)
        result = await manager.send_to_user(user_id, {"test": "message"})
        
        # Verify failure and cleanup
        assert result is False
        assert manager.get_user_connection_count(user_id) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_bot_subscriptions(self):
        """Test user subscribed to multiple bots."""
        manager = ConnectionManager()
        
        user_id = str(uuid.uuid4())
        bot1_id = str(uuid.uuid4())
        bot2_id = str(uuid.uuid4())
        
        # Mock WebSockets
        ws1 = Mock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        
        ws2 = Mock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        
        # Connect to different bots
        conn1_id = await manager.connect(ws1, user_id, bot1_id)
        conn2_id = await manager.connect(ws2, user_id, bot2_id)
        
        # Verify subscriptions
        assert user_id in manager.get_bot_subscribers(bot1_id)
        assert user_id in manager.get_bot_subscribers(bot2_id)
        assert manager.get_user_connection_count(user_id) == 2
        
        # Send message to bot1 - should reach both connections since same user is subscribed to bot1
        message1 = {"type": "test", "bot_id": bot1_id, "data": "message for bot1"}
        sent_count = await manager.broadcast_to_bot_collaborators(bot1_id, message1)
        
        # Both connections should receive the message since it's the same user
        assert sent_count == 2
        ws1.send_text.assert_called_with(json.dumps(message1))
        ws2.send_text.assert_called_with(json.dumps(message1))
        
        # Reset mocks
        ws1.send_text.reset_mock()
        ws2.send_text.reset_mock()
        
        # Send message to bot2 - should reach both connections since same user is subscribed to bot2
        message2 = {"type": "test", "bot_id": bot2_id, "data": "message for bot2"}
        sent_count = await manager.broadcast_to_bot_collaborators(bot2_id, message2)
        
        # Both connections should receive the message since it's the same user
        assert sent_count == 2
        ws1.send_text.assert_called_with(json.dumps(message2))
        ws2.send_text.assert_called_with(json.dumps(message2))
        
        # Disconnect from bot1
        manager.disconnect(conn1_id)
        
        # Verify partial cleanup
        assert user_id not in manager.get_bot_subscribers(bot1_id)
        assert user_id in manager.get_bot_subscribers(bot2_id)
        assert manager.get_user_connection_count(user_id) == 1
        
        # Disconnect from bot2
        manager.disconnect(conn2_id)
        
        # Verify complete cleanup
        assert user_id not in manager.get_bot_subscribers(bot2_id)
        assert manager.get_user_connection_count(user_id) == 0
    
    def test_websocket_stats_and_monitoring(self):
        """Test WebSocket statistics and monitoring functions."""
        manager = ConnectionManager()
        
        # Add some test data
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        bot1_id = str(uuid.uuid4())
        bot2_id = str(uuid.uuid4())
        
        # Simulate connections
        manager.active_connections = {
            user1_id: {"conn1": Mock(), "conn2": Mock()},
            user2_id: {"conn3": Mock()}
        }
        
        manager.bot_subscriptions = {
            bot1_id: {user1_id, user2_id},
            bot2_id: {user1_id}
        }
        
        # Test statistics
        assert manager.get_connection_count() == 3
        assert len(manager.get_connected_users()) == 2
        assert manager.get_user_connection_count(user1_id) == 2
        assert manager.get_user_connection_count(user2_id) == 1
        assert len(manager.get_bot_subscribers(bot1_id)) == 2
        assert len(manager.get_bot_subscribers(bot2_id)) == 1


if __name__ == "__main__":
    pytest.main([__file__])