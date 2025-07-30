/**
 * Unit tests for UserProfile component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserProfile } from '../../components/auth/UserProfile';
import { useAuth } from '../../hooks/useAuth';

// Mock the useAuth hook
vi.mock('../../hooks/useAuth');

const mockUseAuth = vi.mocked(useAuth);

const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  avatar_url: null,
  is_active: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-02T00:00:00Z',
};

describe('UserProfile', () => {
  const mockUpdateProfile = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: mockUpdateProfile,
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });
  });

  it('renders user profile form correctly', () => {
    render(<UserProfile />);

    expect(screen.getByText('Profile Settings')).toBeInTheDocument();
    expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    expect(screen.getByText('Account created:')).toBeInTheDocument();
    expect(screen.getByText('Last updated:')).toBeInTheDocument();
  });

  it('shows loading skeleton when user is not loaded', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: true,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: mockUpdateProfile,
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });

    render(<UserProfile />);

    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument(); // Loading skeleton
  });

  it('validates form fields', async () => {
    const user = userEvent.setup();
    render(<UserProfile />);

    const usernameInput = screen.getByDisplayValue('testuser');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    // Clear username to trigger validation
    await user.clear(usernameInput);
    await user.click(saveButton);

    expect(screen.getByText('This field is required')).toBeInTheDocument();
    expect(mockUpdateProfile).not.toHaveBeenCalled();
  });

  it('validates email format', async () => {
    const user = userEvent.setup();
    render(<UserProfile />);

    const emailInput = screen.getByDisplayValue('test@example.com');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    await user.clear(emailInput);
    await user.type(emailInput, 'invalid-email');
    await user.click(saveButton);

    expect(screen.getByText('Invalid format')).toBeInTheDocument();
    expect(mockUpdateProfile).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    render(<UserProfile />);

    const usernameInput = screen.getByDisplayValue('testuser');
    const emailInput = screen.getByDisplayValue('test@example.com');
    const fullNameInput = screen.getByDisplayValue('Test User');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    await user.clear(usernameInput);
    await user.type(usernameInput, 'newusername');
    await user.clear(emailInput);
    await user.type(emailInput, 'newemail@example.com');
    await user.clear(fullNameInput);
    await user.type(fullNameInput, 'New Full Name');
    await user.click(saveButton);

    expect(mockUpdateProfile).toHaveBeenCalledWith({
      username: 'newusername',
      email: 'newemail@example.com',
      full_name: 'New Full Name',
    });
  });

  it('handles empty full name correctly', async () => {
    const user = userEvent.setup();
    render(<UserProfile />);

    const fullNameInput = screen.getByDisplayValue('Test User');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    await user.clear(fullNameInput);
    await user.click(saveButton);

    expect(mockUpdateProfile).toHaveBeenCalledWith({
      username: 'testuser',
      email: 'test@example.com',
      full_name: undefined,
    });
  });

  it('shows success message after successful update', async () => {
    const user = userEvent.setup();
    mockUpdateProfile.mockResolvedValueOnce(undefined);
    
    render(<UserProfile />);

    const usernameInput = screen.getByDisplayValue('testuser');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    await user.clear(usernameInput);
    await user.type(usernameInput, 'newusername');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Profile updated successfully!')).toBeInTheDocument();
    });
  });

  it('displays error message', () => {
    mockUseAuth.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
      error: 'Update failed',
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: mockUpdateProfile,
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });

    render(<UserProfile />);

    expect(screen.getByText('Update failed')).toBeInTheDocument();
  });

  it('shows loading state during update', () => {
    mockUseAuth.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      isLoading: true,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: mockUpdateProfile,
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });

    render(<UserProfile />);

    expect(screen.getByText('Saving...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled();
  });

  it('disables save button when no changes are made', () => {
    render(<UserProfile />);

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    expect(saveButton).toBeDisabled();
  });

  it('enables save button when changes are made', async () => {
    const user = userEvent.setup();
    render(<UserProfile />);

    const usernameInput = screen.getByDisplayValue('testuser');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    await user.type(usernameInput, '1');

    expect(saveButton).toBeEnabled();
  });

  it('resets form to original values', async () => {
    const user = userEvent.setup();
    render(<UserProfile />);

    const usernameInput = screen.getByDisplayValue('testuser');
    const resetButton = screen.getByRole('button', { name: /reset/i });

    // Make changes
    await user.clear(usernameInput);
    await user.type(usernameInput, 'changedusername');

    // Reset form
    await user.click(resetButton);

    expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
  });
});