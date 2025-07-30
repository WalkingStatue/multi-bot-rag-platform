/**
 * Bot management service for API interactions
 */
import { apiClient } from './api';
import {
  BotCreate,
  BotUpdate,
  BotResponse,
  BotWithRole,
  BotTransferRequest,
  BotAnalytics,
  BotDeleteConfirmation,
  BotProviderSettings,
  CollaboratorInvite,
  CollaboratorInviteResponse,
  BulkPermissionUpdate,
  PermissionHistory,
  ActivityLog,
  BotPermission,
} from '../types/bot';

export class BotService {
  /**
   * Create a new bot
   */
  async createBot(botData: BotCreate): Promise<BotResponse> {
    const response = await apiClient.post('/bots/', botData);
    return response.data;
  }

  /**
   * Get all bots accessible to the current user
   */
  async getUserBots(): Promise<BotWithRole[]> {
    const response = await apiClient.get('/bots/');
    return response.data;
  }

  /**
   * Get a specific bot by ID
   */
  async getBot(botId: string): Promise<BotResponse> {
    const response = await apiClient.get(`/bots/${botId}`);
    return response.data;
  }

  /**
   * Update a bot's configuration
   */
  async updateBot(botId: string, updates: BotUpdate): Promise<BotResponse> {
    const response = await apiClient.put(`/bots/${botId}`, updates);
    return response.data;
  }

  /**
   * Delete a bot (owner only)
   */
  async deleteBot(botId: string): Promise<void> {
    await apiClient.delete(`/bots/${botId}`);
  }

  /**
   * Transfer bot ownership to another user
   */
  async transferOwnership(botId: string, request: BotTransferRequest): Promise<void> {
    await apiClient.post(`/bots/${botId}/transfer`, request);
  }

  /**
   * Get bot analytics and usage statistics
   */
  async getBotAnalytics(botId: string): Promise<BotAnalytics> {
    const response = await apiClient.get(`/bots/${botId}/analytics`);
    return response.data;
  }

  /**
   * Get bot deletion confirmation info (cascade details)
   */
  async getBotDeleteInfo(botId: string): Promise<BotDeleteConfirmation> {
    // This would typically be a separate endpoint, but for now we'll simulate it
    // by getting the bot and analytics data
    const [bot, analytics] = await Promise.all([
      this.getBot(botId),
      this.getBotAnalytics(botId),
    ]);

    return {
      bot_id: botId,
      bot_name: bot.name,
      cascade_info: {
        conversations: analytics.total_conversations,
        messages: analytics.total_messages,
        documents: analytics.total_documents,
        collaborators: analytics.total_collaborators,
      },
    };
  }

