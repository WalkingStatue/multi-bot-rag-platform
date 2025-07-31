/**
 * WebSocket service for real-time updates
 */
import { io, Socket } from 'socket.io-client';
import { Notification } from '../types/notifications';

export class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  /**
   * Connect to WebSocket server
   */
  connect(token: string): void {
    if (this.socket?.connected) {
      return;
    }

    const wsUrl = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000';
    
    this.socket = io(wsUrl, {
      auth: {
        token: token,
      },
      transports: ['websocket'],
      upgrade: false,
    });

    this.setupEventHandlers();
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
    this.reconnectAttempts = 0;
  }

  /**
   * Subscribe to specific event types
   */
  subscribe(eventType: string, callback: (data: any) => void): () => void {
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
   * Join a bot room for real-time updates
   */
  joinBotRoom(botId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('join_bot_room', { bot_id: botId });
    }
  }

  /**
   * Leave a bot room
   */
  leaveBotRoom(botId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('leave_bot_room', { bot_id: botId });
    }
  }

  /**
   * Send a message through WebSocket
   */
  emit(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * Setup event handlers for WebSocket
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.notifyListeners('connection', { status: 'connected' });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.notifyListeners('connection', { status: 'disconnected', reason });
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect
        return;
      }
      
      this.handleReconnect();
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.notifyListeners('connection', { status: 'error', error: error.message });
      this.handleReconnect();
    });

    // Handle notification messages
    this.socket.on('notification', (data: Notification) => {
      this.notifyListeners('notification', data);
    });

    // Handle permission updates
    this.socket.on('permission_update', (data: any) => {
      this.notifyListeners('permission_update', data);
    });

    // Handle bot updates
    this.socket.on('bot_update', (data: any) => {
      this.notifyListeners('bot_update', data);
    });

    // Handle collaboration updates
    this.socket.on('collaboration_update', (data: any) => {
      this.notifyListeners('collaboration_update', data);
    });

    // Handle activity log updates
    this.socket.on('activity_update', (data: any) => {
      this.notifyListeners('activity_update', data);
    });
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.notifyListeners('connection', { 
        status: 'failed', 
        message: 'Failed to reconnect after maximum attempts' 
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.socket?.connect();
    }, delay);
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
          console.error(`Error in WebSocket listener for ${eventType}:`, error);
        }
      });
    }
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();