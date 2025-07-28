"""
Tests for WebSocket API endpoints.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket
import uuid

from main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.bot import Bot


class TestWebSocketEndpoints:
    """Test cases for WebSocket API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
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
    
    @pytest.fixture
    def valid_token(self, mock_user):
        """Create a valid JWT token."""
        return create_access_token(data={"sub": str(mock_user.id)})
    
    def test_websocket_stats_endpoint(self, client):
        """Test WebSocket stats endpoint."""
        with patch('app.services.websocket_service.connection_manager') as mock_manager:
            mock_manager.get_connection_count.return_value = 5
            mock_manager.get_connected_users.return_value = ["user1", "user2"]
            mock_manager.bot_subscriptions = {"bot1": {"user1"}}
            
            response = client.get("/api/ws/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_connections"] == 5
            assert data["connected_users"] == 2
            assert data["bot_subscriptions"] == 1
    
    def test_websocket_connections_endpoint(self, client):
        """Test WebSocket connections endpoint."""
        with patch('app.services.websocket_service.connection_manager') as mock_manager:
            mock_manager.get_connected_users.return_value = ["user1", "user2"]
            mock_manager.bot_subscriptions = {"bot1": {"user1"}}
            mock_manager.connection_metadata = {
                "conn1": {"user_id": "user1", "connected_at": "2023-01-01T00:00:00"}
            }
            
            response = client.get("/api/ws/connections")
            
            assert response.status_code == 200
            data = response.json()
            assert data["connected_users"] == ["user1", "user2"]
            assert data["bot_subscriptions"]["bot1"] == ["user1"]
            assert "conn1" in data["connection_metadata"]


