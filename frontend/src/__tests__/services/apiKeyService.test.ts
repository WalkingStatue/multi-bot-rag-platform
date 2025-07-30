/**
 * Unit tests for APIKeyService
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiKeyService } from '../../services/apiKeyService';
import { apiClient } from '../../services/api';
import {
  APIKeyResponse,
  APIKeyCreate,
  APIKeyUpdate,
  APIKeyValidationResponse,
  ProvidersResponse,
} from '../../types/api';

// Mock the API client
vi.mock('../../services/api');

const mockApiClient = vi.mocked(apiClient);

describe('APIKeyService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getAPIKeys', () => {
    it('should fetch API keys successfully', async () => {
      const mockAPIKeys: APIKeyResponse[] = [
        {
          id: '1',
          provider: 'openai',
          is_active: true,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
        },
        {
          id: '2',
          provider: 'anthropic',
          is_active: true,
          created_at: '2023-01-02T00:00:00Z',
          updated_at: '2023-01-02T00:00:00Z',
        },
      ];

      const mockResponse = {
        data: mockAPIKeys,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.get.mockResolvedValueOnce(mockResponse);

      const result = await apiKeyService.getAPIKeys();

      expect(mockApiClient.get).toHaveBeenCalledWith('/users/api-keys');
      expect(result).toEqual(mockAPIKeys);
    });

    it('should handle API error when fetching API keys', async () => {
      const mockError = new Error('Failed to fetch API keys');
      mockApiClient.get.mockRejectedValueOnce(mockError);

      await expect(apiKeyService.getAPIKeys()).rejects.toThrow('Failed to fetch API keys');
    });
  });

  describe('addAPIKey', () => {
    it('should add API key successfully', async () => {
      const apiKeyData: APIKeyCreate = {
        provider: 'openai',
        api_key: 'sk-test123',
      };

      const mockResponse: APIKeyResponse = {
        id: '1',
        provider: 'openai',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      };

      const mockApiResponse = {
        data: mockResponse,
        status: 201,
        statusText: 'Created',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.post.mockResolvedValueOnce(mockApiResponse);

      const result = await apiKeyService.addAPIKey(apiKeyData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/users/api-keys', apiKeyData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle validation error when adding API key', async () => {
      const apiKeyData: APIKeyCreate = {
        provider: 'openai',
        api_key: 'invalid-key',
      };

      const mockError = {
        response: {
          data: {
            detail: 'Invalid API key format',
          },
          status: 400,
        },
      };

      mockApiClient.post.mockRejectedValueOnce(mockError);

      await expect(apiKeyService.addAPIKey(apiKeyData)).rejects.toEqual(mockError);
    });
  });

  describe('updateAPIKey', () => {
    it('should update API key successfully', async () => {
      const provider = 'openai';
      const updateData: APIKeyUpdate = {
        api_key: 'sk-updated123',
        is_active: true,
      };

      const mockResponse: APIKeyResponse = {
        id: '1',
        provider: 'openai',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T12:00:00Z',
      };

      const mockApiResponse = {
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.put.mockResolvedValueOnce(mockApiResponse);

      const result = await apiKeyService.updateAPIKey(provider, updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith(`/users/api-keys/${provider}`, updateData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle not found error when updating API key', async () => {
      const provider = 'nonexistent';
      const updateData: APIKeyUpdate = {
        api_key: 'sk-test123',
      };

      const mockError = {
        response: {
          data: {
            detail: 'API key not found',
          },
          status: 404,
        },
      };

      mockApiClient.put.mockRejectedValueOnce(mockError);

      await expect(apiKeyService.updateAPIKey(provider, updateData)).rejects.toEqual(mockError);
    });
  });

  describe('deleteAPIKey', () => {
    it('should delete API key successfully', async () => {
      const provider = 'openai';

      const mockResponse = {
        status: 204,
        statusText: 'No Content',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.delete.mockResolvedValueOnce(mockResponse);

      await apiKeyService.deleteAPIKey(provider);

      expect(mockApiClient.delete).toHaveBeenCalledWith(`/users/api-keys/${provider}`);
    });

    it('should handle not found error when deleting API key', async () => {
      const provider = 'nonexistent';

      const mockError = {
        response: {
          data: {
            detail: 'API key not found',
          },
          status: 404,
        },
      };

      mockApiClient.delete.mockRejectedValueOnce(mockError);

      await expect(apiKeyService.deleteAPIKey(provider)).rejects.toEqual(mockError);
    });
  });

  describe('validateAPIKey', () => {
    it('should validate API key successfully', async () => {
      const provider = 'openai';
      const apiKey = 'sk-test123';

      const mockResponse: APIKeyValidationResponse = {
        valid: true,
        provider: 'openai',
        message: 'API key is valid',
      };

      const mockApiResponse = {
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.post.mockResolvedValueOnce(mockApiResponse);

      const result = await apiKeyService.validateAPIKey(provider, apiKey);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        `/users/api-keys/${provider}/validate`,
        { provider, api_key: apiKey }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should return invalid result for invalid API key', async () => {
      const provider = 'openai';
      const apiKey = 'invalid-key';

      const mockResponse: APIKeyValidationResponse = {
        valid: false,
        provider: 'openai',
        message: 'API key is invalid',
      };

      const mockApiResponse = {
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.post.mockResolvedValueOnce(mockApiResponse);

      const result = await apiKeyService.validateAPIKey(provider, apiKey);

      expect(result.valid).toBe(false);
      expect(result.message).toBe('API key is invalid');
    });

    it('should handle validation service error', async () => {
      const provider = 'openai';
      const apiKey = 'sk-test123';

      const mockError = new Error('Validation service unavailable');
      mockApiClient.post.mockRejectedValueOnce(mockError);

      await expect(apiKeyService.validateAPIKey(provider, apiKey)).rejects.toThrow(
        'Validation service unavailable'
      );
    });
  });

  describe('getSupportedProviders', () => {
    it('should fetch supported providers successfully', async () => {
      const mockResponse: ProvidersResponse = {
        providers: {
          openai: {
            name: 'openai',
            models: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
          },
          anthropic: {
            name: 'anthropic',
            models: ['claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus'],
          },
          gemini: {
            name: 'gemini',
            models: ['gemini-pro', 'gemini-pro-vision'],
          },
          openrouter: {
            name: 'openrouter',
            models: ['openrouter/auto', 'anthropic/claude-3-opus'],
          },
        },
        total: 4,
      };

      const mockApiResponse = {
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.get.mockResolvedValueOnce(mockApiResponse);

      const result = await apiKeyService.getSupportedProviders();

      expect(mockApiClient.get).toHaveBeenCalledWith('/users/api-keys/providers');
      expect(result).toEqual(mockResponse);
      expect(result.total).toBe(4);
      expect(Object.keys(result.providers)).toHaveLength(4);
    });

    it('should handle error when fetching providers', async () => {
      const mockError = new Error('Failed to fetch providers');
      mockApiClient.get.mockRejectedValueOnce(mockError);

      await expect(apiKeyService.getSupportedProviders()).rejects.toThrow(
        'Failed to fetch providers'
      );
    });
  });
});