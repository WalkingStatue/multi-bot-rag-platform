/**
 * WebSocket service specifically for chat functionality
 */
import { ChatMessage, TypingIndicator, ConnectionStatus } from '../types/chat';

export class ChatWebSocketService {
  private socket: WebSocket | null = null;
  private currentBotId: string | null = null;
  private typingTimeout: number | null = null;
  private pingInterval: number | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private token: string | null = null;

  /**
   * Connect to chat WebSocket for a specific bot
   */
  connectToBot(botId: string, token: string): void {
    if (this.socket?.readyState === WebSocket.OPEN && this.currentBotId === botId) {
      return;
    }

    // Disconnect existing connection if any
    this.disconnect();

    this.currentBotId = botId;
    this.token = token;
    
    const wsUrl = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000';
    const chatUrl = `${wsUrl}/api/ws/chat/${botId}?token=${encodeURIComponent(token)}`;
    
    this.socket = new WebSocket(chatUrl);
    this.setupEventHandlers();
  }

  /**
   * Disconnect from current bot chat
   */
  disconnect(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
      this.typingTimeout = null;
    }
    
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    this.listeners.clear();
    this.currentBotId = null;
    this.reconnectAttempts = 0;
    this.token = null;
  }

  /**
   * Subscribe to chat messages
   */
  onChatMessage(callback: (message: ChatMessage) => void): () => void {
    return this.subscribe('chat_message', callback);
  }

  /**
   * Subscribe to typing indicators
   */
  onTypingIndicator(callback: (indicator: TypingIndicator) => void): () => void {
    return this.subscribe('typing_indicator', callback);
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionStatus(callback: (status: ConnectionStatus) => void): () => void {
    return this.subscribe('connection', callback);
  }

  /**
   * Subscribe to specific event types
   */
  private subscribe(eventType: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    
    this.listeners.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      const eventListeners = this.listeners.get(eventType);
      if (eventListeners) {
        eventListeners.delete(callback);
        if (eventListeners.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(isTyping: boolean): void {
    if (!this.currentBotId || !this.isConnected()) return;

    this.send({
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
   * Send a message through WebSocket
   */
  private send(data: any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN || false;
  }

  /**
   * Get current bot ID
   */
  getCurrentBotId(): string | null {
    return this.currentBotId;
  }

  /**
   * Setup event handlers for WebSocket
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log('Chat WebSocket connected for bot:', this.currentBotId);
      this.reconnectAttempts = 0;
      this.notifyListeners('connection', { status: 'connected' });
      this.startPingInterval();
    };

    this.socket.onclose = (event) => {
      console.log('Chat WebSocket disconnected:', event.code, event.reason);
      this.notifyListeners('connection', { 
        status: 'disconnected', 
        code: event.code, 
        reason: event.reason 
      });
      
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
      
      // Don't reconnect if it was a clean close or authentication error
      if (event.code !== 1000 && event.code !== 4001 && event.code !== 4003) {
        this.handleReconnect();
      }
    };

    this.socket.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
      this.notifyListeners('connection', { status: 'error', error: 'Connection error' });
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing chat WebSocket message:', error);
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: any): void {
    const { type, data } = message;

    switch (type) {
      case 'connection_established':
        console.log('Chat WebSocket connection established:', data);
        break;
      
      case 'chat_message':
        this.notifyListeners('chat_message', message);
        break;
      
      case 'typing_indicator':
        this.notifyListeners('typing_indicator', message);
        break;
      
      case 'pong':
        // Handle pong response for ping/pong health check
        break;
      
      case 'error':
        console.error('Chat WebSocket server error:', data);
        break;
      
      default:
        console.log('Unknown chat WebSocket message type:', type, data);
    }
  }

  /**
   * Notify all listeners for a specific event type
   */
  private notifyListeners(eventType: string, data: any): void {
    const eventListeners = this.listeners.get(eventType);
    if (eventListeners) {
      eventListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in chat WebSocket listener for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts || !this.token || !this.currentBotId) {
      console.error('Max reconnection attempts reached or missing connection info');
      this.notifyListeners('connection', { 
        status: 'failed', 
        message: 'Failed to reconnect after maximum attempts' 
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Attempting to reconnect chat WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      if (this.token && this.currentBotId) {
        this.connectToBot(this.currentBotId, this.token);
      }
    }, delay);
  }

  /**
   * Start ping interval for connection health
   */
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({
          type: 'ping',
          timestamp: new Date().toISOString()
        });
      }
    }, 30000); // Ping every 30 seconds
  }
}

// Export singleton instance
export const chatWebSocketService = new ChatWebSocketService();