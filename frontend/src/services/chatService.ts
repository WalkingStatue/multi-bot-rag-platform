/**
 * Chat service for handling chat operations with backend API
 */
import { apiClient } from './api';
import {
  ConversationSession,
  ConversationSessionCreate,
  Message,
  MessageCreate,
  ChatRequest,
  ChatResponse,
  ConversationSearchResult,
  ConversationAnalytics,
  ConversationExport
} from '../types/chat';

export class ChatService {
  /**
   * Create a new conversation session
   */
  async createSession(sessionData: ConversationSessionCreate): Promise<ConversationSession> {
    const response = await apiClient.post('/conversations/sessions', sessionData);
    return response.data;
  }

  /**
   * Create a session for a specific bot
   */
  async createBotSession(botId: string, title?: string): Promise<ConversationSession> {
    const response = await apiClient.post(`/conversations/bots/${botId}/sessions`, {
      title: title || 'New Conversation'
    });
    return response.data;
  }

  /**
   * Get list of conversation sessions
   */
  async getSessions(
    botId?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<ConversationSession[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    if (botId) {
      params.append('bot_id', botId);
    }

    const response = await apiClient.get(`/conversations/sessions?${params}`);
    return response.data;
  }

  /**
   * Get a specific conversation session
   */
  async getSession(sessionId: string): Promise<ConversationSession> {
    const response = await apiClient.get(`/conversations/sessions/${sessionId}`);
    return response.data;
  }

  /**
   * Update a conversation session
   */
  async updateSession(
    sessionId: string,
    title?: string,
    isShared?: boolean
  ): Promise<ConversationSession> {
    const updateData: any = {};
    if (title !== undefined) updateData.title = title;
    if (isShared !== undefined) updateData.is_shared = isShared;

    const response = await apiClient.put(`/conversations/sessions/${sessionId}`, updateData);
    return response.data;
  }

  /**
   * Delete a conversation session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/conversations/sessions/${sessionId}`);
  } 
 /**
   * Send a chat message to a bot
   */
  async sendMessage(botId: string, chatRequest: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post(`/conversations/bots/${botId}/chat`, chatRequest);
    return response.data;
  }

  /**
   * Add a message to a session
   */
  async addMessage(messageData: MessageCreate): Promise<Message> {
    const response = await apiClient.post('/conversations/messages', messageData);
    return response.data;
  }

  /**
   * Get messages from a session
   */
  async getSessionMessages(
    sessionId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<Message[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });

    const response = await apiClient.get(`/conversations/sessions/${sessionId}/messages?${params}`);
    return response.data;
  }

  /**
   * Search conversations
   */
  async searchConversations(
    query: string,
    botId?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{ query: string; results: ConversationSearchResult[]; total: number }> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
      offset: offset.toString()
    });

    if (botId) {
      params.append('bot_id', botId);
    }

    const response = await apiClient.get(`/conversations/search?${params}`);
    return response.data;
  }

  /**
   * Export conversations
   */
  async exportConversations(
    botId?: string,
    sessionId?: string,
    format: string = 'json'
  ): Promise<ConversationExport> {
    const params = new URLSearchParams({
      format_type: format
    });

    if (botId) params.append('bot_id', botId);
    if (sessionId) params.append('session_id', sessionId);

    const response = await apiClient.get(`/conversations/export?${params}`);
    return response.data;
  }

  /**
   * Get conversation analytics
   */
  async getAnalytics(botId?: string): Promise<ConversationAnalytics> {
    const params = botId ? `?bot_id=${botId}` : '';
    const response = await apiClient.get(`/conversations/analytics${params}`);
    return response.data;
  }
}

// Export singleton instance
export const chatService = new ChatService();