  /**
   * Get available provider configurations
   */
  async getProviderSettings(): Promise<BotProviderSettings> {
    // This would typically come from a dedicated endpoint
    // For now, we'll return a static configuration
    return {
      llm_providers: {
        openai: {
          name: 'openai',
          display_name: 'OpenAI',
          models: [
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', max_tokens: 4096 },
            { id: 'gpt-4', name: 'GPT-4', max_tokens: 8192 },
            { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', max_tokens: 128000 },
          ],
          default_model: 'gpt-3.5-turbo',
          supports_embeddings: true,
          embedding_models: [
            { id: 'text-embedding-3-small', name: 'Text Embedding 3 Small' },
            { id: 'text-embedding-3-large', name: 'Text Embedding 3 Large' },
          ],
          default_embedding_model: 'text-embedding-3-small',
        },
        anthropic: {
          name: 'anthropic',
          display_name: 'Anthropic',
          models: [
            { id: 'claude-3-haiku', name: 'Claude 3 Haiku', max_tokens: 4096 },
            { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', max_tokens: 4096 },
            { id: 'claude-3-opus', name: 'Claude 3 Opus', max_tokens: 4096 },
          ],
          default_model: 'claude-3-haiku',
          supports_embeddings: false,
        },
        gemini: {
          name: 'gemini',
          display_name: 'Google Gemini',
          models: [
            { id: 'gemini-pro', name: 'Gemini Pro', max_tokens: 8192 },
            { id: 'gemini-pro-vision', name: 'Gemini Pro Vision', max_tokens: 8192 },
          ],
          default_model: 'gemini-pro',
          supports_embeddings: true,
          embedding_models: [
            { id: 'embedding-001', name: 'Embedding 001' },
          ],
          default_embedding_model: 'embedding-001',
        },
        openrouter: {
          name: 'openrouter',
          display_name: 'OpenRouter',
          models: [
            { id: 'openrouter/auto', name: 'Auto (Best Available)' },
            { id: 'anthropic/claude-3-opus', name: 'Claude 3 Opus' },
            { id: 'openai/gpt-4-turbo', name: 'GPT-4 Turbo' },
          ],
          default_model: 'openrouter/auto',
          supports_embeddings: false,
        },
      },
      embedding_providers: {
        openai: {
          name: 'openai',
          display_name: 'OpenAI',
          models: [
            { id: 'text-embedding-3-small', name: 'Text Embedding 3 Small' },
            { id: 'text-embedding-3-large', name: 'Text Embedding 3 Large' },
          ],
          default_model: 'text-embedding-3-small',
          supports_embeddings: true,
        },
        gemini: {
          name: 'gemini',
          display_name: 'Google Gemini',
          models: [
            { id: 'embedding-001', name: 'Embedding 001' },
          ],
          default_model: 'embedding-001',
          supports_embeddings: true,
        },
        local: {
          name: 'local',
          display_name: 'Local Models',
          models: [
            { id: 'sentence-transformers/all-MiniLM-L6-v2', name: 'All-MiniLM-L6-v2' },
            { id: 'sentence-transformers/all-mpnet-base-v2', name: 'All-MPNet-Base-v2' },
          ],
          default_model: 'sentence-transformers/all-MiniLM-L6-v2',
          supports_embeddings: true,
        },
      },
    };
  }

  // Collaboration methods
  /**
   * Get bot permissions/collaborators
   */
  async getBotPermissions(botId: string): Promise<BotPermission[]> {
    const response = await apiClient.get(`/bots/${botId}/permissions`);
    return response.data;
  }

  /**
   * Invite a collaborator to a bot
   */
  async inviteCollaborator(
    botId: string,
    invite: CollaboratorInvite
  ): Promise<CollaboratorInviteResponse> {
    const response = await apiClient.post(`/bots/${botId}/permissions/invite`, invite);
    return response.data;
  }

  /**
   * Update a collaborator's role
   */
  async updateCollaboratorRole(
    botId: string,
    userId: string,
    role: 'admin' | 'editor' | 'viewer'
  ): Promise<BotPermission> {
    const response = await apiClient.put(`/bots/${botId}/permissions/${userId}`, { role });
    return response.data;
  }

  /**
   * Remove a collaborator from a bot
   */
  async removeCollaborator(botId: string, userId: string): Promise<void> {
    await apiClient.delete(`/bots/${botId}/permissions/${userId}`);
  }

  /**
   * Bulk update permissions
   */
  async bulkUpdatePermissions(
    botId: string,
    updates: BulkPermissionUpdate
  ): Promise<BotPermission[]> {
    const response = await apiClient.post(`/bots/${botId}/permissions/bulk`, updates);
    return response.data;
  }

  /**
   * Get permission history for a bot
   */
  async getPermissionHistory(botId: string): Promise<PermissionHistory[]> {
    const response = await apiClient.get(`/bots/${botId}/permissions/history`);
    return response.data;
  }

  /**
   * Get activity log for a bot
   */
  async getActivityLog(botId: string): Promise<ActivityLog[]> {
    const response = await apiClient.get(`/bots/${botId}/activity`);
    return response.data;
  }

  // Utility methods
  /**
   * Search for users to invite as collaborators
   */
  async searchUsers(query: string): Promise<Array<{ id: string; username: string; email: string }>> {
    const response = await apiClient.get(`/users/search?q=${encodeURIComponent(query)}`);
    return response.data;
  }

  /**
   * Validate bot configuration before saving
   */
  validateBotConfig(config: BotCreate | BotUpdate): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if ('name' in config && config.name) {
      if (config.name.length < 1 || config.name.length > 255) {
        errors.push('Bot name must be between 1 and 255 characters');
      }
    }

    if ('system_prompt' in config && config.system_prompt) {
      if (config.system_prompt.length < 1) {
        errors.push('System prompt is required');
      }
    }

    if ('temperature' in config && config.temperature !== undefined) {
      if (config.temperature < 0 || config.temperature > 2) {
        errors.push('Temperature must be between 0 and 2');
      }
    }

    if ('max_tokens' in config && config.max_tokens !== undefined) {
      if (config.max_tokens < 1 || config.max_tokens > 8000) {
        errors.push('Max tokens must be between 1 and 8000');
      }
    }

    if ('top_p' in config && config.top_p !== undefined) {
      if (config.top_p < 0 || config.top_p > 1) {
        errors.push('Top P must be between 0 and 1');
      }
    }

    if ('frequency_penalty' in config && config.frequency_penalty !== undefined) {
      if (config.frequency_penalty < -2 || config.frequency_penalty > 2) {
        errors.push('Frequency penalty must be between -2 and 2');
      }
    }

    if ('presence_penalty' in config && config.presence_penalty !== undefined) {
      if (config.presence_penalty < -2 || config.presence_penalty > 2) {
        errors.push('Presence penalty must be between -2 and 2');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

// Export singleton instance
export const botService = new BotService();