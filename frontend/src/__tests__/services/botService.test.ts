/**
 * Unit tests for BotService
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { botService } from '../../services/botService';
import { apiClient } from '../../services/api';
import { BotCreate, BotUpdate, BotResponse, BotWithRole, BotTransferRequest } from '../../types/bot';

// Mock the API client
vi.mock('../../services/api');

const mockApiClient = vi.mocked(apiClient);

describe('BotService', () => {
  beforeEach(() => {
    // Clear localStorage mock
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('createBot', () => {
    it('should create bot successfully', async () => {
      const botData: BotCreate = {
        name: 'Test Bot',
        description: 'A test bot',
        system_prompt: 'You are a helpful assistant',
        llm_provider: 'openai',
        llm_model: 'gpt-3.5-turbo',
        embedding_provider: 'openai',
        embedding_model: 'text-embedding-3-small',
        temperature: 0.7,
        max_tokens: 1000,
        is_public: false,
        allow_collaboration: true,
      };

      const mockResponse: BotResponse = {
        id: '123',
        name: 'Test Bot',
        description: 'A test bot',
        system_prompt: 'You are a helpful assistant',
        owner_id: 'user123',
        llm_provider: 'openai',
        llm_model: 'gpt-3.5-turbo',
        embedding_provider: 'openai',
        embedding_model: 'text-embedding-3-small',
        temperature: 0.7,
        max_tokens: 1000,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
        is_public: false,
        allow_collaboration: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      mockApiClient.post.mockResolvedValueOnce({
        data: mockResponse,
        status: 201,
        statusText: 'Created',
        headers: {},
        config: { headers: {} },
      } as any);

      const result = await botService.createBot(botData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/bots/', botData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle create bot error', async () => {
      const botData: BotCreate = {
        name: 'Test Bot',
        system_prompt: 'You are a helpful assistant',
        llm_provider: 'openai',
        llm_model: 'gpt-3.5-turbo',
      };

      const mockError = new Error('Validation failed');
      mockApiClient.post.mockRejectedValueOnce(mockError);

      await expect(botService.createBot(botData)).rejects.toThrow('Validation failed');
    });
  });

  describe('getUserBots', () => {
    it('should get user bots successfully', async () => {
      const mockBots: BotWithRole[] = [
        {
          bot: {
            id: '123',
            name: 'Test Bot 1',
            description: 'First test bot',
            system_prompt: 'You are a helpful assistant',
            owner_id: 'user123',
            llm_provider: 'openai',
            llm_model: 'gpt-3.5-turbo',
            temperature: 0.7,
            max_tokens: 1000,
            top_p: 1.0,
            frequency_penalty: 0.0,
            presence_penalty: 0.0,
            is_public: false,
            allow_collaboration: true,
            created_at: '2023-01-01T00:00:00Z',
            updated_at: '2023-01-01T00:00:00Z',
          },
          role: 'owner',
          granted_at: '2023-01-01T00:00:00Z',
        },
        {
          bot: {
            id: '456',
            name: 'Test Bot 2',
            description: 'Second test bot',
            system_prompt: 'You are a helpful assistant',
            owner_id: 'user456',
            llm_provider: 'anthropic',
            llm_model: 'claude-3-haiku',
            temperature: 0.5,
            max_tokens: 2000,
            top_p: 1.0,
            frequency_penalty: 0.0,
            presence_penalty: 0.0,
            is_public: true,
            allow_collaboration: true,
            created_at: '2023-01-02T00:00:00Z',
            updated_at: '2023-01-02T00:00:00Z',
          },
          role: 'editor',
          granted_at: '2023-01-02T00:00:00Z',
        },
      ];

      mockApiClient.get.mockResolvedValueOnce({
        data: mockBots,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      const result = await botService.getUserBots();

      expect(mockApiClient.get).toHaveBeenCalledWith('/bots/');
      expect(result).toEqual(mockBots);
    });
  });

  describe('getBot', () => {
    it('should get bot by ID successfully', async () => {
      const mockBot: BotResponse = {
        id: '123',
        name: 'Test Bot',
        description: 'A test bot',
        system_prompt: 'You are a helpful assistant',
        owner_id: 'user123',
        llm_provider: 'openai',
        llm_model: 'gpt-3.5-turbo',
        temperature: 0.7,
        max_tokens: 1000,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
        is_public: false,
        allow_collaboration: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      mockApiClient.get.mockResolvedValueOnce({
        data: mockBot,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      const result = await botService.getBot('123');

      expect(mockApiClient.get).toHaveBeenCalledWith('/bots/123');
      expect(result).toEqual(mockBot);
    });

    it('should handle bot not found error', async () => {
      const mockError = new Error('Bot not found');
      mockApiClient.get.mockRejectedValueOnce(mockError);

      await expect(botService.getBot('nonexistent')).rejects.toThrow('Bot not found');
    });
  });

  describe('updateBot', () => {
    it('should update bot successfully', async () => {
      const botId = '123';
      const updateData: BotUpdate = {
        name: 'Updated Bot Name',
        temperature: 0.8,
      };

      const mockResponse: BotResponse = {
        id: '123',
        name: 'Updated Bot Name',
        description: 'A test bot',
        system_prompt: 'You are a helpful assistant',
        owner_id: 'user123',
        llm_provider: 'openai',
        llm_model: 'gpt-3.5-turbo',
        temperature: 0.8,
        max_tokens: 1000,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
        is_public: false,
        allow_collaboration: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T01:00:00Z',
      };

      mockApiClient.put.mockResolvedValueOnce({
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      const result = await botService.updateBot(botId, updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith(`/bots/${botId}`, updateData);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteBot', () => {
    it('should delete bot successfully', async () => {
      const botId = '123';

      mockApiClient.delete.mockResolvedValueOnce({
        data: {},
        status: 204,
        statusText: 'No Content',
        headers: {},
        config: { headers: {} },
      } as any);

      await botService.deleteBot(botId);

      expect(mockApiClient.delete).toHaveBeenCalledWith(`/bots/${botId}`);
    });

    it('should handle delete bot error', async () => {
      const botId = '123';
      const mockError = new Error('Insufficient permissions');
      mockApiClient.delete.mockRejectedValueOnce(mockError);

      await expect(botService.deleteBot(botId)).rejects.toThrow('Insufficient permissions');
    });
  });

  describe('transferOwnership', () => {
    it('should transfer ownership successfully', async () => {
      const botId = '123';
      const transferRequest: BotTransferRequest = {
        new_owner_id: 'user456',
      };

      mockApiClient.post.mockResolvedValueOnce({
        data: {},
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      await botService.transferOwnership(botId, transferRequest);

      expect(mockApiClient.post).toHaveBeenCalledWith(`/bots/${botId}/transfer`, transferRequest);
    });

    it('should handle transfer ownership error', async () => {
      const botId = '123';
      const transferRequest: BotTransferRequest = {
        new_owner_id: 'nonexistent',
      };

      const mockError = new Error('User not found');
      mockApiClient.post.mockRejectedValueOnce(mockError);

      await expect(botService.transferOwnership(botId, transferRequest)).rejects.toThrow('User not found');
    });
  });

  describe('getBotAnalytics', () => {
    it('should get bot analytics successfully', async () => {
      const botId = '123';
      const mockAnalytics = {
        total_conversations: 10,
        total_messages: 50,
        total_documents: 3,
        total_collaborators: 2,
        last_activity: '2023-01-01T12:00:00Z',
        usage_by_day: [
          { date: '2023-01-01', conversations: 5, messages: 25 },
          { date: '2023-01-02', conversations: 5, messages: 25 },
        ],
        top_collaborators: [
          { user_id: 'user123', username: 'testuser', message_count: 30 },
          { user_id: 'user456', username: 'collaborator', message_count: 20 },
        ],
      };

      mockApiClient.get.mockResolvedValueOnce({
        data: mockAnalytics,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      const result = await botService.getBotAnalytics(botId);

      expect(mockApiClient.get).toHaveBeenCalledWith(`/bots/${botId}/analytics`);
      expect(result).toEqual(mockAnalytics);
    });
  });

  describe('searchUsers', () => {
    it('should search users successfully', async () => {
      const query = 'test';
      const mockUsers = [
        { id: 'user123', username: 'testuser', email: 'test@example.com' },
        { id: 'user456', username: 'testuser2', email: 'test2@example.com' },
      ];

      mockApiClient.get.mockResolvedValueOnce({
        data: mockUsers,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      const result = await botService.searchUsers(query);

      expect(mockApiClient.get).toHaveBeenCalledWith(`/users/search?q=${encodeURIComponent(query)}`);
      expect(result).toEqual(mockUsers);
    });
  });

  describe('validateBotConfig', () => {
    it('should validate valid bot config', () => {
      const validConfig: BotCreate = {
        name: 'Valid Bot',
        system_prompt: 'You are a helpful assistant',
        llm_provider: 'openai',
        llm_model: 'gpt-3.5-turbo',
        temperature: 0.7,
        max_tokens: 1000,
        top_p: 0.9,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
      };

      const result = botService.validateBotConfig(validConfig);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should validate invalid bot config', () => {
      const invalidConfig: BotCreate = {
        name: '', // Invalid: empty name
        system_prompt: '', // Invalid: empty system prompt
        llm_provider: 'openai',
        llm_model: 'gpt-3.5-turbo',
        temperature: 3.0, // Invalid: temperature > 2
        max_tokens: -1, // Invalid: negative max_tokens
        top_p: 1.5, // Invalid: top_p > 1
        frequency_penalty: 3.0, // Invalid: frequency_penalty > 2
        presence_penalty: -3.0, // Invalid: presence_penalty < -2
      };

      const result = botService.validateBotConfig(invalidConfig);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Bot name must be between 1 and 255 characters');
      expect(result.errors).toContain('System prompt is required');
      expect(result.errors).toContain('Temperature must be between 0 and 2');
      expect(result.errors).toContain('Max tokens must be between 1 and 8000');
      expect(result.errors).toContain('Top P must be between 0 and 1');
      expect(result.errors).toContain('Frequency penalty must be between -2 and 2');
      expect(result.errors).toContain('Presence penalty must be between -2 and 2');
    });

    it('should validate bot name length limits', () => {
      const longName = 'a'.repeat(256); // 256 characters, exceeds limit
      const invalidConfig: BotUpdate = {
        name: longName,
      };

      const result = botService.validateBotConfig(invalidConfig);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Bot name must be between 1 and 255 characters');
    });

    it('should validate parameter ranges', () => {
      const invalidConfig: BotUpdate = {
        temperature: -0.1, // Below minimum
        max_tokens: 8001, // Above maximum
        top_p: -0.1, // Below minimum
        frequency_penalty: 2.1, // Above maximum
        presence_penalty: -2.1, // Below minimum
      };

      const result = botService.validateBotConfig(invalidConfig);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Temperature must be between 0 and 2');
      expect(result.errors).toContain('Max tokens must be between 1 and 8000');
      expect(result.errors).toContain('Top P must be between 0 and 1');
      expect(result.errors).toContain('Frequency penalty must be between -2 and 2');
      expect(result.errors).toContain('Presence penalty must be between -2 and 2');
    });
  });

  describe('getProviderSettings', () => {
    it('should return provider settings', async () => {
      const result = await botService.getProviderSettings();

      expect(result).toHaveProperty('llm_providers');
      expect(result).toHaveProperty('embedding_providers');
      expect(result.llm_providers).toHaveProperty('openai');
      expect(result.llm_providers).toHaveProperty('anthropic');
      expect(result.llm_providers).toHaveProperty('gemini');
      expect(result.llm_providers).toHaveProperty('openrouter');
      expect(result.embedding_providers).toHaveProperty('openai');
      expect(result.embedding_providers).toHaveProperty('gemini');
      expect(result.embedding_providers).toHaveProperty('local');
    });

    it('should have correct provider configurations', async () => {
      const result = await botService.getProviderSettings();

      // Check OpenAI configuration
      const openaiLLM = result.llm_providers.openai;
      expect(openaiLLM.display_name).toBe('OpenAI');
      expect(openaiLLM.supports_embeddings).toBe(true);
      expect(openaiLLM.models).toContainEqual(
        expect.objectContaining({ id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' })
      );

      // Check Anthropic configuration
      const anthropicLLM = result.llm_providers.anthropic;
      expect(anthropicLLM.display_name).toBe('Anthropic');
      expect(anthropicLLM.supports_embeddings).toBe(false);
      expect(anthropicLLM.models).toContainEqual(
        expect.objectContaining({ id: 'claude-3-haiku', name: 'Claude 3 Haiku' })
      );

      // Check embedding providers
      const openaiEmbedding = result.embedding_providers.openai;
      expect(openaiEmbedding.supports_embeddings).toBe(true);
      expect(openaiEmbedding.models).toContainEqual(
        expect.objectContaining({ id: 'text-embedding-3-small', name: 'Text Embedding 3 Small' })
      );
    });
  });
});