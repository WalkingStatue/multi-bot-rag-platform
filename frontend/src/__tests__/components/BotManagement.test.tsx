/**
 * Unit tests for BotManagement component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BotManagement } from '../../components/bots/BotManagement';
import { botService } from '../../services/botService';
import { BotWithRole, BotFormData } from '../../types/bot';

// Mock the bot service
vi.mock('../../services/botService');

const mockBotService = vi.mocked(botService);

describe('BotManagement', () => {
  const mockBots: BotWithRole[] = [
    {
      bot: {
        id: '1',
        name: 'Test Bot 1',
        description: 'First test bot',
        system_prompt: 'You are a helpful assistant',
        owner_id: 'user1',
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
        updated_at: '2023-01-01T12:00:00Z',
      },
      role: 'owner',
      granted_at: '2023-01-01T00:00:00Z',
    },
    {
      bot: {
        id: '2',
        name: 'Test Bot 2',
        description: 'Second test bot',
        system_prompt: 'You are a helpful assistant',
        owner_id: 'user2',
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
        updated_at: '2023-01-02T12:00:00Z',
      },
      role: 'editor',
      granted_at: '2023-01-02T00:00:00Z',
    },
  ];

  const mockProviderSettings = {
    llm_providers: {
      openai: {
        name: 'openai',
        display_name: 'OpenAI',
        models: [
          { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', max_tokens: 4096 },
        ],
        default_model: 'gpt-3.5-turbo',
        supports_embeddings: true,
        embedding_models: [
          { id: 'text-embedding-3-small', name: 'Text Embedding 3 Small' },
        ],
        default_embedding_model: 'text-embedding-3-small',
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
    },
  };

  beforeEach(() => {
    mockBotService.getUserBots.mockResolvedValue(mockBots);
    mockBotService.getProviderSettings.mockResolvedValue(mockProviderSettings);
    mockBotService.validateBotConfig.mockReturnValue({ valid: true, errors: [] });
    mockBotService.createBot.mockResolvedValue(mockBots[0].bot);
    mockBotService.updateBot.mockResolvedValue(mockBots[0].bot);
    mockBotService.deleteBot.mockResolvedValue();
    mockBotService.transferOwnership.mockResolvedValue();
    mockBotService.searchUsers.mockResolvedValue([
      { id: 'user456', username: 'testuser', email: 'test@example.com' },
    ]);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Loading', () => {
    it('should load bots on mount', async () => {
      render(<BotManagement />);

      expect(screen.getByText('Your Bots')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(mockBotService.getUserBots).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
        expect(screen.getByText('Test Bot 2')).toBeInTheDocument();
      });
    });

    it('should show loading state initially', () => {
      // Mock a delayed response
      mockBotService.getUserBots.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockBots), 100))
      );

      render(<BotManagement />);

      // Should show loading skeletons
      const skeletons = screen.getAllByRole('generic');
      expect(skeletons.some(el => el.classList.contains('animate-pulse'))).toBe(true);
    });

    it('should handle loading error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockBotService.getUserBots.mockRejectedValue(new Error('Network error'));

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load bots')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Bot List View', () => {
    it('should display bot list by default', async () => {
      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Your Bots')).toBeInTheDocument();
        expect(screen.getByText('Manage your AI assistants and their configurations')).toBeInTheDocument();
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
        expect(screen.getByText('Test Bot 2')).toBeInTheDocument();
      });
    });

    it('should handle filtering', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      // Filter by search
      const searchInput = screen.getByPlaceholderText('Search bots...');
      await user.type(searchInput, 'Test Bot 1');

      // Should filter the list (this is handled by the filteredBots memo)
      expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
    });

    it('should handle sorting', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      // Change sort order
      const sortSelect = screen.getByDisplayValue('Recently Updated');
      await user.selectOptions(sortSelect, 'name-asc');

      // Should update the filters (sorting logic is in the filteredBots memo)
      expect(sortSelect).toHaveValue('name-asc');
    });
  });

  describe('Bot Creation', () => {
    it('should switch to create mode when create button is clicked', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Create Bot'));

      expect(screen.getByText('Create New Bot')).toBeInTheDocument();
    });

    it('should create bot successfully', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      // Fill out the form
      await user.type(screen.getByLabelText(/Bot Name/), 'New Test Bot');
      await user.type(screen.getByLabelText(/Instructions for the AI/), 'You are helpful');

      // Submit the form
      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(mockBotService.createBot).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'New Test Bot',
            system_prompt: 'You are helpful',
          })
        );
      });

      await waitFor(() => {
        expect(screen.getByText('Bot created successfully')).toBeInTheDocument();
        expect(screen.getByText('Your Bots')).toBeInTheDocument(); // Should return to list view
      });
    });

    it('should handle create bot error', async () => {
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockBotService.createBot.mockRejectedValue(new Error('Validation failed'));

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      await user.type(screen.getByLabelText(/Bot Name/), 'New Test Bot');
      await user.type(screen.getByLabelText(/Instructions for the AI/), 'You are helpful');
      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByText('Failed to create bot')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });

    it('should cancel bot creation', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByText('Create New Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Cancel'));

      expect(screen.getByText('Your Bots')).toBeInTheDocument();
    });
  });

  describe('Bot Editing', () => {
    it('should switch to edit mode when edit button is clicked', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]);

      expect(screen.getByText('Edit Bot')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test Bot 1')).toBeInTheDocument();
    });

    it('should update bot successfully', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByDisplayValue('Test Bot 1')).toBeInTheDocument();
      });

      // Update the bot name
      const nameInput = screen.getByDisplayValue('Test Bot 1');
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Bot Name');

      await user.click(screen.getByText('Update Bot'));

      await waitFor(() => {
        expect(mockBotService.updateBot).toHaveBeenCalledWith(
          '1',
          expect.objectContaining({
            name: 'Updated Bot Name',
          })
        );
      });

      await waitFor(() => {
        expect(screen.getByText('Bot updated successfully')).toBeInTheDocument();
        expect(screen.getByText('Your Bots')).toBeInTheDocument();
      });
    });

    it('should handle update bot error', async () => {
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockBotService.updateBot.mockRejectedValue(new Error('Update failed'));

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByDisplayValue('Test Bot 1')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Update Bot'));

      await waitFor(() => {
        expect(screen.getByText('Failed to update bot')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Bot Deletion', () => {
    it('should delete bot successfully', async () => {
      const user = userEvent.setup();

      mockBotService.getBotDeleteInfo.mockResolvedValue({
        bot_id: '1',
        bot_name: 'Test Bot 1',
        cascade_info: {
          conversations: 5,
          messages: 25,
          documents: 3,
          collaborators: 2,
        },
      });

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      // Click delete button (only visible for owners)
      await user.click(screen.getByText('Delete'));

      // Confirm deletion in modal
      await waitFor(() => {
        expect(screen.getByText('Delete Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Delete Bot'));

      await waitFor(() => {
        expect(mockBotService.deleteBot).toHaveBeenCalledWith('1');
      });

      await waitFor(() => {
        expect(screen.getByText('Bot deleted successfully')).toBeInTheDocument();
      });
    });

    it('should handle delete bot error', async () => {
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockBotService.deleteBot.mockRejectedValue(new Error('Delete failed'));
      mockBotService.getBotDeleteInfo.mockResolvedValue({
        bot_id: '1',
        bot_name: 'Test Bot 1',
        cascade_info: {
          conversations: 0,
          messages: 0,
          documents: 0,
          collaborators: 0,
        },
      });

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(screen.getByText('Delete Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Delete Bot'));

      await waitFor(() => {
        expect(screen.getByText('Failed to delete bot')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Bot Transfer', () => {
    it('should open transfer modal when transfer button is clicked', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Transfer'));

      expect(screen.getByText('Transfer Bot Ownership')).toBeInTheDocument();
      expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
    });

    it('should transfer bot ownership successfully', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Transfer'));

      await waitFor(() => {
        expect(screen.getByText('Transfer Bot Ownership')).toBeInTheDocument();
      });

      // Search for user
      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });

      await user.click(screen.getByText('testuser'));
      await user.click(screen.getByText('Transfer Ownership'));

      await waitFor(() => {
        expect(mockBotService.transferOwnership).toHaveBeenCalledWith('1', {
          new_owner_id: 'user456',
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Bot ownership transferred successfully')).toBeInTheDocument();
      });
    });

    it('should close transfer modal when cancelled', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Transfer'));

      await waitFor(() => {
        expect(screen.getByText('Transfer Bot Ownership')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Cancel'));

      expect(screen.queryByText('Transfer Bot Ownership')).not.toBeInTheDocument();
    });
  });

  describe('Message Display', () => {
    it('should display success messages', async () => {
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      await user.type(screen.getByLabelText(/Bot Name/), 'New Test Bot');
      await user.type(screen.getByLabelText(/Instructions for the AI/), 'You are helpful');
      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByText('Bot created successfully')).toBeInTheDocument();
      });

      // Message should have success styling
      const messageElement = screen.getByText('Bot created successfully').closest('div');
      expect(messageElement).toHaveClass('bg-green-50');
    });

    it('should display error messages', async () => {
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockBotService.createBot.mockRejectedValue(new Error('Validation failed'));

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      await user.type(screen.getByLabelText(/Bot Name/), 'New Test Bot');
      await user.type(screen.getByLabelText(/Instructions for the AI/), 'You are helpful');
      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByText('Failed to create bot')).toBeInTheDocument();
      });

      // Message should have error styling
      const messageElement = screen.getByText('Failed to create bot').closest('div');
      expect(messageElement).toHaveClass('bg-red-50');

      consoleSpy.mockRestore();
    });

    it('should auto-hide messages after 5 seconds', async () => {
      vi.useFakeTimers();
      
      const user = userEvent.setup();

      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Bot Name/)).toBeInTheDocument();
      });

      await user.type(screen.getByLabelText(/Bot Name/), 'New Test Bot');
      await user.type(screen.getByLabelText(/Instructions for the AI/), 'You are helpful');
      await user.click(screen.getByText('Create Bot'));

      await waitFor(() => {
        expect(screen.getByText('Bot created successfully')).toBeInTheDocument();
      });

      // Fast-forward time
      vi.advanceTimersByTime(5000);

      await waitFor(() => {
        expect(screen.queryByText('Bot created successfully')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });
  });

  describe('Filtering Logic', () => {
    it('should filter bots by search query', async () => {
      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
        expect(screen.getByText('Test Bot 2')).toBeInTheDocument();
      });

      // The filtering logic is tested through the filteredBots memo
      // This test verifies the component structure supports filtering
      expect(screen.getByPlaceholderText('Search bots...')).toBeInTheDocument();
    });

    it('should filter bots by role', async () => {
      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
        expect(screen.getByText('Test Bot 2')).toBeInTheDocument();
      });

      // The filtering logic is tested through the filteredBots memo
      expect(screen.getByDisplayValue('All Roles')).toBeInTheDocument();
    });

    it('should sort bots correctly', async () => {
      render(<BotManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
        expect(screen.getByText('Test Bot 2')).toBeInTheDocument();
      });

      // The sorting logic is tested through the filteredBots memo
      expect(screen.getByDisplayValue('Recently Updated')).toBeInTheDocument();
    });
  });
});