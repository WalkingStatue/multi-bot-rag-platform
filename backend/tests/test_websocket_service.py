"""
Tests for WebSocket service functionality.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.services.websocket_service import ConnectionManager, WebSocketService, connection_manager
from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.core.security import create_access_token


class TestConnectionManager:
    """Test cases for ConnectionManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance for each test."""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_user(self, manager, mock_websocket):
        """Test connecting a user to WebSocket."""
        user_id = str(uuid.uuid4())
        bot_id = str(uuid.uuid4())
        
        connection_id = await manager.connect(mock_websocket, user_id, bot_id)
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify connection is stored
        assert user_id in manager.active_connections
        assert connection_id in manager.active_connections[user_id]
        assert manager.active_connections[user_id][connection_id] == mock_websocket
        
        # Verify metadata is stored
        assert connection_id in manager.connection_metadata
        metadata = manager.connection_metadata[connection_id]
        assert metadata["user_id"] == user_id
        assert metadata["bot_id"] == bot_id
        
        # Verify bot subscription
        assert bot_id in manager.bot_subscriptions
        assert user_id in manager.bot_subscriptions[bot_id]
    
    @pytest.mark.asyncio
    async def test_connect_user_without_bot(self, manager, mock_websocket):
        """Test connecting a user without bot subscription."""
        user_id = str(uuid.uuid4())
        
        connection_id = await manager.connect(mock_websocket, user_id)
        
        # Verify connection is stored
        assert user_id in manager.active_connections
        assert connection_id in manager.active_connections[user_id]
        
        # Verify no bot subscription
        assert len(manager.bot_subscriptions) == 0
    
    def test_disconnect_user(self, manager):
        """Test disconnecting a user."""
        user_id = str(uuid.uuid4())
        bot_id = str(uuid.uuid4())
        connection_id = str(uuid.uuid4())
        
        # Manually set up connection
        manager.active_connections[user_id] = {connection_id: Mock()}
        manager.connection_metadata[connection_id] = {
            "user_id": user_id,
            "bot_id": bot_id,
            "connected_at": datetime.utcnow().isoformat()
        }
        manager.bot_subscriptions[bot_id] = {user_id}
        
        # Disconnect
        manager.disconnect(connection_id)
        
        # Verify cleanup
        assert user_id not in manager.active_connections
        assert connection_id not in manager.connection_metadata
        assert bot_id not in manager.bot_subscriptions
    
    def test_disconnect_nonexistent_connection(self, manager):
        """Test disconnecting a non-existent connection."""
        # Should not raise exception
        manager.disconnect("nonexistent-id")
    
    @pytest.mark.asyncio
    async def test_send_to_user(self, manager, mock_websocket):
        """Test sending message to a specific user."""
        user_id = str(uuid.uuid4())
        connection_id = str(uuid.uuid4())
        
        # Set up connection
        manager.active_connections[user_id] = {connection_id: mock_websocket}
        
        message = {"type": "test", "data": "hello"}
        result = await manager.send_to_user(user_id, message)
        
        # Verify message was sent
        assert result is True
        mock_websocket.send_text.assert_called_once_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self, manager):
        """Test sending message to non-existent user."""
        result = await manager.send_to_user("nonexistent-user", {"test": "data"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_to_user_with_failed_connection(self, manager):
        """Test sending message when WebSocket connection fails."""
        user_id = str(uuid.uuid4())
        connection_id = str(uuid.uuid4())
        
        # Create mock that raises exception
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Set up connection
        manager.active_connections[user_id] = {connection_id: mock_websocket}
        manager.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        message = {"type": "test", "data": "hello"}
        result = await manager.send_to_user(user_id, message)
        
        # Should return False and clean up failed connection
        assert result is False
        assert user_id not in manager.active_connections
        assert connection_id not in manager.connection_metadata
    
    @pytest.mark.asyncio
    async def test_broadcast_to_bot_collaborators(self, manager):
        """Test broadcasting message to bot collaborators."""
        bot_id = str(uuid.uuid4())
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        exclude_user = str(uuid.uuid4())
        
        # Set up connections
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock()
        mock_ws_exclude = Mock(spec=WebSocket)
        mock_ws_exclude.send_text = AsyncMock()
        
        manager.active_connections = {
            user1_id: {"conn1": mock_ws1},
            user2_id: {"conn2": mock_ws2},
            exclude_user: {"conn3": mock_ws_exclude}
        }
        manager.bot_subscriptions[bot_id] = {user1_id, user2_id, exclude_user}
        
        message = {"type": "broadcast", "data": "hello"}
        sent_count = await manager.broadcast_to_bot_collaborators(
            bot_id, message, exclude_user
        )
        
        # Verify message was sent to non-excluded users
        assert sent_count == 2
        mock_ws1.send_text.assert_called_once_with(json.dumps(message))
        mock_ws2.send_text.assert_called_once_with(json.dumps(message))
        mock_ws_exclude.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_notification(self, manager, mock_websocket):
        """Test sending notification to user."""
        user_id = str(uuid.uuid4())
        connection_id = str(uuid.uuid4())
        
        # Set up connection
        manager.active_connections[user_id] = {connection_id: mock_websocket}
        
        result = await manager.send_notification(
            user_id, "test_notification", {"message": "test"}
        )
        
        assert result is True
        mock_websocket.send_text.assert_called_once()
        
        # Verify notification format
        call_args = mock_websocket.send_text.call_args[0][0]
        notification = json.loads(call_args)
        assert notification["type"] == "notification"
        assert notification["notification_type"] == "test_notification"
        assert notification["data"]["message"] == "test"
    
    def test_get_connected_users(self, manager):
        """Test getting list of connected users."""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        manager.active_connections = {
            user1_id: {"conn1": Mock()},
            user2_id: {"conn2": Mock()}
        }
        
        connected_users = manager.get_connected_users()
        assert set(connected_users) == {user1_id, user2_id}
    
    def test_get_bot_subscribers(self, manager):
        """Test getting bot subscribers."""
        bot_id = str(uuid.uuid4())
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        manager.bot_subscriptions[bot_id] = {user1_id, user2_id}
        
        subscribers = manager.get_bot_subscribers(bot_id)
        assert set(subscribers) == {user1_id, user2_id}
    
    def test_get_connection_count(self, manager):
        """Test getting total connection count."""
        manager.active_connections = {
            "user1": {"conn1": Mock(), "conn2": Mock()},
            "user2": {"conn3": Mock()}
        }
        
        assert manager.get_connection_count() == 3
    
    def test_get_user_connection_count(self, manager):
        """Test getting connection count for specific user."""
        user_id = "user1"
        manager.active_connections = {
            user_id: {"conn1": Mock(), "conn2": Mock()},
            "user2": {"conn3": Mock()}
        }
        
        assert manager.get_user_connection_count(user_id) == 2
        assert manager.get_user_connection_count("nonexistent") == 0


class TestWebSocketService:
    """Test cases for WebSocketService class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def websocket_service(self, mock_db):
        """Create WebSocketService instance."""
        return WebSocketService(mock_db)
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = uuid.uuid4()
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = Mock(spec=Bot)
        bot.id = uuid.uuid4()
        bot.name = "Test Bot"
        bot.owner_id = uuid.uuid4()
        return bot
    
    @pytest.mark.asyncio
    async def test_authenticate_websocket_success(self, websocket_service, mock_websocket, mock_user, mock_db):
        """Test successful WebSocket authentication."""
        # Create valid token
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.websocket_service.verify_token') as mock_decode:
            mock_decode.return_value = {"sub": str(mock_user.id)}
            
            result = await websocket_service.authenticate_websocket(mock_websocket, token)
            
            assert result == mock_user
            mock_websocket.close.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_websocket_no_token(self, websocket_service, mock_websocket):
        """Test WebSocket authentication without token."""
        result = await websocket_service.authenticate_websocket(mock_websocket, None)
        
        assert result is None
        mock_websocket.close.assert_called_once_with(code=4001, reason="Authentication required")
    
    @pytest.mark.asyncio
    async def test_authenticate_websocket_invalid_token(self, websocket_service, mock_websocket):
        """Test WebSocket authentication with invalid token."""
        with patch('app.services.websocket_service.verify_token') as mock_decode:
            mock_decode.return_value = None
            
            result = await websocket_service.authenticate_websocket(mock_websocket, "invalid_token")
            
            assert result is None
            mock_websocket.close.assert_called_once_with(code=4001, reason="Invalid token")
    
    @pytest.mark.asyncio
    async def test_authenticate_websocket_user_not_found(self, websocket_service, mock_websocket, mock_db):
        """Test WebSocket authentication when user not found."""
        user_id = str(uuid.uuid4())
        
        # Mock database query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.websocket_service.verify_token') as mock_decode:
            mock_decode.return_value = {"sub": user_id}
            
            result = await websocket_service.authenticate_websocket(mock_websocket, "valid_token")
            
            assert result is None
            mock_websocket.close.assert_called_once_with(code=4001, reason="User not found or inactive")
    
    @pytest.mark.asyncio
    async def test_verify_bot_access_success(self, websocket_service, mock_user, mock_bot, mock_db):
        """Test successful bot access verification."""
        bot_id = str(mock_bot.id)
        
        # Mock permission check
        websocket_service.permission_service.check_bot_permission = Mock(return_value=True)
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
        
        result = await websocket_service.verify_bot_access(mock_user, bot_id)
        
        assert result == mock_bot
        websocket_service.permission_service.check_bot_permission.assert_called_once_with(
            mock_user.id, mock_bot.id, "view_bot"
        )
    
    @pytest.mark.asyncio
    async def test_verify_bot_access_no_permission(self, websocket_service, mock_user, mock_bot):
        """Test bot access verification without permission."""
        bot_id = str(mock_bot.id)
        
        # Mock permission check to return False
        websocket_service.permission_service.check_bot_permission = Mock(return_value=False)
        
        result = await websocket_service.verify_bot_access(mock_user, bot_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_verify_bot_access_invalid_bot_id(self, websocket_service, mock_user):
        """Test bot access verification with invalid bot ID."""
        result = await websocket_service.verify_bot_access(mock_user, "invalid-uuid")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_chat_message(self, websocket_service):
        """Test handling chat message broadcast."""
        bot_id = str(uuid.uuid4())
        sender_user_id = str(uuid.uuid4())
        message_data = {"content": "Hello", "user": "testuser"}
        
        with patch('app.services.websocket_service.connection_manager') as mock_manager:
            mock_manager.broadcast_to_bot_collaborators = AsyncMock()
            
            await websocket_service.handle_chat_message(bot_id, message_data, sender_user_id)
            
            mock_manager.broadcast_to_bot_collaborators.assert_called_once()
            call_args = mock_manager.broadcast_to_bot_collaborators.call_args
            
            assert call_args[1]["bot_id"] == bot_id
            assert call_args[1]["exclude_user"] == sender_user_id
            assert call_args[1]["message"]["type"] == "chat_message"
            assert call_args[1]["message"]["data"] == message_data
    
    @pytest.mark.asyncio
    async def test_handle_typing_indicator(self, websocket_service):
        """Test handling typing indicator broadcast."""
        bot_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        username = "testuser"
        is_typing = True
        
        with patch('app.services.websocket_service.connection_manager') as mock_manager:
            mock_manager.broadcast_to_bot_collaborators = AsyncMock()
            
            await websocket_service.handle_typing_indicator(bot_id, user_id, username, is_typing)
            
            mock_manager.broadcast_to_bot_collaborators.assert_called_once()
            call_args = mock_manager.broadcast_to_bot_collaborators.call_args
            
            assert call_args[1]["bot_id"] == bot_id
            assert call_args[1]["exclude_user"] == user_id
            assert call_args[1]["message"]["type"] == "typing_indicator"
            assert call_args[1]["message"]["data"]["is_typing"] == is_typing
    
    @pytest.mark.asyncio
    async def test_handle_permission_change(self, websocket_service):
        """Test handling permission change notifications."""
        bot_id = str(uuid.uuid4())
        target_user_id = str(uuid.uuid4())
        action = "granted"
        details = {"role": "editor"}
        
        with patch('app.services.websocket_service.connection_manager') as mock_manager:
            mock_manager.send_notification = AsyncMock()
            mock_manager.broadcast_to_bot_collaborators = AsyncMock()
            
            await websocket_service.handle_permission_change(bot_id, target_user_id, action, details)
            
            # Verify notification was sent to target user
            mock_manager.send_notification.assert_called_once_with(
                user_id=target_user_id,
                notification_type="permission_change",
                data={
                    "bot_id": bot_id,
                    "action": action,
                    "details": details
                }
            )
            
            # Verify broadcast to collaborators
            mock_manager.broadcast_to_bot_collaborators.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_bot_update(self, websocket_service):
        """Test handling bot update notifications."""
        bot_id = str(uuid.uuid4())
        update_type = "config"
        details = {"name": "New Name"}
        updated_by = str(uuid.uuid4())
        
        with patch('app.services.websocket_service.connection_manager') as mock_manager:
            mock_manager.broadcast_to_bot_collaborators = AsyncMock()
            
            await websocket_service.handle_bot_update(bot_id, update_type, details, updated_by)
            
            mock_manager.broadcast_to_bot_collaborators.assert_called_once()
            call_args = mock_manager.broadcast_to_bot_collaborators.call_args
            
            assert call_args[1]["bot_id"] == bot_id
            assert call_args[1]["exclude_user"] == updated_by
            assert call_args[1]["message"]["type"] == "bot_update"
    
    @pytest.mark.asyncio
    async def test_handle_document_update(self, websocket_service):
        """Test handling document update notifications."""
        bot_id = str(uuid.uuid4())
        action = "uploaded"
        document_data = {"id": str(uuid.uuid4()), "name": "test.pdf"}
        user_id = str(uuid.uuid4())
        
        with patch('app.services.websocket_service.connection_manager') as mock_manager:
            mock_manager.broadcast_to_bot_collaborators = AsyncMock()
            
            await websocket_service.handle_document_update(bot_id, action, document_data, user_id)
            
            mock_manager.broadcast_to_bot_collaborators.assert_called_once()
            call_args = mock_manager.broadcast_to_bot_collaborators.call_args
            
            assert call_args[1]["bot_id"] == bot_id
            assert call_args[1]["exclude_user"] == user_id
            assert call_args[1]["message"]["type"] == "document_update"
            assert call_args[1]["message"]["data"]["action"] == action


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self):
        """Test complete WebSocket connection lifecycle."""
        manager = ConnectionManager()
        user_id = str(uuid.uuid4())
        bot_id = str(uuid.uuid4())
        
        # Mock WebSocket
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Connect
        connection_id = await manager.connect(mock_websocket, user_id, bot_id)
        
        # Verify connection state
        assert manager.get_user_connection_count(user_id) == 1
        assert user_id in manager.get_bot_subscribers(bot_id)
        
        # Send message
        message = {"type": "test", "data": "hello"}
        result = await manager.send_to_user(user_id, message)
        assert result is True
        
        # Disconnect
        manager.disconnect(connection_id)
        
        # Verify cleanup
        assert manager.get_user_connection_count(user_id) == 0
        assert user_id not in manager.get_bot_subscribers(bot_id)
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self):
        """Test multiple connections for the same user."""
        manager = ConnectionManager()
        user_id = str(uuid.uuid4())
        
        # Create multiple mock WebSockets
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock()
        
        # Connect both
        conn1_id = await manager.connect(mock_ws1, user_id)
        conn2_id = await manager.connect(mock_ws2, user_id)
        
        # Verify both connections exist
        assert manager.get_user_connection_count(user_id) == 2
        
        # Send message should reach both connections
        message = {"type": "test", "data": "hello"}
        result = await manager.send_to_user(user_id, message)
        assert result is True
        
        mock_ws1.send_text.assert_called_once_with(json.dumps(message))
        mock_ws2.send_text.assert_called_once_with(json.dumps(message))
        
        # Disconnect one
        manager.disconnect(conn1_id)
        assert manager.get_user_connection_count(user_id) == 1
        
        # Disconnect the other
        manager.disconnect(conn2_id)
        assert manager.get_user_connection_count(user_id) == 0


if __name__ == "__main__":
    pytest.main([__file__])