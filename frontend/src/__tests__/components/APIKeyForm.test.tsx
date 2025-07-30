/**
 * Unit tests for APIKeyForm component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { APIKeyForm } from '../../components/apikeys/APIKeyForm';
import { apiKeyService } from '../../services/apiKeyService';
import { ProviderInfo } from '../../types/api';

// Mock the API key service
vi.mock('../../services/apiKeyService');

const mockApiKeyService = vi.mocked(apiKeyService);

describe('APIKeyForm', () => {
  const mockProviders: Record<string, ProviderInfo> = {
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
  };

  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Add Mode', () => {
    it('should render add form correctly', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      expect(screen.getByText('Add API Key')).toBeInTheDocument();
      expect(screen.getByLabelText('Provider')).toBeInTheDocument();
      expect(screen.getByLabelText('API Key')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Add API Key')).toBeInTheDocument();
    });

    it('should show provider options in select', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      expect(screen.getByText('Select a provider')).toBeInTheDocument();
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('Google Gemini')).toBeInTheDocument();
    });

    it('should update placeholder when provider is selected', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key') as HTMLInputElement;

      // Select OpenAI
      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      expect(apiKeyInput.placeholder).toBe('sk-...');

      // Select Anthropic
      fireEvent.change(providerSelect, { target: { value: 'anthropic' } });
      expect(apiKeyInput.placeholder).toBe('sk-ant-...');

      // Select Gemini
      fireEvent.change(providerSelect, { target: { value: 'gemini' } });
      expect(apiKeyInput.placeholder).toBe('AIza...');
    });

    it('should show available models when provider is selected', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      fireEvent.change(providerSelect, { target: { value: 'openai' } });

      expect(screen.getByText('Available Models')).toBeInTheDocument();
      expect(screen.getByText('gpt-3.5-turbo')).toBeInTheDocument();
      expect(screen.getByText('gpt-4')).toBeInTheDocument();
      expect(screen.getByText('gpt-4-turbo')).toBeInTheDocument();
    });

    it('should submit form with correct data', async () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');
      const submitButton = screen.getByText('Add API Key');

      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          provider: 'openai',
          api_key: 'sk-test123',
        });
      });
    });

    it('should not submit form with empty fields', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const submitButton = screen.getByText('Add API Key');
      expect(submitButton).toBeDisabled();

      // Add provider but no API key
      const providerSelect = screen.getByLabelText('Provider');
      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      expect(submitButton).toBeDisabled();

      // Add API key
      const apiKeyInput = screen.getByLabelText('API Key');
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });
      expect(submitButton).not.toBeDisabled();
    });

    it('should call onCancel when cancel button is clicked', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edit Mode', () => {
    it('should render edit form correctly', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
          initialProvider="openai"
        />
      );

      expect(screen.getByText('Update API Key')).toBeInTheDocument();
      expect(screen.getByDisplayValue('openai')).toBeInTheDocument();
      expect(screen.getByText('Update API Key')).toBeInTheDocument();
    });

    it('should disable provider selection in edit mode', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
          initialProvider="openai"
        />
      );

      const providerSelect = screen.getByLabelText('Provider') as HTMLSelectElement;
      expect(providerSelect.disabled).toBe(true);
      expect(providerSelect.value).toBe('openai');
    });

    it('should show models for initial provider in edit mode', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
          initialProvider="openai"
        />
      );

      expect(screen.getByText('Available Models')).toBeInTheDocument();
      expect(screen.getByText('gpt-3.5-turbo')).toBeInTheDocument();
      expect(screen.getByText('gpt-4')).toBeInTheDocument();
    });
  });

  describe('API Key Validation', () => {
    it('should show validate button when provider and API key are entered', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');

      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

      expect(screen.getByText('Validate')).toBeInTheDocument();
    });

    it('should validate API key successfully', async () => {
      mockApiKeyService.validateAPIKey.mockResolvedValue({
        valid: true,
        provider: 'openai',
        message: 'API key is valid',
      });

      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');

      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      expect(screen.getByText('Validating...')).toBeInTheDocument();

      await waitFor(() => {
        expect(mockApiKeyService.validateAPIKey).toHaveBeenCalledWith('openai', 'sk-test123');
      });

      await waitFor(() => {
        expect(screen.getByText('API key is valid')).toBeInTheDocument();
      });
    });

    it('should show invalid API key message', async () => {
      mockApiKeyService.validateAPIKey.mockResolvedValue({
        valid: false,
        provider: 'openai',
        message: 'API key is invalid',
      });

      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');

      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'invalid-key' } });

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText('API key is invalid')).toBeInTheDocument();
      });
    });

    it('should handle validation error', async () => {
      mockApiKeyService.validateAPIKey.mockRejectedValue(new Error('Network error'));

      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');

      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to validate API key')).toBeInTheDocument();
      });
    });

    it('should clear validation status when provider changes', () => {
      mockApiKeyService.validateAPIKey.mockResolvedValue({
        valid: true,
        provider: 'openai',
        message: 'API key is valid',
      });

      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');

      // Set initial values and validate
      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      // Change provider - should clear validation
      fireEvent.change(providerSelect, { target: { value: 'anthropic' } });

      expect(screen.queryByText('API key is valid')).not.toBeInTheDocument();
    });

    it('should clear validation status when API key changes', () => {
      mockApiKeyService.validateAPIKey.mockResolvedValue({
        valid: true,
        provider: 'openai',
        message: 'API key is valid',
      });

      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');

      // Set initial values and validate
      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      // Change API key - should clear validation
      fireEvent.change(apiKeyInput, { target: { value: 'sk-different123' } });

      expect(screen.queryByText('API key is valid')).not.toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('should show loading state when submitting', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
          isLoading={true}
        />
      );

      expect(screen.getByText('Saving...')).toBeInTheDocument();
      
      const submitButton = screen.getByText('Saving...');
      expect(submitButton).toBeDisabled();
    });

    it('should disable form during validation', async () => {
      // Make validation hang to test loading state
      mockApiKeyService.validateAPIKey.mockImplementation(() => new Promise(() => {}));

      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={mockProviders}
        />
      );

      const providerSelect = screen.getByLabelText('Provider');
      const apiKeyInput = screen.getByLabelText('API Key');

      fireEvent.change(providerSelect, { target: { value: 'openai' } });
      fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      expect(screen.getByText('Validating...')).toBeInTheDocument();
      expect(validateButton).toBeDisabled();
    });
  });

  describe('Provider Display Names', () => {
    it('should show correct display names for providers', () => {
      render(
        <APIKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          providers={{
            openai: { name: 'openai', models: [] },
            anthropic: { name: 'anthropic', models: [] },
            openrouter: { name: 'openrouter', models: [] },
            gemini: { name: 'gemini', models: [] },
          }}
        />
      );

      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('OpenRouter')).toBeInTheDocument();
      expect(screen.getByText('Google Gemini')).toBeInTheDocument();
    });
  });
});