# WebSocket Real-time Connection Improvements

## Overview
This document outlines the comprehensive improvements made to the WebSocket real-time connection system, specifically addressing issues with connection and reconnection when joining previous sessions.

## Key Issues Addressed

### 1. Session State Management
- **Problem**: WebSocket connections didn't properly sync with session state when switching between sessions
- **Solution**: Added session synchronization with `syncToSession()` method and session sync queue

### 2. Connection Debouncing
- **Problem**: Aggressive debouncing prevented necessary reconnections
- **Solution**: Reduced debounce time from 1000ms to 500ms and improved debounce logic

### 3. Session Message Loading
- **Problem**: Messages weren't properly loaded when switching between sessions
- **Solution**: Created `useChatSession` hook with proper message preloading

### 4. WebSocket Lifecycle Management
- **Problem**: Connection cleanup and re-establishment wasn't coordinated with session changes
- **Solution**: Improved connection state management with proper cleanup and session tracking

### 5. Error Recovery
- **Problem**: Limited error recovery when WebSocket fails during session transitions
- **Solution**: Added comprehensive connection recovery system with diagnostics

## New Components and Utilities

### 1. Enhanced WebSocket Service (`chatWebSocketService.ts`)
- Added session synchronization support
- Improved connection state management
- Better error handling and recovery
- Session sync queue for pending operations

### 2. Session Management Hook (`useChatSession.ts`)
- Centralized session management logic
- Automatic session initialization
- Message preloading
- Error handling and recovery

### 3. Connection Recovery Manager (`connectionRecovery.ts`)
- Exponential backoff retry logic
- Network health checking
- Comprehensive diagnostics integration
- Cancellable recovery operations

### 4. WebSocket Diagnostics (`websocketDiagnostics.ts`)
- Backend connectivity testing
- WebSocket URL validation
- Authentication token verification
- Bot access validation
- Connection attempt testing

### 5. Connection Health Monitor (`connectionHealth.ts`)
- Network connectivity monitoring
- Health status tracking
- Automatic health checks
- Event-based notifications

## Backend Improvements

### 1. Session Synchronization Support
- Added `session_sync` message type handling
- Proper session state tracking
- Session sync confirmation responses

### 2. Enhanced Error Handling
- Better error messages and codes
- Improved connection state management
- Proper cleanup on disconnection

## Key Features

### 1. Session Synchronization
```typescript
// Sync WebSocket to specific session
chatWebSocketService.syncToSession(sessionId);

// Queue sync operations for when connection is established
this.sessionSyncQueue.push({
  sessionId,
  callback: () => this.send({ type: 'session_sync', data: { session_id: sessionId } })
});
```

### 2. Connection Recovery
```typescript
// Quick recovery for common cases
const success = await quickRecover(botId, sessionId);

// Full recovery with diagnostics
const result = await fullRecover(botId, sessionId);
```

### 3. Comprehensive Diagnostics
```typescript
// Run full diagnostics
const diagnostics = await runWebSocketDiagnostics(botId, token);

// Format report for debugging
const report = formatDiagnosticsReport(diagnostics);
```

### 4. Improved Session Management
```typescript
// Use the session management hook
const {
  sessions,
  currentSession,
  isLoading,
  error,
  selectSession,
  createSession,
  refreshSessions
} = useChatSession({
  botId: bot.id,
  autoSelectFirst: true,
  preloadMessages: true
});
```

## Connection Flow Improvements

### 1. Initial Connection
1. Check if already connected to the same bot
2. Perform backend health check
3. Create WebSocket connection with timeout
4. Process queued session sync operations
5. Start ping interval for health monitoring

### 2. Session Switching
1. Update current session ID
2. Sync WebSocket to new session
3. Load session messages if preloading enabled
4. Update UI state

### 3. Reconnection Logic
1. Check network health before attempting
2. Use exponential backoff with jitter
3. Preserve session state during reconnection
4. Run diagnostics on repeated failures
5. Provide manual recovery options

### 4. Error Recovery
1. Detect connection failures
2. Attempt automatic recovery with backoff
3. Run diagnostics if recovery fails
4. Provide user-initiated recovery options
5. Maintain session context throughout

## Configuration Options

### WebSocket Service Configuration
- `connectionDebounceMs`: 500ms (reduced from 1000ms)
- `maxReconnectAttempts`: 5
- `reconnectDelay`: 1000ms base delay
- `connectionTimeout`: 10 seconds

### Recovery Manager Configuration
- `maxAttempts`: 5 (default)
- `baseDelay`: 1000ms (default)
- `maxDelay`: 30000ms
- `backoffMultiplier`: 2
- `runDiagnostics`: true (for full recovery)

### Health Monitor Configuration
- `CHECK_INTERVAL`: 30 seconds
- `MAX_FAILURES`: 3 consecutive failures
- Network online/offline event handling

## Usage Examples

### Basic Session Management
```typescript
// In a React component
const { selectSession, createSession } = useChatSession({
  botId: bot.id,
  autoSelectFirst: true,
  preloadMessages: true
});

// Switch to a session
await selectSession(sessionId);

// Create new session
const newSession = await createSession();
```

### Manual Connection Recovery
```typescript
// Quick recovery attempt
const success = await quickRecover(botId, sessionId);
if (!success) {
  console.log('Quick recovery failed');
}

// Full recovery with diagnostics
const result = await fullRecover(botId, sessionId);
if (result.success) {
  console.log('Recovery successful');
} else {
  console.log('Recovery failed:', result.error);
  console.log('Diagnostics:', result.diagnostics);
}
```

### Connection Status Monitoring
```typescript
// Subscribe to connection status changes
const unsubscribe = chatWebSocketService.onConnectionStatus((status) => {
  console.log('Connection status:', status);
});

// Check current connection status
const isConnected = chatWebSocketService.isConnected();
const currentBot = chatWebSocketService.getCurrentBotId();
const currentSession = chatWebSocketService.getCurrentSessionId();
```

## Testing and Debugging

### Diagnostic Tools
- Backend connectivity testing
- WebSocket URL validation
- Authentication verification
- Bot access checking
- Connection attempt testing

### Debug Information
- Connection state logging
- Session sync operation tracking
- Recovery attempt monitoring
- Health check status
- Error categorization

### Manual Recovery Options
- Retry connection button in UI
- Diagnostic report generation
- Connection status indicators
- Recovery progress feedback

## Benefits

1. **Improved Reliability**: Better handling of network issues and connection failures
2. **Session Continuity**: Proper session state management during reconnections
3. **User Experience**: Seamless session switching with preloaded messages
4. **Debugging**: Comprehensive diagnostics for troubleshooting
5. **Recovery**: Automatic and manual recovery options
6. **Performance**: Optimized connection management with proper debouncing
7. **Monitoring**: Real-time connection health monitoring

## Migration Notes

### For Existing Components
- Update `ChatWindow` to use `useChatSession` hook
- Update `SessionList` to accept sessions and selection handler as props
- Update connection status handling to use new recovery options

### For New Development
- Use `useChatSession` hook for session management
- Implement connection recovery for critical operations
- Add diagnostic capabilities for troubleshooting
- Monitor connection health for better UX

This comprehensive improvement addresses all the major issues with WebSocket real-time connections and provides a robust foundation for reliable chat functionality.