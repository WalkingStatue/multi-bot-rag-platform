/**
 * WebSocket service specifically for chat functionality
 */
import { websocketService } from './websocketService';
import { ChatMessage, TypingIndicator, ConnectionStatus } from '../types/chat';

export class ChatWebSocketService {
  private currentBotId: string | null = null;
  private typingTimeout: number | null = null;
  private pingInterval: number | null = null;

  /**
   * Connect to chat WebSocket for a specific bot
   */
  connectToBot(botId: string, token: string): void {
    this.currentBotId = botId;
    
    // Use the existing websocket service but enhance it for chat
    websocketService.connect(token);
    websocketService.joinBotRoom(botId);
    
    // Start ping interval for connection health
    this.startPingInterval();
  }

  /**
   * Disconnect from current bot chat
   */
  disconnect(): void {
    if (this.currentBotId) {
      websocketService.leaveBotRoom(this.currentBotId);
      this.currentBotId = null;
    }
    
    this.stopPingInterval();
    websocketService.disconnect();
  }

  /**
   * Subscribe to chat messages
   */
  onChatMessage(callback: (message: ChatMessage) => void): () => void {
    return websocketService.subscribe('chat_message', callback);
  }

  /**
   * Subscribe to typing indicators
   */
  onTypingIndicator(callback: (indicator: TypingIndicator) => void): () => void {
    return websocketService.subscribe('typing_indicator', callback);
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionStatus(callback: (status: ConnectionStatus) => void): () => void {
    return websocketService.subscribe('connection', callback);
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(isTyping: boolean): void {
    if (!this.currentBotId) return;

    websocketService.emit('typing', {
      type: 'typing',
      data: { is_typing: isTyping }
    });

    // Auto-stop typing after 3 seconds
    if (isTyping) {
      if (this.typingTimeout) {
        clearTimeout(this.typingTimeout);
      }
      
      this.typingTimeout = setTimeout(() => {
        this.sendTypingIndicator(false);
      }, 3000);
    } else if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
      this.typingTimeout = null;
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return websocketService.isConnected();
  }

  /**
   * Get current bot ID
   */
  getCurrentBotId(): string | null {
    return this.currentBotId;
  }

  /**
   * Start ping interval for connection health
   */
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (websocketService.isConnected()) {
        websocketService.emit('ping', {
          type: 'ping',
          timestamp: new Date().toISOString()
        });
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

// Export singleton instance
export const chatWebSocketService = new ChatWebSocketService();