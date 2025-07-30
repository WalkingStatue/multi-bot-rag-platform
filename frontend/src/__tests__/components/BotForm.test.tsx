/**
 * Unit tests for BotForm component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BotForm } from '../../components/bots/BotForm';
import { botService } from '../../services/botService';
import { BotResponse } from '../../types/bot';

// Mock the bot service
vi.mock('../../services/botService');

const mockBotService = vi.mocked(botService);

describe('BotForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  const mockProviderSettings = {
    llm_providers: {
      openai: {
        name: 'openai',
        display_name: 'OpenAI',
        models: [
          { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', max_tokens: 4096 },
          { id: 'gpt-4', name: 'GPT-4', max_tokens: 8192 },
        ],
        default_model: 'gpt-3.5-turbo',
        supports_embeddings: true,
        embedding_models: [
          { id: 'text-embedding-3-small', name: 'Text Embedding 3 Small' },
        ],
        default_embedding_model: 'text-embedding-3-small',
      },
      anthropic: {
        name: 'anthropic',
        display_name: 'Anthropic',
        models: [
          { id: 'claude-3-haiku', name: 'Claude 3 Haiku', max_tokens: 4096 },
        ],
        default_model: 'claude-3-haiku',
        supports_embeddings: false,
      },
    },
    embedding_providers: {
      openai: {
        name: 'openai',
        display_name: 'OpenAI',
        models: [
          { id: 'text-embedding-3-small', name: 'Text Embedding 3 Small' },
        ],
        default_model: 'text-embedding-3-small',
        supports_embeddings: true,
      },
      local: {
        name: 'local',
        display_name: 'Local Models',
        models: [
          { id: 'sentence-transformers/all-MiniLM-L6-v2', name: 'All-MiniLM-L6-v2' },
        ],
        default_model: 'sentence-transformers/all-MiniLM-L6-v2',
        supports_embeddings: true,
      },
    },
  };

  beforeEach(() => {
    mockBotService.getProviderSettings.mockResolvedValue(mockProviderSettings);
    mockBotService.validateBotConfig.mockReturnValue({ valid: true, errors: [] });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Create Mode', () => {
    it('should render create form with default values', async () => {
      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('')).toBeInTheDocument(); // Bot name input
      });

      expect(screen.getByText('Create New Bot')).toBeInTheDocument();
      expect(screen.getByLabelText(/Bot Name/)).toHaveValue('');
      expect(screen.getByLabelText(/Description/)).toHaveValue('');
      expect(screen.getByLabelText(/Provider/)).toHaveValue('openai');
      expect(screen.getByLabelText(/Temperature/)).toHaveValue('0.7');
      expect(screen.getByText('Create Bot')).toBeInTheDocument();
    });

    it('should load provider settings on mount', async () => {
      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(mockBotService.getProviderSettings).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText('OpenAI')).toBeInTheDocument();
        expect(screen.getByText('Anthropic')).toBeInTheDocument();
      });
    });

    it('should update model when provider changes', async () => {
      const user = userEvent.setup();

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/Provider/)).toBeInTheDocument();
      });

      const providerSelect = screen.getByLabelText(/Provider/);
      await user.selectOptions(providerSelect, 'anthropic');

      await waitFor(() => {
        expect(screen.getByDisplayValue('claude-3-haiku')).toBeInTheDocument();
      });
    });

    it('should validate form data in real-time', async () => {
      const user = userEvent.setup();

      mockBotService.validateBotConfig.mockReturnValue({
        valid: false,
        errors: ['Bot name must be between 1 and 255 characters'],
      });

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/Bot Name/);
      await user.clear(nameInput);

      await waitFor(() => {
        expect(screen.getByText('Bot name must be between 1 and 255 characters')).toBeInTheDocument();
      });
    });

    it('should submit form with correct data', async () => {
      const user = userEvent.setup();

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      // Fill out the form
      await user.type(screen.getByLabelText(/Bot Name/), 'Test Bot');
      await user.type(screen.getByLabelText(/Description/), 'A test bot');
      await user.type(screen.getByLabelText(/Instructions for the AI/), 'You are a helpful assistant');

      // Submit the form
      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Bot',
            description: 'A test bot',
            system_prompt: 'You are a helpful assistant',
            llm_provider: 'openai',
            llm_model: 'gpt-3.5-turbo',
            temperature: 0.7,
            max_tokens: 1000,
            is_public: false,
            allow_collaboration: true,
          })
        );
      });
    });

    it('should handle form cancellation', async () => {
      const user = userEvent.setup();

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await user.click(screen.getByText('Cancel'));

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should disable submit button when form is invalid', async () => {
      mockBotService.validateBotConfig.mockReturnValue({
        valid: false,
        errors: ['Bot name is required'],
      });

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        const submitButton = screen.getByText('Create Bot');
        expect(submitButton).toBeDisabled();
      });
    });
  });

  describe('Edit Mode', () => {
    const mockBotData: BotResponse = {
      id: '123',
      name: 'Existing Bot',
      description: 'An existing bot',
      system_prompt: 'You are an existing assistant',
      owner_id: 'user123',
      llm_provider: 'anthropic',
      llm_model: 'claude-3-haiku',
      embedding_provider: 'openai',
      embedding_model: 'text-embedding-3-small',
      temperature: 0.5,
      max_tokens: 2000,
      top_p: 0.9,
      frequency_penalty: 0.1,
      presence_penalty: 0.2,
      is_public: true,
      allow_collaboration: false,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    };

    it('should render edit form with initial data', async () => {
      render(
        <BotForm
          mode="edit"
          initialData={mockBotData}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('Existing Bot')).toBeInTheDocument();
      });

      expect(screen.getByText('Edit Bot')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Existing Bot')).toBeInTheDocument();
      expect(screen.getByDisplayValue('An existing bot')).toBeInTheDocument();
      expect(screen.getByDisplayValue('You are an existing assistant')).toBeInTheDocument();
      expect(screen.getByDisplayValue('anthropic')).toBeInTheDocument();
      expect(screen.getByDisplayValue('claude-3-haiku')).toBeInTheDocument();
      expect(screen.getByDisplayValue('0.5')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2000')).toBeInTheDocument();
      expect(screen.getByText('Update Bot')).toBeInTheDocument();
    });

    it('should update form when initial data changes', async () => {
      const { rerender } = render(
        <BotForm
          mode="edit"
          initialData={mockBotData}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('Existing Bot')).toBeInTheDocument();
      });

      const updatedBotData = { ...mockBotData, name: 'Updated Bot' };
      rerender(
        <BotForm
          mode="edit"
          initialData={updatedBotData}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('Updated Bot')).toBeInTheDocument();
      });
    });

    it('should submit updated form data', async () => {
      const user = userEvent.setup();

      render(
        <BotForm
          mode="edit"
          initialData={mockBotData}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('Existing Bot')).toBeInTheDocument();
      });

      // Update the bot name
      const nameInput = screen.getByDisplayValue('Existing Bot');
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Bot Name');

      // Submit the form
      await user.click(screen.getByText('Update Bot'));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Updated Bot Name',
            description: 'An existing bot',
            system_prompt: 'You are an existing assistant',
            llm_provider: 'anthropic',
            llm_model: 'claude-3-haiku',
            temperature: 0.5,
            max_tokens: 2000,
            is_public: true,
            allow_collaboration: false,
          })
        );
      });
    });
  });

  describe('Advanced Configuration', () => {
    it('should render all advanced parameters', async () => {
      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/Temperature/)).toBeInTheDocument();
      });

      expect(screen.getByLabelText(/Max Tokens/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Top P/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Frequency Penalty/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Presence Penalty/)).toBeInTheDocument();
    });

    it('should update parameter values with sliders', async () => {
      const user = userEvent.setup();

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/Temperature/)).toBeInTheDocument();
      });

      const temperatureSlider = screen.getByLabelText(/Temperature/);
      fireEvent.change(temperatureSlider, { target: { value: '1.2' } });

      expect(screen.getByText('Temperature (1.2)')).toBeInTheDocument();
    });

    it('should render embedding configuration', async () => {
      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Embedding Configuration')).toBeInTheDocument();
      });

      expect(screen.getByLabelText(/Embedding Provider/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Embedding Model/)).toBeInTheDocument();
    });

    it('should render collaboration settings', async () => {
      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Collaboration Settings')).toBeInTheDocument();
      });

      expect(screen.getByLabelText(/Allow collaboration on this bot/)).toBeInTheDocument();
    });

    it('should toggle collaboration setting', async () => {
      const user = userEvent.setup();

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/Allow collaboration on this bot/)).toBeInTheDocument();
      });

      const collaborationCheckbox = screen.getByLabelText(/Allow collaboration on this bot/);
      expect(collaborationCheckbox).toBeChecked(); // Default is true

      await user.click(collaborationCheckbox);
      expect(collaborationCheckbox).not.toBeChecked();
    });
  });

  describe('Loading States', () => {
    it('should show loading state while fetching provider settings', async () => {
      // Mock a delayed response
      mockBotService.getProviderSettings.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockProviderSettings), 100))
      );

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Should show loading skeleton
      expect(screen.getByText('LLM Configuration')).toBeInTheDocument();
      
      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByText('OpenAI')).toBeInTheDocument();
      }, { timeout: 200 });
    });

    it('should show submitting state', async () => {
      const user = userEvent.setup();
      
      // Mock a delayed submit
      mockOnSubmit.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      await user.type(screen.getByLabelText(/Bot Name/), 'Test Bot');
      await user.type(screen.getByLabelText(/Instructions for the AI/), 'You are helpful');

      const submitButton = screen.getByText('Create Bot');
      await user.click(submitButton);

      expect(screen.getByText('Saving...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('should handle provider settings loading error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockBotService.getProviderSettings.mockRejectedValue(new Error('Network error'));

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to load provider settings:', expect.any(Error));
      });

      consoleSpy.mockRestore();
    });

    it('should display validation errors', async () => {
      mockBotService.validateBotConfig.mockReturnValue({
        valid: false,
        errors: [
          'Bot name must be between 1 and 255 characters',
          'System prompt is required',
          'Temperature must be between 0 and 2',
        ],
      });

      render(
        <BotForm
          mode="create"
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Please fix the following errors:')).toBeInTheDocument();
        expect(screen.getByText('Bot name must be between 1 and 255 characters')).toBeInTheDocument();
        expect(screen.getByText('System prompt is required')).toBeInTheDocument();
        expect(screen.getByText('Temperature must be between 0 and 2')).toBeInTheDocument();
      });
    });
  });
});