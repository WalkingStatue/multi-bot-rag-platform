/**
 * Unit tests for BotTransferModal component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BotTransferModal } from '../../components/bots/BotTransferModal';
import { botService } from '../../services/botService';
import { BotWithRole } from '../../types/bot';

// Mock the bot service
vi.mock('../../services/botService');

const mockBotService = vi.mocked(botService);

describe('BotTransferModal', () => {
  const mockOnClose = vi.fn();
  const mockOnTransfer = vi.fn();

  const mockBot: BotWithRole = {
    bot: {
      id: '123',
      name: 'Test Bot',
      description: 'A test bot for transfer',
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
  };

  const mockUsers = [
    { id: 'user456', username: 'testuser', email: 'test@example.com' },
    { id: 'user789', username: 'anotheruser', email: 'another@example.com' },
  ];

  beforeEach(() => {
    mockBotService.searchUsers.mockResolvedValue(mockUsers);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render when open', () => {
      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      expect(screen.getByText('Transfer Bot Ownership')).toBeInTheDocument();
      expect(screen.getByText('Test Bot')).toBeInTheDocument();
      expect(screen.getByText('A test bot for transfer')).toBeInTheDocument();
    });

    it('should not render when closed', () => {
      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={false}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      expect(screen.queryByText('Transfer Bot Ownership')).not.toBeInTheDocument();
    });

    it('should display warning message', () => {
      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      expect(screen.getByText('Important: This action cannot be undone')).toBeInTheDocument();
      expect(screen.getByText(/Once you transfer ownership, you will lose all owner privileges/)).toBeInTheDocument();
    });

    it('should display bot information', () => {
      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      expect(screen.getByText('Test Bot')).toBeInTheDocument();
      expect(screen.getByText('A test bot for transfer')).toBeInTheDocument();
    });

    it('should handle bot without description', () => {
      const botWithoutDescription = {
        ...mockBot,
        bot: { ...mockBot.bot, description: undefined },
      };

      render(
        <BotTransferModal
          bot={botWithoutDescription}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      expect(screen.getByText('No description')).toBeInTheDocument();
    });
  });

  describe('User Search', () => {
    it('should search users when typing', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(mockBotService.searchUsers).toHaveBeenCalledWith('test');
      });
    });

    it('should debounce search requests', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      
      // Type multiple characters quickly
      await user.type(searchInput, 'test');

      // Should only make one API call after debounce
      await waitFor(() => {
        expect(mockBotService.searchUsers).toHaveBeenCalledTimes(1);
      });
    });

    it('should not search for queries less than 2 characters', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'a');

      // Should not make API call for single character
      expect(mockBotService.searchUsers).not.toHaveBeenCalled();
    });

    it('should display search results', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
        expect(screen.getByText('test@example.com')).toBeInTheDocument();
        expect(screen.getByText('anotheruser')).toBeInTheDocument();
        expect(screen.getByText('another@example.com')).toBeInTheDocument();
      });
    });

    it('should show loading indicator while searching', async () => {
      const user = userEvent.setup();
      
      // Mock a delayed response
      mockBotService.searchUsers.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockUsers), 100))
      );

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      // Should show loading spinner
      expect(screen.getByRole('generic', { hidden: true })).toHaveClass('animate-spin');
    });

    it('should handle search errors', async () => {
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockBotService.searchUsers.mockRejectedValue(new Error('Network error'));

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('Failed to search users. Please try again.')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });

    it('should show no results message', async () => {
      const user = userEvent.setup();
      
      mockBotService.searchUsers.mockResolvedValue([]);

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText('No users found matching "nonexistent"')).toBeInTheDocument();
      });
    });
  });

  describe('User Selection', () => {
    it('should select user when clicked', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });

      await user.click(screen.getByText('testuser'));

      // Should show selected user
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
      
      // Should show selected user card
      const selectedUserCards = screen.getAllByText('testuser');
      expect(selectedUserCards.length).toBeGreaterThan(1); // One in input, one in selected card
    });

    it('should clear selection when X is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });

      await user.click(screen.getByText('testuser'));

      // Should show selected user
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();

      // Click the X button to clear selection
      const clearButtons = screen.getAllByRole('button');
      const clearButton = clearButtons.find(btn => 
        btn.querySelector('svg path[d*="M6 18L18 6M6 6l12 12"]')
      );
      
      if (clearButton) {
        await user.click(clearButton);
      }

      // Should clear the input
      expect(screen.getByPlaceholderText('Enter username or email...')).toHaveValue('');
    });

    it('should enable transfer button when user is selected', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const transferButton = screen.getByText('Transfer Ownership');
      expect(transferButton).toBeDisabled();

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });

      await user.click(screen.getByText('testuser'));

      expect(transferButton).toBeEnabled();
    });
  });

  describe('Transfer Action', () => {
    it('should call onTransfer when transfer button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });

      await user.click(screen.getByText('testuser'));
      await user.click(screen.getByText('Transfer Ownership'));

      expect(mockOnTransfer).toHaveBeenCalledWith('123', {
        new_owner_id: 'user456',
      });
    });

    it('should show transferring state', async () => {
      const user = userEvent.setup();
      
      // Mock a delayed transfer
      mockOnTransfer.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });

      await user.click(screen.getByText('testuser'));
      
      const transferButton = screen.getByText('Transfer Ownership');
      await user.click(transferButton);

      expect(screen.getByText('Transferring...')).toBeInTheDocument();
      expect(transferButton).toBeDisabled();
      expect(screen.getByText('Cancel')).toBeDisabled();
    });

    it('should handle transfer errors', async () => {
      const user = userEvent.setup();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockOnTransfer.mockRejectedValue(new Error('Transfer failed'));

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });

      await user.click(screen.getByText('testuser'));
      await user.click(screen.getByText('Transfer Ownership'));

      await waitFor(() => {
        expect(screen.getByText('Failed to transfer ownership. Please try again.')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Modal Controls', () => {
    it('should close modal when close button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should close modal when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      await user.click(screen.getByText('Cancel'));

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should reset state when modal opens', () => {
      const { rerender } = render(
        <BotTransferModal
          bot={mockBot}
          isOpen={false}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      rerender(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      // Should have empty search input
      expect(screen.getByPlaceholderText('Enter username or email...')).toHaveValue('');
      
      // Transfer button should be disabled
      expect(screen.getByText('Transfer Ownership')).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      expect(screen.getByRole('dialog', { hidden: true })).toBeInTheDocument();
      expect(screen.getByLabelText('Search for new owner')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Transfer Ownership/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Cancel/ })).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      
      // Should be able to focus search input
      await user.click(searchInput);
      expect(searchInput).toHaveFocus();
      
      // Should be able to tab to buttons
      await user.tab();
      expect(screen.getByText('Cancel')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByText('Transfer Ownership')).toHaveFocus();
    });

    it('should trap focus within modal', async () => {
      const user = userEvent.setup();

      render(
        <BotTransferModal
          bot={mockBot}
          isOpen={true}
          onClose={mockOnClose}
          onTransfer={mockOnTransfer}
        />
      );

      // Focus should start within the modal
      const searchInput = screen.getByPlaceholderText('Enter username or email...');
      await user.click(searchInput);
      
      // Tab through all focusable elements
      await user.tab(); // Cancel button
      await user.tab(); // Transfer button
      await user.tab(); // Should wrap back to close button or search input
      
      // Focus should remain within modal
      const focusedElement = document.activeElement;
      const modal = screen.getByRole('dialog', { hidden: true });
      expect(modal).toContainElement(focusedElement as HTMLElement);
    });
  });
});