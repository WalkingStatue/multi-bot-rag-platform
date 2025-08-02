/**
 * Simple WebSocket test that can be run in browser console
 * Copy and paste this into your browser console to test WebSocket connection
 */

function testWebSocketSimple() {
  const botId = 'c8c0470a-bbb4-4a75-952b-102203d866de';
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    console.error('No access token found. Please login first.');
    return;
  }
  
  const wsUrl = 'ws://localhost:8000';
  const chatUrl = `${wsUrl}/api/ws/chat/${botId}?token=${encodeURIComponent(token)}`;
  
  console.log('🔌 Connecting to:', chatUrl.replace(token, '[TOKEN_HIDDEN]'));
  
  const socket = new WebSocket(chatUrl);
  
  socket.onopen = (event) => {
    console.log('✅ WebSocket opened:', event);
    console.log('📊 ReadyState:', socket.readyState);
    
    // Don't send anything immediately, just wait for server messages
    console.log('⏳ Waiting for server messages...');
  };
  
  socket.onmessage = (event) => {
    console.log('📨 Message received:', event.data);
    try {
      const message = JSON.parse(event.data);
      console.log('📋 Parsed message:', message);
      
      if (message.type === 'connection_established') {
        console.log('🎉 Connection established successfully!');
        
        // Now try sending a ping after connection is established
        setTimeout(() => {
          console.log('📤 Sending ping...');
          socket.send(JSON.stringify({
            type: 'ping',
            timestamp: new Date().toISOString()
          }));
        }, 2000);
      }
      
      if (message.type === 'pong') {
        console.log('🏓 Pong received!');
        
        // Close connection after successful ping/pong
        setTimeout(() => {
          console.log('👋 Closing connection...');
          socket.close();
        }, 1000);
      }
      
    } catch (error) {
      console.error('❌ Error parsing message:', error);
    }
  };
  
  socket.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
    console.log('📊 ReadyState at error:', socket.readyState);
  };
  
  socket.onclose = (event) => {
    console.log('🔌 WebSocket closed:', event.code, event.reason);
    console.log('📊 Was clean:', event.wasClean);
    
    // Interpret close codes
    switch (event.code) {
      case 1000:
        console.log('✅ Normal closure');
        break;
      case 1006:
        console.log('⚠️ Abnormal closure (no close frame)');
        break;
      case 4001:
        console.log('🔐 Authentication error');
        break;
      case 4003:
        console.log('🚫 Access denied');
        break;
      default:
        console.log('❓ Unknown close code');
    }
  };
  
  // Return socket for manual testing
  window.testSocket = socket;
  console.log('💡 Socket stored in window.testSocket for manual testing');
  
  return socket;
}

// Make function available globally
window.testWebSocketSimple = testWebSocketSimple;

console.log('🧪 WebSocket test function loaded. Run: testWebSocketSimple()');