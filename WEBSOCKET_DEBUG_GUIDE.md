# WebSocket Connection Debugging Guide

## Current Issue Analysis

Based on the console logs you're seeing:
1. WebSocket connects successfully (`Chat WebSocket connected for bot`)
2. Connection established message is received
3. Immediately after, a WebSocket error occurs
4. Connection closes with code 1006 (abnormal closure)
5. Reconnection attempts begin

This pattern suggests the server is accepting the connection but then immediately terminating it, possibly due to:
- Authentication/authorization issues
- Server-side error during connection handling
- Protocol mismatch or invalid message format
- Server resource constraints

## New Debugging Tools Added

### 1. Enhanced Logging
- More detailed connection state logging
- Connection timeout detection (10 seconds)
- Backend health check before WebSocket connection
- Clearer error messages with context

### 2. Diagnostic Tools

#### Browser Console Functions
```javascript
// Test WebSocket connection manually
testWebSocket('your-bot-id', 'your-token')

// Run comprehensive diagnostics
runWebSocketDiagnostics('your-bot-id', 'your-token')
```

#### Connection Status UI
- Visual connection status indicator
- Retry button for manual reconnection
- Diagnose button to run diagnostics

### 3. Connection Health Monitoring
- Network connectivity checks
- Backend availability verification
- Prevents reconnection when network is unhealthy

## Debugging Steps

### Step 1: Check Browser Console
Look for these specific log messages:
```
Attempting to connect to chat WebSocket: ws://localhost:8000/api/ws/chat/[BOT_ID]?token=[TOKEN]
Chat WebSocket connected for bot: [BOT_ID]
Chat WebSocket connection established: {...}
Chat WebSocket error: [Error Object]
Chat WebSocket disconnected: 1006 - [Reason]
```

### Step 2: Run Manual Test
Open browser console and run:
```javascript
testWebSocket('c8c0470a-bbb4-4a75-952b-102203d866de', localStorage.getItem('access_token'))
```

### Step 3: Check Network Tab
1. Open DevTools → Network tab
2. Filter by "WS" (WebSocket)
3. Look for the WebSocket connection
4. Check if it shows any specific error codes or messages

### Step 4: Verify Backend
Check if the backend WebSocket endpoint is properly configured:
- Is the WebSocket server running?
- Are there any server-side errors in backend logs?
- Is the authentication middleware working correctly?

### Step 5: Test Different Scenarios
```javascript
// Test with different bot IDs
testWebSocket('different-bot-id', localStorage.getItem('access_token'))

// Test with fresh token
// (Login again and test immediately)

// Test backend health
fetch('http://localhost:8000/api/health').then(r => console.log('Health:', r.status))
```

## Common Solutions

### 1. Token Issues
If authentication is failing:
```javascript
// Check token validity
console.log('Token:', localStorage.getItem('access_token'))

// Try refreshing token
// Logout and login again
```

### 2. Backend Configuration
Verify backend WebSocket configuration:
- CORS settings for WebSocket
- Authentication middleware
- Bot permission checks

### 3. Network/Proxy Issues
If behind corporate firewall or proxy:
- Check if WebSocket connections are allowed
- Try different network (mobile hotspot)
- Check browser WebSocket support

### 4. Server Resource Issues
If server is overloaded:
- Check server logs for errors
- Monitor server resources (CPU, memory)
- Restart backend services

## Environment Variables

Make sure these are set correctly:
```env
VITE_WS_URL=ws://localhost:8000
VITE_API_URL=http://localhost:8000
```

## Advanced Debugging

### Enable Verbose Logging
Add to your browser console:
```javascript
// Enable all WebSocket logging
localStorage.setItem('debug', 'websocket:*')
```

### Monitor Connection State
```javascript
// Watch connection state changes
setInterval(() => {
  const ws = chatWebSocketService.getCurrentBotId();
  console.log('Current bot:', ws, 'Connected:', chatWebSocketService.isConnected());
}, 5000);
```

### Check Server Response
If you have access to backend logs, look for:
- WebSocket connection attempts
- Authentication failures
- Server errors during connection handling
- Resource exhaustion warnings

## Next Steps

1. **Run the diagnostic tools** to get detailed connection information
2. **Check backend logs** for server-side errors
3. **Test with different browsers** to rule out browser-specific issues
4. **Verify network connectivity** and firewall settings
5. **Check server resources** and restart if necessary

The enhanced error handling and diagnostic tools should provide much more insight into what's causing the immediate disconnection after successful connection.