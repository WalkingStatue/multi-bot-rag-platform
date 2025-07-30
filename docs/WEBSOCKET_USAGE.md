# WebSocket System Usage Guide

## Overview

The Multi-Bot RAG Platform includes a comprehensive real-time WebSocket system that enables:

- Real-time chat message updates for bot collaborators
- Live typing indicators during conversations
- Instant notifications for permission changes
- Real-time bot configuration updates
- Document upload/processing notifications

## WebSocket Endpoints

### 1. Chat WebSocket (`/api/ws/chat/{bot_id}`)

Connect to receive real-time updates for a specific bot's conversations.

**Connection URL:**
```
ws://localhost:8000/api/ws/chat/{bot_id}?token={jwt_token}
```

**Authentication:**
- Requires valid JWT token as query parameter
- User must have at least "viewer" permission for the bot

**Supported Message Types:**

#### Client → Server Messages

**Typing Indicator:**
```json
{
  "type": "typing",
  "data": {
    "is_typing": true
  }
}
```

**Ping (Health Check):**
```json
{
  "type": "ping",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Server → Client Messages

**Connection Established:**
```json
{
  "type": "connection_established",
  "data": {
    "bot_id": "uuid",
    "bot_name": "Bot Name",
    "user_id": "uuid",
    "connection_id": "uuid"
  }
}
```

**Chat Message:**
```json
{
  "type": "chat_message",
  "bot_id": "uuid",
  "data": {
    "message_id": "uuid",
    "session_id": "uuid",
    "user_id": "uuid",
    "username": "user123",
    "content": "Hello world!",
    "role": "user",
    "timestamp": "2023-01-01T00:00:00Z",
    "metadata": {}
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Typing Indicator:**
```json
{
  "type": "typing_indicator",
  "bot_id": "uuid",
  "data": {
    "user_id": "uuid",
    "username": "user123",
    "is_typing": true
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Permission Change:**
```json
{
  "type": "permission_change",
  "bot_id": "uuid",
  "data": {
    "target_user_id": "uuid",
    "action": "granted",
    "details": {
      "role": "editor",
      "granted_by": "uuid"
    }
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Bot Update:**
```json
{
  "type": "bot_update",
  "bot_id": "uuid",
  "data": {
    "update_type": "config",
    "details": {
      "name": "New Bot Name"
    },
    "updated_by": "uuid"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Document Update:**
```json
{
  "type": "document_update",
  "bot_id": "uuid",
  "data": {
    "action": "uploaded",
    "document": {
      "id": "uuid",
      "filename": "document.pdf"
    },
    "user_id": "uuid"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Pong Response:**
```json
{
  "type": "pong",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Error:**
```json
{
  "type": "error",
  "message": "Error description"
}
```

### 2. Notifications WebSocket (`/api/ws/notifications`)

Connect to receive general user notifications.

**Connection URL:**
```
ws://localhost:8000/api/ws/notifications?token={jwt_token}
```

**Authentication:**
- Requires valid JWT token as query parameter

**Supported Message Types:**

#### Client → Server Messages

**Ping (Health Check):**
```json
{
  "type": "ping",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Server → Client Messages

**Connection Established:**
```json
{
  "type": "connection_established",
  "data": {
    "user_id": "uuid",
    "connection_id": "uuid",
    "connection_type": "notifications"
  }
}
```

**Notification:**
```json
{
  "type": "notification",
  "notification_type": "permission_change",
  "data": {
    "bot_id": "uuid",
    "action": "granted",
    "details": {
      "role": "editor"
    }
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## JavaScript Client Example

```javascript
class ChatWebSocket {
  constructor(botId, token) {
    this.botId = botId;
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const wsUrl = `ws://localhost:8000/api/ws/chat/${this.botId}?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.stopHeartbeat();
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'connection_established':
        console.log('Connected to bot:', message.data.bot_name);
        break;
      
      case 'chat_message':
        this.onChatMessage(message.data);
        break;
      
      case 'typing_indicator':
        this.onTypingIndicator(message.data);
        break;
      
      case 'permission_change':
        this.onPermissionChange(message.data);
        break;
      
      case 'bot_update':
        this.onBotUpdate(message.data);
        break;
      
      case 'document_update':
        this.onDocumentUpdate(message.data);
        break;
      
      case 'pong':
        // Heartbeat response received
        break;
      
      case 'error':
        console.error('WebSocket error:', message.message);
        break;
    }
  }

  sendTypingIndicator(isTyping) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'typing',
        data: { is_typing: isTyping }
      }));
    }
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'ping',
          timestamp: new Date().toISOString()
        }));
      }
    }, 30000); // Send ping every 30 seconds
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, delay);
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Event handlers (implement these in your application)
  onChatMessage(data) {
    console.log('New chat message:', data);
  }

  onTypingIndicator(data) {
    console.log('Typing indicator:', data);
  }

  onPermissionChange(data) {
    console.log('Permission changed:', data);
  }

  onBotUpdate(data) {
    console.log('Bot updated:', data);
  }

  onDocumentUpdate(data) {
    console.log('Document updated:', data);
  }
}

// Usage
const chatWS = new ChatWebSocket('bot-uuid', 'jwt-token');
chatWS.connect();

// Send typing indicator when user starts typing
chatWS.sendTypingIndicator(true);

// Stop typing indicator when user stops typing
chatWS.sendTypingIndicator(false);

// Disconnect when done
chatWS.disconnect();
```

## Error Codes

WebSocket connections may be closed with the following error codes:

- `4001`: Authentication required or failed
- `4003`: Bot not found or access denied
- `1000`: Normal closure
- `1001`: Going away
- `1002`: Protocol error
- `1003`: Unsupported data
- `1006`: Abnormal closure

## Security Considerations

1. **Authentication**: All WebSocket connections require valid JWT tokens
2. **Authorization**: Users can only connect to bots they have permission to access
3. **Permission Validation**: Real-time permission checking for bot collaborators
4. **Connection Limits**: Consider implementing rate limiting for connections
5. **Message Validation**: All incoming messages are validated for proper format

## Monitoring and Statistics

### WebSocket Statistics Endpoint

**GET** `/api/ws/stats`

Returns connection statistics:
```json
{
  "total_connections": 15,
  "connected_users": 8,
  "bot_subscriptions": 5
}
```

### WebSocket Connections Endpoint (Debug)

**GET** `/api/ws/connections`

Returns detailed connection information:
```json
{
  "connected_users": ["user1", "user2"],
  "bot_subscriptions": {
    "bot1": ["user1", "user2"],
    "bot2": ["user1"]
  },
  "connection_metadata": {
    "conn1": {
      "user_id": "user1",
      "bot_id": "bot1",
      "connected_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

## Integration with Other Services

The WebSocket system is automatically integrated with:

1. **Chat Service**: Sends real-time message updates
2. **Permission Service**: Sends permission change notifications
3. **Bot Service**: Sends bot configuration updates
4. **Document Service**: Sends document processing updates

No additional configuration is required - the WebSocket notifications are sent automatically when these events occur.