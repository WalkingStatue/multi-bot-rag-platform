/**
 * Unit tests for LoginForm component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from '../../components/auth/LoginForm';
import { useAuth } from '../../hooks/useAuth';

// Mock the useAuth hook
vi.mock('../../hooks/useAuth');

const mockUseAuth = vi.mocked(useAuth);

const renderLoginForm = (props = {}) => {
  return render(
    <BrowserRouter>
      <LoginForm {...props} />
    </BrowserRouter>
  );
};

describe('LoginForm', () => {
  const mockLogin = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: mockLogin,
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });
  });

  it('renders login form correctly', () => {
    renderLoginForm();

    expect(screen.getByText('Sign in to your account')).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText('create a new account')).toBeInTheDocument();
    expect(screen.getByText('Forgot your password?')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    expect(screen.getByText('This field is required')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('validates username minimum length', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    const usernameInput = screen.getByLabelText('Username');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'ab');
    await user.click(submitButton);

    expect(screen.getByText('Must be at least 3 characters')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    renderLoginForm({ onSuccess });

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    expect(mockLogin).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password123',
    });
  });

  it('calls onSuccess callback after successful login', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    mockLogin.mockResolvedValueOnce(undefined);
    
    renderLoginForm({ onSuccess });

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('displays error message', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: 'Invalid credentials',
      login: mockLogin,
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });

    renderLoginForm();

    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      login: mockLogin,
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });

    renderLoginForm();

    expect(screen.getByText('Signing in...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
  });

  it('clears error when user starts typing', async () => {
    const user = userEvent.setup();
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: 'Invalid credentials',
      login: mockLogin,
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: mockClearError,
    });

    renderLoginForm();

    const usernameInput = screen.getByLabelText('Username');
    await user.type(usernameInput, 'a');

    expect(mockClearError).toHaveBeenCalled();
  });

  it('clears field errors when user starts typing', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    // First trigger validation error
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    expect(screen.getByText('This field is required')).toBeInTheDocument();

    // Then start typing to clear error
    const usernameInput = screen.getByLabelText('Username');
    await user.type(usernameInput, 'a');

    expect(screen.queryByText('This field is required')).not.toBeInTheDocument();
  });
});