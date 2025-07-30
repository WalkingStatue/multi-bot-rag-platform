/**
 * Unit tests for APIKeyList component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { APIKeyList } from '../../components/apikeys/APIKeyList';
import { APIKeyResponse, ProviderInfo } from '../../types/api';

describe('APIKeyList', () => {
  const mockAPIKeys: APIKeyResponse[] = [
    {
      id: '1',
      provider: 'openai',
      is_active: true,
      created_at: '2023-01-01T10:00:00Z',
      updated_at: '2023-01-01T10:00:00Z',
    },
    {
      id: '2',
      provider: 'anthropic',
      is_active: false,
      created_at: '2023-01-02T15:30:00Z',
      updated_at: '2023-01-03T09:15:00Z',
    },
    {
      id: '3',
      provider: 'gemini',
      is_active: true,
      created_at: '2023-01-03T08:45:00Z',
      updated_at: '2023-01-03T08:45:00Z',
    },
  ];

  const mockProviders: Record<string, ProviderInfo> = {
    openai: {
      name: 'openai',
      models: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4-vision', 'dall-e-3', 'whisper-1'],
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

  const mockOnEdit = vi.fn();
  const mockOnDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should show loading skeleton when isLoading is true', () => {
      render(
        <APIKeyList
          apiKeys={[]}
          providers={{}}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={true}
        />
      );

      // Should show loading skeleton
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no API keys exist', () => {
      render(
        <APIKeyList
          apiKeys={[]}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      expect(screen.getByText('No API Keys')).toBeInTheDocument();
      expect(screen.getByText('Add your first API key to start using the platform with your preferred LLM provider.')).toBeInTheDocument();
      expect(screen.getByText('🔑')).toBeInTheDocument();
    });
  });

  describe('API Key Display', () => {
    it('should display all API keys with correct information', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      expect(screen.getByText('Your API Keys')).toBeInTheDocument();
      
      // Check provider display names
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('Google Gemini')).toBeInTheDocument();

      // Check status badges
      const activeStatuses = screen.getAllByText('Active');
      const inactiveStatuses = screen.getAllByText('Inactive');
      expect(activeStatuses).toHaveLength(2); // OpenAI and Gemini
      expect(inactiveStatuses).toHaveLength(1); // Anthropic
    });

    it('should show correct provider icons', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      // Check for provider icons (emojis)
      expect(screen.getByText('🤖')).toBeInTheDocument(); // OpenAI
      expect(screen.getByText('🧠')).toBeInTheDocument(); // Anthropic
      expect(screen.getByText('💎')).toBeInTheDocument(); // Gemini
    });

    it('should format dates correctly', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      // Check for formatted dates
      expect(screen.getByText(/Added Jan 1, 2023/)).toBeInTheDocument();
      expect(screen.getByText(/Added Jan 2, 2023/)).toBeInTheDocument();
      expect(screen.getByText(/Updated Jan 3, 2023/)).toBeInTheDocument();
    });

    it('should show updated date only when different from created date', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      // OpenAI and Gemini have same created/updated dates, so no "Updated" text
      const openaiCard = screen.getByText('OpenAI').closest('.border');
      const geminiCard = screen.getByText('Google Gemini').closest('.border');
      
      expect(openaiCard).not.toHaveTextContent('Updated');
      expect(geminiCard).not.toHaveTextContent('Updated');

      // Anthropic has different dates, so should show "Updated"
      const anthropicCard = screen.getByText('Anthropic').closest('.border');
      expect(anthropicCard).toHaveTextContent('Updated');
    });
  });

  describe('Available Models Display', () => {
    it('should show available models for each provider', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      // Check for model displays
      expect(screen.getByText('gpt-3.5-turbo')).toBeInTheDocument();
      expect(screen.getByText('gpt-4')).toBeInTheDocument();
      expect(screen.getByText('claude-3-haiku')).toBeInTheDocument();
      expect(screen.getByText('gemini-pro')).toBeInTheDocument();
    });

    it('should show limited models with "more" indicator when there are many models', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      // OpenAI has 6 models, should show first 5 + "more" indicator
      expect(screen.getByText('+1 more')).toBeInTheDocument();
    });

    it('should not show models section when provider info is missing', () => {
      const apiKeysWithUnknownProvider: APIKeyResponse[] = [
        {
          id: '1',
          provider: 'unknown-provider',
          is_active: true,
          created_at: '2023-01-01T10:00:00Z',
          updated_at: '2023-01-01T10:00:00Z',
        },
      ];

      render(
        <APIKeyList
          apiKeys={apiKeysWithUnknownProvider}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      // Should not show "Available Models" section
      expect(screen.queryByText('Available Models:')).not.toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('should show Edit and Delete buttons for each API key', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const editButtons = screen.getAllByText('Edit');
      const deleteButtons = screen.getAllByText('Delete');

      expect(editButtons).toHaveLength(3);
      expect(deleteButtons).toHaveLength(3);
    });

    it('should call onEdit with correct provider when Edit button is clicked', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const editButtons = screen.getAllByText('Edit');
      fireEvent.click(editButtons[0]); // Click first edit button (OpenAI)

      expect(mockOnEdit).toHaveBeenCalledWith('openai');
    });

    it('should show confirmation state on first delete click', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]); // Click first delete button

      expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('should call onDelete when Confirm Delete is clicked', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]); // First click shows confirmation

      const confirmButton = screen.getByText('Confirm Delete');
      fireEvent.click(confirmButton); // Second click confirms deletion

      expect(mockOnDelete).toHaveBeenCalledWith('openai');
    });

    it('should cancel delete confirmation when Cancel is clicked', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]); // Show confirmation

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton); // Cancel confirmation

      // Should return to normal state
      expect(screen.queryByText('Confirm Delete')).not.toBeInTheDocument();
      expect(screen.getAllByText('Delete')).toHaveLength(3);
    });

    it('should handle multiple delete confirmations independently', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const deleteButtons = screen.getAllByText('Delete');
      
      // Click first delete button
      fireEvent.click(deleteButtons[0]);
      expect(screen.getByText('Confirm Delete')).toBeInTheDocument();

      // Click second delete button - should cancel first and show second
      fireEvent.click(deleteButtons[1]);
      
      // Should still have one confirmation button, but for the second item
      expect(screen.getAllByText('Confirm Delete')).toHaveLength(1);
    });
  });

  describe('Status Display', () => {
    it('should show correct status styling for active and inactive keys', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const activeStatuses = screen.getAllByText('Active');
      const inactiveStatuses = screen.getAllByText('Inactive');

      // Check active status styling (green)
      activeStatuses.forEach(status => {
        expect(status).toHaveClass('bg-green-100', 'text-green-800');
      });

      // Check inactive status styling (red)
      inactiveStatuses.forEach(status => {
        expect(status).toHaveClass('bg-red-100', 'text-red-800');
      });
    });
  });

  describe('Provider Display Names', () => {
    it('should handle unknown providers gracefully', () => {
      const apiKeysWithUnknownProvider: APIKeyResponse[] = [
        {
          id: '1',
          provider: 'unknown-provider',
          is_active: true,
          created_at: '2023-01-01T10:00:00Z',
          updated_at: '2023-01-01T10:00:00Z',
        },
      ];

      render(
        <APIKeyList
          apiKeys={apiKeysWithUnknownProvider}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      // Should show the provider name as-is when no display name mapping exists
      expect(screen.getByText('unknown-provider')).toBeInTheDocument();
      // Should show default icon
      expect(screen.getByText('🔑')).toBeInTheDocument();
    });

    it('should show correct display names for all supported providers', () => {
      const allProviderKeys: APIKeyResponse[] = [
        { id: '1', provider: 'openai', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
        { id: '2', provider: 'anthropic', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
        { id: '3', provider: 'openrouter', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
        { id: '4', provider: 'gemini', is_active: true, created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
      ];

      const allProviders = {
        ...mockProviders,
        openrouter: { name: 'openrouter', models: ['openrouter/auto'] },
      };

      render(
        <APIKeyList
          apiKeys={allProviderKeys}
          providers={allProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('OpenRouter')).toBeInTheDocument();
      expect(screen.getByText('Google Gemini')).toBeInTheDocument();
    });
  });

  describe('Hover Effects', () => {
    it('should apply hover styles to API key cards', () => {
      render(
        <APIKeyList
          apiKeys={mockAPIKeys}
          providers={mockProviders}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          isLoading={false}
        />
      );

      const cards = document.querySelectorAll('.border.border-gray-200.rounded-lg');
      cards.forEach(card => {
        expect(card).toHaveClass('hover:shadow-sm', 'transition-shadow');
      });
    });
  });
});