class TestWebSocketChatEndpoint:
    """Test cases for WebSocket chat endpoint."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        websocket.receive_text = AsyncMock()
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
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_websocket_chat_successful_connection(self, mock_websocket, mock_user, mock_bot, mock_db):
        """Test successful WebSocket chat connection."""
        bot_id = str(mock_bot.id)
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=mock_user)
            mock_service.verify_bot_access = AsyncMock(return_value=mock_bot)
            
            with patch('app.services.websocket_service.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock(return_value="connection-id")
                mock_manager.disconnect = Mock()
                
                # Mock WebSocket to raise WebSocketDisconnect after connection
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text.side_effect = WebSocketDisconnect()
                
                # Import and call the endpoint function directly
                from app.api.websocket import websocket_chat_endpoint
                
                await websocket_chat_endpoint(mock_websocket, bot_id, token, mock_db)
                
                # Verify authentication was called
                mock_service.authenticate_websocket.assert_called_once_with(mock_websocket, token)
                
                # Verify bot access was checked
                mock_service.verify_bot_access.assert_called_once_with(mock_user, bot_id)
                
                # Verify connection was established
                mock_manager.connect.assert_called_once_with(
                    websocket=mock_websocket,
                    user_id=str(mock_user.id),
                    bot_id=bot_id
                )
                
                # Verify connection confirmation was sent
                mock_websocket.send_text.assert_called()
                
                # Verify cleanup on disconnect
                mock_manager.disconnect.assert_called_once_with("connection-id")
    
    @pytest.mark.asyncio
    async def test_websocket_chat_authentication_failure(self, mock_websocket, mock_db):
        """Test WebSocket chat connection with authentication failure."""
        bot_id = str(uuid.uuid4())
        token = "invalid-token"
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=None)
            
            from app.api.websocket import websocket_chat_endpoint
            
            await websocket_chat_endpoint(mock_websocket, bot_id, token, mock_db)
            
            # Verify authentication was attempted
            mock_service.authenticate_websocket.assert_called_once_with(mock_websocket, token)
            
            # Verify no further processing occurred
            mock_service.verify_bot_access.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_websocket_chat_bot_access_denied(self, mock_websocket, mock_user, mock_db):
        """Test WebSocket chat connection with bot access denied."""
        bot_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=mock_user)
            mock_service.verify_bot_access = AsyncMock(return_value=None)
            
            from app.api.websocket import websocket_chat_endpoint
            
            await websocket_chat_endpoint(mock_websocket, bot_id, token, mock_db)
            
            # Verify bot access was checked
            mock_service.verify_bot_access.assert_called_once_with(mock_user, bot_id)
            
            # Verify connection was closed
            mock_websocket.close.assert_called_once_with(code=4003, reason="Bot not found or access denied")
    
    @pytest.mark.asyncio
    async def test_websocket_chat_typing_message(self, mock_websocket, mock_user, mock_bot, mock_db):
        """Test handling typing indicator message."""
        bot_id = str(mock_bot.id)
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        # Mock typing message
        typing_message = json.dumps({
            "type": "typing",
            "data": {"is_typing": True}
        })
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=mock_user)
            mock_service.verify_bot_access = AsyncMock(return_value=mock_bot)
            mock_service.handle_typing_indicator = AsyncMock()
            
            with patch('app.services.websocket_service.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock(return_value="connection-id")
                mock_manager.disconnect = Mock()
                
                # Mock WebSocket to return typing message then disconnect
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text = AsyncMock(side_effect=[typing_message, WebSocketDisconnect()])
                
                from app.api.websocket import websocket_chat_endpoint
                
                await websocket_chat_endpoint(mock_websocket, bot_id, token, mock_db)
                
                # Verify typing indicator was handled
                mock_service.handle_typing_indicator.assert_called_once_with(
                    bot_id=bot_id,
                    user_id=str(mock_user.id),
                    username=mock_user.username,
                    is_typing=True
                )
    
    @pytest.mark.asyncio
    async def test_websocket_chat_ping_message(self, mock_websocket, mock_user, mock_bot, mock_db):
        """Test handling ping message."""
        bot_id = str(mock_bot.id)
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        # Mock ping message
        ping_message = json.dumps({
            "type": "ping",
            "timestamp": "2023-01-01T00:00:00Z"
        })
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=mock_user)
            mock_service.verify_bot_access = AsyncMock(return_value=mock_bot)
            
            with patch('app.services.websocket_service.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock(return_value="connection-id")
                mock_manager.disconnect = Mock()
                
                # Mock WebSocket to return ping message then disconnect
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text = AsyncMock(side_effect=[ping_message, WebSocketDisconnect()])
                
                from app.api.websocket import websocket_chat_endpoint
                
                await websocket_chat_endpoint(mock_websocket, bot_id, token, mock_db)
                
                # Verify pong response was sent
                calls = mock_websocket.send_text.call_args_list
                
                # Find the pong response (should be after connection confirmation)
                pong_sent = False
                for call in calls:
                    message = json.loads(call[0][0])
                    if message.get("type") == "pong":
                        assert message["timestamp"] == "2023-01-01T00:00:00Z"
                        pong_sent = True
                        break
                
                assert pong_sent, "Pong response was not sent"
    
    @pytest.mark.asyncio
    async def test_websocket_chat_invalid_json(self, mock_websocket, mock_user, mock_bot, mock_db):
        """Test handling invalid JSON message."""
        bot_id = str(mock_bot.id)
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=mock_user)
            mock_service.verify_bot_access = AsyncMock(return_value=mock_bot)
            
            with patch('app.services.websocket_service.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock(return_value="connection-id")
                mock_manager.disconnect = Mock()
                
                # Mock WebSocket to return invalid JSON then disconnect
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text = AsyncMock(side_effect=["invalid json", WebSocketDisconnect()])
                
                from app.api.websocket import websocket_chat_endpoint
                
                await websocket_chat_endpoint(mock_websocket, bot_id, token, mock_db)
                
                # Verify error response was sent
                calls = mock_websocket.send_text.call_args_list
                
                # Find the error response
                error_sent = False
                for call in calls:
                    try:
                        message = json.loads(call[0][0])
                        if message.get("type") == "error" and "Invalid JSON format" in message.get("message", ""):
                            error_sent = True
                            break
                    except json.JSONDecodeError:
                        continue
                
                assert error_sent, "Error response was not sent for invalid JSON"


class TestWebSocketNotificationsEndpoint:
    """Test cases for WebSocket notifications endpoint."""
    
    @pytest.mark.asyncio
    async def test_websocket_notifications_successful_connection(self, mock_db):
        """Test successful WebSocket notifications connection."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        mock_user = Mock(spec=User)
        mock_user.id = uuid.uuid4()
        mock_user.username = "testuser"
        
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=mock_user)
            
            with patch('app.services.websocket_service.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock(return_value="connection-id")
                mock_manager.disconnect = Mock()
                
                # Mock WebSocket to raise WebSocketDisconnect after connection
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())
                
                from app.api.websocket import websocket_notifications_endpoint
                
                await websocket_notifications_endpoint(mock_websocket, token, mock_db)
                
                # Verify authentication was called
                mock_service.authenticate_websocket.assert_called_once_with(mock_websocket, token)
                
                # Verify connection was established (without bot_id)
                mock_manager.connect.assert_called_once_with(
                    websocket=mock_websocket,
                    user_id=str(mock_user.id)
                )
                
                # Verify connection confirmation was sent
                mock_websocket.send_text.assert_called()
                
                # Verify cleanup on disconnect
                mock_manager.disconnect.assert_called_once_with("connection-id")
    
    @pytest.mark.asyncio
    async def test_websocket_notifications_ping_handling(self, mock_db):
        """Test ping handling in notifications endpoint."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        mock_user = Mock(spec=User)
        mock_user.id = uuid.uuid4()
        mock_user.username = "testuser"
        
        token = create_access_token(data={"sub": str(mock_user.id)})
        
        # Mock ping message
        ping_message = json.dumps({
            "type": "ping",
            "timestamp": "2023-01-01T00:00:00Z"
        })
        
        with patch('app.api.websocket.WebSocketService') as MockWebSocketService:
            mock_service = MockWebSocketService.return_value
            mock_service.authenticate_websocket = AsyncMock(return_value=mock_user)
            
            with patch('app.services.websocket_service.connection_manager') as mock_manager:
                mock_manager.connect = AsyncMock(return_value="connection-id")
                mock_manager.disconnect = Mock()
                
                # Mock WebSocket to return ping message then disconnect
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text = AsyncMock(side_effect=[ping_message, WebSocketDisconnect()])
                
                from app.api.websocket import websocket_notifications_endpoint
                
                await websocket_notifications_endpoint(mock_websocket, token, mock_db)
                
                # Verify pong response was sent
                calls = mock_websocket.send_text.call_args_list
                
                # Find the pong response
                pong_sent = False
                for call in calls:
                    message = json.loads(call[0][0])
                    if message.get("type") == "pong":
                        assert message["timestamp"] == "2023-01-01T00:00:00Z"
                        pong_sent = True
                        break
                
                assert pong_sent, "Pong response was not sent"


if __name__ == "__main__":
    pytest.main([__file__])