/**
 * WebSocket service specifically for chat functionality
 */
import { ChatMessage, TypingIndicator, ConnectionStatus } from '../types/chat';
import { connectionHealthMonitor } from '../utils/connectionHealth';

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
  private connectionTimeout: number | null = null;
  private lastConnectionAttempt = 0;
  private connectionDebounceMs = 1000; // Prevent connections within 1 second

  /**
   * Connect to chat WebSocket for a specific bot
   */
  async connectToBot(botId: string, token: string): Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
      // Debounce connection attempts
      const now = Date.now();
      if (now - this.lastConnectionAttempt < this.connectionDebounceMs) {
        console.log('Connection attempt debounced, too soon since last attempt');
        resolve();
        return;
      }
      this.lastConnectionAttempt = now;

      // If already connected to the same bot, don't reconnect
      if (this.socket?.readyState === WebSocket.OPEN && this.currentBotId === botId) {
        console.log('Already connected to bot:', botId);
        resolve();
        return;
      }

      // If connecting to the same bot but connection is not open, wait a bit
      if (this.currentBotId === botId && this.socket?.readyState === WebSocket.CONNECTING) {
        console.log('Connection already in progress for bot:', botId);
        resolve();
        return;
      }

    // Disconnect existing connection if any
    this.disconnect();

    this.currentBotId = botId;
    this.token = token;
    
    const wsUrl = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000';
    const chatUrl = `${wsUrl}/api/ws/chat/${botId}?token=${encodeURIComponent(token)}`;
    
    console.log('Attempting to connect to chat WebSocket:', chatUrl.replace(token, '[TOKEN]'));
    
      // Check if backend is reachable before attempting WebSocket connection
      const checkHealth = async () => {
        try {
          const apiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
          const healthResponse = await fetch(`${apiUrl}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000)
          });
          
          if (!healthResponse.ok) {
            throw new Error(`Backend not available: ${healthResponse.status}`);
          }
        } catch (error) {
          console.log('Backend health check failed, attempting WebSocket connection anyway:', error);
        }
      };
      
      await checkHealth();
      
      try {
        this.socket = new WebSocket(chatUrl);
        this.setupEventHandlers(resolve, reject);
        
        // Set connection timeout
        this.connectionTimeout = setTimeout(() => {
          if (this.socket && this.socket.readyState === WebSocket.CONNECTING) {
            console.log('WebSocket connection timeout, closing...');
            this.socket.close();
            this.notifyListeners('connection', { status: 'error', error: 'Connection timeout' });
            reject(new Error('Connection timeout'));
          }
        }, 10000); // 10 second timeout
        
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        this.notifyListeners('connection', { status: 'error', error: 'Failed to create connection' });
        reject(error);
      }
    });
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
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
    
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    this.listeners.clear();
    this.currentBotId = null;
    this.reconnectAttempts = 0;
    this.token = null;
    this.lastConnectionAttempt = 0; // Reset debounce
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
      console.log('Sending WebSocket message:', JSON.stringify(data));
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('Cannot send WebSocket message - connection not open:', this.socket?.readyState);
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
  private setupEventHandlers(resolve?: () => void, reject?: (error: Error) => void): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log('Chat WebSocket connected for bot:', this.currentBotId);
      
      // Clear connection timeout
      if (this.connectionTimeout) {
        clearTimeout(this.connectionTimeout);
        this.connectionTimeout = null;
      }
      
      this.reconnectAttempts = 0;
      this.notifyListeners('connection', { status: 'connected' });
      // Start ping with delay to let connection stabilize
      this.startPingInterval();
      
      // Resolve the connection promise
      if (resolve) {
        resolve();
      }
    };

    this.socket.onclose = (event) => {
      console.log(`Chat WebSocket disconnected: ${event.code} - ${event.reason || 'No reason provided'}`);
      this.notifyListeners('connection', { 
        status: 'disconnected', 
        code: event.code, 
        reason: event.reason 
      });
      
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
      
      // Handle different close codes appropriately
      if (event.code === 1000) {
        // Normal closure - don't reconnect
        console.log('WebSocket closed normally');
      } else if (event.code === 4001 || event.code === 4003) {
        // Authentication errors - don't reconnect
        console.log('WebSocket closed due to authentication error');
        this.notifyListeners('connection', { 
          status: 'error', 
          error: 'Authentication failed' 
        });
      } else if (event.code === 1006) {
        // Abnormal closure - could be network or server issue
        console.log('WebSocket closed abnormally, will attempt reconnection');
        setTimeout(() => {
          if (this.token && this.currentBotId && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.handleReconnect();
          }
        }, 2000); // Wait 2 seconds before reconnecting
      } else {
        // Other errors - attempt reconnection
        console.log('WebSocket closed with error code, will attempt reconnection');
        this.handleReconnect();
      }
    };

    this.socket.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
      console.log('WebSocket readyState at error:', this.socket?.readyState);
      this.notifyListeners('connection', { status: 'error', error: 'Connection error' });
      
      // Reject the connection promise
      if (reject) {
        reject(new Error('WebSocket connection error'));
      }
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing chat WebSocket message:', error, 'Raw data:', event.data);
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: any): void {
    console.log('WebSocket message received:', JSON.stringify(message));
    console.log('Parsed WebSocket message:', message);
    
    const { type, data } = message;

    switch (type) {
      case 'connection_established':
        console.log('Chat WebSocket connection established:', data);
        break;
      
      case 'chat_message':
        this.notifyListeners('chat_message', message);
        break;
      
      case 'chat_response':
        // Handle bot responses - treat them as chat messages
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

    // Check network health before attempting reconnection
    if (!connectionHealthMonitor.isHealthy()) {
      console.log('Network appears unhealthy, delaying reconnection');
      setTimeout(() => this.handleReconnect(), 10000);
      return;
    }

    this.reconnectAttempts++;
    // Increase delay more aggressively to avoid rate limiting
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`Attempting to reconnect chat WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(async () => {
      if (this.token && this.currentBotId && connectionHealthMonitor.isHealthy()) {
        await this.connectToBot(this.currentBotId, this.token);
      }
    }, delay);
  }

  /**
   * Start ping interval for connection health
   */
  private startPingInterval(): void {
    // Wait a bit before starting ping to let connection stabilize
    setTimeout(() => {
      this.pingInterval = setInterval(() => {
        if (this.isConnected()) {
          this.send({
            type: 'ping',
            timestamp: new Date().toISOString()
          });
        }
      }, 30000); // Ping every 30 seconds
    }, 5000); // Wait 5 seconds before starting ping
  }
}

// Export singleton instance
export const chatWebSocketService = new ChatWebSocketService();