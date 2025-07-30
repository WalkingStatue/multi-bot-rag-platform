/**
 * Unit tests for BotList component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BotList } from '../../components/bots/BotList';
import { botService } from '../../services/botService';
import { BotWithRole, BotListFilters } from '../../types/bot';

// Mock the bot service
vi.mock('../../services/botService');

const mockBotService = vi.mocked(botService);

describe('BotList', () => {
  const mockOnFiltersChange = vi.fn();
  const mockOnCreateBot = vi.fn();
  const mockOnEditBot = vi.fn();
  const mockOnDeleteBot = vi.fn();
  const mockOnTransferOwnership = vi.fn();

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
    {
      bot: {
        id: '3',
        name: 'Test Bot 3',
        description: 'Third test bot',
        system_prompt: 'You are a helpful assistant',
        owner_id: 'user3',
        llm_provider: 'gemini',
        llm_model: 'gemini-pro',
        temperature: 0.8,
        max_tokens: 1500,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
        is_public: false,
        allow_collaboration: false,
        created_at: '2023-01-03T00:00:00Z',
        updated_at: '2023-01-03T12:00:00Z',
      },
      role: 'viewer',
      granted_at: '2023-01-03T00:00:00Z',
    },
  ];

  const defaultFilters: BotListFilters = {};

  beforeEach(() => {
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
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render bot list with bots', () => {
      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      expect(screen.getByText('Test Bot 2')).toBeInTheDocument();
      expect(screen.getByText('Test Bot 3')).toBeInTheDocument();
      expect(screen.getByText('Create Bot')).toBeInTheDocument();
    });

    it('should render loading state', () => {
      render(
        <BotList
          bots={[]}
          isLoading={true}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      // Should show loading skeletons
      const skeletons = screen.getAllByRole('generic');
      expect(skeletons.some(el => el.classList.contains('animate-pulse'))).toBe(true);
    });

    it('should render empty state when no bots', () => {
      render(
        <BotList
          bots={[]}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      expect(screen.getByText('No Bots Found')).toBeInTheDocument();
      expect(screen.getByText('Get started by creating your first AI assistant.')).toBeInTheDocument();
      expect(screen.getByText('Create Your First Bot')).toBeInTheDocument();
    });

    it('should render filtered empty state', () => {
      const filters = { search: 'nonexistent' };
      
      render(
        <BotList
          bots={[]}
          isLoading={false}
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      expect(screen.getByText('No Bots Found')).toBeInTheDocument();
      expect(screen.getByText('No bots match your current filters. Try adjusting your search criteria.')).toBeInTheDocument();
    });
  });

  describe('Bot Information Display', () => {
    it('should display bot information correctly', () => {
      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      // Check bot names and descriptions
      expect(screen.getByText('Test Bot 1')).toBeInTheDocument();
      expect(screen.getByText('First test bot')).toBeInTheDocument();
      expect(screen.getByText('Test Bot 2')).toBeInTheDocument();
      expect(screen.getByText('Second test bot')).toBeInTheDocument();

      // Check role badges
      expect(screen.getByText('owner')).toBeInTheDocument();
      expect(screen.getByText('editor')).toBeInTheDocument();
      expect(screen.getByText('viewer')).toBeInTheDocument();

      // Check public badge
      expect(screen.getByText('Public')).toBeInTheDocument();

      // Check provider information
      expect(screen.getByText('OpenAI • gpt-3.5-turbo')).toBeInTheDocument();
      expect(screen.getByText('Anthropic • claude-3-haiku')).toBeInTheDocument();
      expect(screen.getByText('Google Gemini • gemini-pro')).toBeInTheDocument();
    });

    it('should display provider icons correctly', () => {
      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      // Provider icons should be displayed (emojis in this case)
      expect(screen.getByText('🤖')).toBeInTheDocument(); // OpenAI
      expect(screen.getByText('🧠')).toBeInTheDocument(); // Anthropic
      expect(screen.getByText('💎')).toBeInTheDocument(); // Gemini
    });

    it('should format dates correctly', () => {
      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      // Should display formatted update dates
      expect(screen.getByText(/Updated Jan 1, 2023/)).toBeInTheDocument();
      expect(screen.getByText(/Updated Jan 2, 2023/)).toBeInTheDocument();
      expect(screen.getByText(/Updated Jan 3, 2023/)).toBeInTheDocument();
    });
  });

  describe('Filtering', () => {
    it('should handle search input changes', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      const searchInput = screen.getByPlaceholderText('Search bots...');
      await user.type(searchInput, 'test query');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        search: 'test query',
      });
    });

    it('should handle role filter changes', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      const roleSelect = screen.getByDisplayValue('All Roles');
      await user.selectOptions(roleSelect, 'owner');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        role: 'owner',
      });
    });

    it('should handle provider filter changes', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      const providerSelect = screen.getByDisplayValue('All Providers');
      await user.selectOptions(providerSelect, 'openai');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        provider: 'openai',
      });
    });

    it('should handle sort changes', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      const sortSelect = screen.getByDisplayValue('Recently Updated');
      await user.selectOptions(sortSelect, 'name-asc');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        sort_by: 'name',
        sort_order: 'asc',
      });
    });
  });

  describe('Actions', () => {
    it('should handle create bot action', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      await user.click(screen.getByText('Create Bot'));

      expect(mockOnCreateBot).toHaveBeenCalled();
    });

    it('should handle edit bot action for admin/owner', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]); // Click first edit button (owner)

      expect(mockOnEditBot).toHaveBeenCalledWith(mockBots[0]);
    });

    it('should not show edit button for viewers', () => {
      render(
        <BotList
          bots={[mockBots[2]]} // Only viewer bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      expect(screen.queryByText('Edit')).not.toBeInTheDocument();
    });

    it('should handle transfer ownership action for owners', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={[mockBots[0]]} // Only owner bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      await user.click(screen.getByText('Transfer'));

      expect(mockOnTransferOwnership).toHaveBeenCalledWith(mockBots[0]);
    });

    it('should not show transfer button for non-owners', () => {
      render(
        <BotList
          bots={[mockBots[1]]} // Only editor bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      expect(screen.queryByText('Transfer')).not.toBeInTheDocument();
    });
  });

  describe('Delete Functionality', () => {
    it('should show delete confirmation modal when delete is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={[mockBots[0]]} // Only owner bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      await user.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(screen.getByText('Delete Bot')).toBeInTheDocument();
        expect(mockBotService.getBotDeleteInfo).toHaveBeenCalledWith('1');
      });
    });

    it('should display cascade information in delete modal', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={[mockBots[0]]} // Only owner bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      await user.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(screen.getByText('Are you sure you want to delete Test Bot 1?')).toBeInTheDocument();
        expect(screen.getByText('• 5 conversation sessions')).toBeInTheDocument();
        expect(screen.getByText('• 25 messages')).toBeInTheDocument();
        expect(screen.getByText('• 3 documents')).toBeInTheDocument();
        expect(screen.getByText('• 2 collaborator permissions')).toBeInTheDocument();
      });
    });

    it('should handle delete confirmation', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={[mockBots[0]]} // Only owner bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      await user.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(screen.getByText('Delete Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Delete Bot'));

      expect(mockOnDeleteBot).toHaveBeenCalledWith('1');
    });

    it('should handle delete cancellation', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={[mockBots[0]]} // Only owner bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      await user.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(screen.getByText('Delete Bot')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Cancel'));

      expect(screen.queryByText('Delete Bot')).not.toBeInTheDocument();
      expect(mockOnDeleteBot).not.toHaveBeenCalled();
    });

    it('should not show delete button for non-owners', () => {
      render(
        <BotList
          bots={[mockBots[1]]} // Only editor bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      expect(screen.queryByText('Delete')).not.toBeInTheDocument();
    });

    it('should handle delete info loading error', async () => {
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockBotService.getBotDeleteInfo.mockRejectedValue(new Error('Network error'));

      render(
        <BotList
          bots={[mockBots[0]]} // Only owner bot
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      await user.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to load delete info:', expect.any(Error));
        // Should still show delete modal with fallback data
        expect(screen.getByText('Delete Bot')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      // Check for proper form controls
      expect(screen.getByLabelText(/Search bots/)).toBeInTheDocument();
      expect(screen.getByRole('combobox', { name: /All Roles/ })).toBeInTheDocument();
      expect(screen.getByRole('combobox', { name: /All Providers/ })).toBeInTheDocument();
      
      // Check for buttons
      expect(screen.getByRole('button', { name: /Create Bot/ })).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();

      render(
        <BotList
          bots={mockBots}
          isLoading={false}
          filters={defaultFilters}
          onFiltersChange={mockOnFiltersChange}
          onCreateBot={mockOnCreateBot}
          onEditBot={mockOnEditBot}
          onDeleteBot={mockOnDeleteBot}
          onTransferOwnership={mockOnTransferOwnership}
        />
      );

      const searchInput = screen.getByPlaceholderText('Search bots...');
      
      // Should be able to focus and type in search input
      await user.click(searchInput);
      expect(searchInput).toHaveFocus();
      
      await user.type(searchInput, 'test');
      expect(searchInput).toHaveValue('test');
    });
  });
});