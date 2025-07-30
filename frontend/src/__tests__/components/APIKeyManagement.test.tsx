/**
 * Unit tests for APIKeyManagement component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { APIKeyManagement } from '../../components/apikeys/APIKeyManagement';
import { apiKeyService } from '../../services/apiKeyService';
import {
  APIKeyResponse,
  ProvidersResponse,
} from '../../types/api';

// Mock the API key service
vi.mock('../../services/apiKeyService');

const mockApiKeyService = vi.mocked(apiKeyService);

describe('APIKeyManagement', () => {
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

  const mockProviders: ProvidersResponse = {
    providers: {
      openai: {
        name: 'openai',
        models: ['gpt-3.5-turbo', 'gpt-4'],
      },
      anthropic: {
        name: 'anthropic',
        models: ['claude-3-haiku', 'claude-3-sonnet'],
      },
      gemini: {
        name: 'gemini',
        models: ['gemini-pro'],
      },
      openrouter: {
        name: 'openrouter',
        models: ['openrouter/auto'],
      },
    },
    total: 4,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default successful responses
    mockApiKeyService.getAPIKeys.mockResolvedValue(mockAPIKeys);
    mockApiKeyService.getSupportedProviders.mockResolvedValue(mockProviders);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Loading', () => {
    it('should render loading state initially', async () => {
      // Make the API calls hang to test loading state
      mockApiKeyService.getAPIKeys.mockImplementation(() => new Promise(() => {}));
      mockApiKeyService.getSupportedProviders.mockImplementation(() => new Promise(() => {}));

      render(<APIKeyManagement />);

      expect(screen.getByText('API Key Management')).toBeInTheDocument();
      expect(screen.getByText('Manage your API keys for different LLM providers')).toBeInTheDocument();
    });

    it('should load API keys and providers on mount', async () => {
      render(<APIKeyManagement />);

      await waitFor(() => {
        expect(mockApiKeyService.getAPIKeys).toHaveBeenCalledTimes(1);
        expect(mockApiKeyService.getSupportedProviders).toHaveBeenCalledTimes(1);
      });

      expect(screen.getByText('Your API Keys')).toBeInTheDocument();
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
    });

    it('should display error message when loading fails', async () => {
      mockApiKeyService.getAPIKeys.mockRejectedValue(new Error('Network error'));
      mockApiKeyService.getSupportedProviders.mockRejectedValue(new Error('Network error'));

      render(<APIKeyManagement />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load API keys and providers')).toBeInTheDocument();
      });
    });
  });

  describe('API Key List View', () => {
    it('should display existing API keys', async () => {
      render(<APIKeyManagement />);

      await waitFor(() => {
        expect(screen.getByText('OpenAI')).toBeInTheDocument();
        expect(screen.getByText('Anthropic')).toBeInTheDocument();
      });

      // Should show edit and delete buttons for each key
      const editButtons = screen.getAllByText('Edit');
      const deleteButtons = screen.getAllByText('Delete');
      
      expect(editButtons).toHaveLength(2);
      expect(deleteButtons).toHaveLength(2);
    });

    it('should show empty state when no API keys exist', async () => {
      mockApiKeyService.getAPIKeys.mockResolvedValue([]);

      render(<APIKeyManagement />);

      await waitFor(() => {
        expect(screen.getByText('No API Keys')).toBeInTheDocument();
        expect(screen.getByText('Add your first API key to start using the platform with your preferred LLM provider.')).toBeInTheDocument();
      });
    });

    it('should show Add API Key button when available providers exist', async () => {
      // Only return one API key so there are available providers
      mockApiKeyService.getAPIKeys.mockResolvedValue([mockAPIKeys[0]]);

      render(<APIKeyManagement />);

      await waitFor(() => {
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
      });
    });

    it('should disable Add API Key button when all providers are used', async () => {
      // Return API keys for all providers
      const allProvidersUsed: APIKeyResponse[] = [
        { id: '1', provider: 'openai', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
        { id: '2', provider: 'anthropic', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
        { id: '3', provider: 'gemini', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
        { id: '4', provider: 'openrouter', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
      ];
      
      mockApiKeyService.getAPIKeys.mockResolvedValue(allProvidersUsed);

      render(<APIKeyManagement />);

      await waitFor(() => {
        const addButton = screen.getByText('Add API Key');
        expect(addButton).toBeDisabled();
      });
    });
  });

  describe('Add API Key Flow', () => {
    it('should show add form when Add API Key button is clicked', async () => {
      mockApiKeyService.getAPIKeys.mockResolvedValue([mockAPIKeys[0]]); // Only one key

      render(<APIKeyManagement />);

      await waitFor(() => {
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add API Key'));

      expect(screen.getByText('Add API Key')).toBeInTheDocument();
      expect(screen.getByText('Provider')).toBeInTheDocument();
      expect(screen.getByText('API Key')).toBeInTheDocument();
    });

    it('should successfully add new API key', async () => {
      mockApiKeyService.getAPIKeys.mockResolvedValue([mockAPIKeys[0]]); // Only one key initially
      
      const newAPIKey: APIKeyResponse = {
        id: '3',
        provider: 'gemini',
        is_active: true,
        created_at: '2023-01-03T00:00:00Z',
        updated_at: '2023-01-03T00:00:00Z',
      };
      
      mockApiKeyService.addAPIKey.mockResolvedValue(newAPIKey);

      render(<APIKeyManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add API Key'));
      });

      // Fill out the form
      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');
      
      fireEvent.change(providerSelect, { target: { value: 'gemini' } });
      fireEvent.change(apiKeyInput, { target: { value: 'AIza-test123' } });

      // Submit the form
      fireEvent.click(screen.getByText('Add API Key'));

      await waitFor(() => {
        expect(mockApiKeyService.addAPIKey).toHaveBeenCalledWith({
          provider: 'gemini',
          api_key: 'AIza-test123',
        });
      });

      // Should show success message and return to list view
      await waitFor(() => {
        expect(screen.getByText('API key for gemini added successfully')).toBeInTheDocument();
      });
    });

    it('should handle add API key error', async () => {
      mockApiKeyService.getAPIKeys.mockResolvedValue([mockAPIKeys[0]]);
      mockApiKeyService.addAPIKey.mockRejectedValue({
        response: { data: { detail: 'Invalid API key' } }
      });

      render(<APIKeyManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add API Key'));
      });

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');
      
      fireEvent.change(providerSelect, { target: { value: 'gemini' } });
      fireEvent.change(apiKeyInput, { target: { value: 'invalid-key' } });
      fireEvent.click(screen.getByText('Add API Key'));

      await waitFor(() => {
        expect(screen.getByText('Invalid API key')).toBeInTheDocument();
      });
    });

    it('should cancel add operation and return to list', async () => {
      mockApiKeyService.getAPIKeys.mockResolvedValue([mockAPIKeys[0]]);

      render(<APIKeyManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add API Key'));
      });

      expect(screen.getByText('Cancel')).toBeInTheDocument();
      fireEvent.click(screen.getByText('Cancel'));

      await waitFor(() => {
        expect(screen.getByText('Your API Keys')).toBeInTheDocument();
      });
    });
  });

  describe('Edit API Key Flow', () => {
    it('should show edit form when Edit button is clicked', async () => {
      render(<APIKeyManagement />);

      await waitFor(() => {
        const editButtons = screen.getAllByText('Edit');
        fireEvent.click(editButtons[0]);
      });

      expect(screen.getByText('Update API Key')).toBeInTheDocument();
      expect(screen.getByDisplayValue('openai')).toBeInTheDocument();
    });

    it('should successfully update API key', async () => {
      const updatedAPIKey: APIKeyResponse = {
        ...mockAPIKeys[0],
        updated_at: '2023-01-01T12:00:00Z',
      };
      
      mockApiKeyService.updateAPIKey.mockResolvedValue(updatedAPIKey);

      render(<APIKeyManagement />);

      await waitFor(() => {
        const editButtons = screen.getAllByText('Edit');
        fireEvent.click(editButtons[0]);
      });

      const apiKeyInput = screen.getByLabelText('API Key');
      fireEvent.change(apiKeyInput, { target: { value: 'sk-updated123' } });
      fireEvent.click(screen.getByText('Update API Key'));

      await waitFor(() => {
        expect(mockApiKeyService.updateAPIKey).toHaveBeenCalledWith('openai', {
          api_key: 'sk-updated123',
          is_active: true,
        });
      });

      await waitFor(() => {
        expect(screen.getByText('API key for openai updated successfully')).toBeInTheDocument();
      });
    });
  });

  describe('Delete API Key Flow', () => {
    it('should show confirmation on first delete click', async () => {
      render(<APIKeyManagement />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByText('Delete');
        fireEvent.click(deleteButtons[0]);
      });

      expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('should successfully delete API key on confirmation', async () => {
      mockApiKeyService.deleteAPIKey.mockResolvedValue();

      render(<APIKeyManagement />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByText('Delete');
        fireEvent.click(deleteButtons[0]);
      });

      // Click confirm delete
      fireEvent.click(screen.getByText('Confirm Delete'));

      await waitFor(() => {
        expect(mockApiKeyService.deleteAPIKey).toHaveBeenCalledWith('openai');
      });

      await waitFor(() => {
        expect(screen.getByText('API key for openai deleted successfully')).toBeInTheDocument();
      });
    });

    it('should cancel delete operation', async () => {
      render(<APIKeyManagement />);

      await waitFor(() => {
        const deleteButtons = screen.getAllByText('Delete');
        fireEvent.click(deleteButtons[0]);
      });

      // Click cancel
      fireEvent.click(screen.getByText('Cancel'));

      // Should return to normal delete button
      expect(screen.getAllByText('Delete')).toHaveLength(2);
      expect(screen.queryByText('Confirm Delete')).not.toBeInTheDocument();
    });
  });

  describe('Message Handling', () => {
    it('should auto-hide success messages after 5 seconds', async () => {
      vi.useFakeTimers();
      
      mockApiKeyService.getAPIKeys.mockResolvedValue([mockAPIKeys[0]]);
      mockApiKeyService.addAPIKey.mockResolvedValue({
        id: '3',
        provider: 'gemini',
        is_active: true,
        created_at: '2023-01-03T00:00:00Z',
        updated_at: '2023-01-03T00:00:00Z',
      });

      render(<APIKeyManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Add API Key'));
      });

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');
      
      fireEvent.change(providerSelect, { target: { value: 'gemini' } });
      fireEvent.change(apiKeyInput, { target: { value: 'AIza-test123' } });
      fireEvent.click(screen.getByText('Add API Key'));

      await waitFor(() => {
        expect(screen.getByText('API key for gemini added successfully')).toBeInTheDocument();
      });

      // Fast-forward 5 seconds
      vi.advanceTimersByTime(5000);

      await waitFor(() => {
        expect(screen.queryByText('API key for gemini added successfully')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('should auto-hide error messages after 5 seconds', async () => {
      vi.useFakeTimers();
      
      mockApiKeyService.getAPIKeys.mockRejectedValue(new Error('Network error'));
      mockApiKeyService.getSupportedProviders.mockRejectedValue(new Error('Network error'));

      render(<APIKeyManagement />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load API keys and providers')).toBeInTheDocument();
      });

      // Fast-forward 5 seconds
      vi.advanceTimersByTime(5000);

      await waitFor(() => {
        expect(screen.queryByText('Failed to load API keys and providers')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });
  });
});