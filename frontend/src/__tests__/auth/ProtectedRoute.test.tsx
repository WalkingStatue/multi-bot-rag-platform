/**
 * Unit tests for ProtectedRoute component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProtectedRoute } from '../../components/auth/ProtectedRoute';
import { useAuth } from '../../hooks/useAuth';

// Mock the useAuth hook
vi.mock('../../hooks/useAuth');

const mockUseAuth = vi.mocked(useAuth);

const TestComponent = () => <div>Protected Content</div>;

const renderProtectedRoute = (props = {}, initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ProtectedRoute {...props}>
        <TestComponent />
      </ProtectedRoute>
    </MemoryRouter>
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: vi.fn(),
    });
  });

  it('shows loading spinner when authentication is loading', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: vi.fn(),
    });

    renderProtectedRoute();

    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument(); // Loading spinner
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('redirects to login when user is not authenticated and auth is required', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: vi.fn(),
    });

    renderProtectedRoute({ requireAuth: true });

    // Should redirect, so protected content should not be rendered
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders children when user is authenticated and auth is required', () => {
    mockUseAuth.mockReturnValue({
      user: { id: '1', username: 'testuser', email: 'test@example.com', full_name: 'Test User', avatar_url: null, is_active: true, created_at: '2023-01-01', updated_at: '2023-01-01' },
      isAuthenticated: true,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: vi.fn(),
    });

    renderProtectedRoute({ requireAuth: true });

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects authenticated user away from auth pages', () => {
    mockUseAuth.mockReturnValue({
      user: { id: '1', username: 'testuser', email: 'test@example.com', full_name: 'Test User', avatar_url: null, is_active: true, created_at: '2023-01-01', updated_at: '2023-01-01' },
      isAuthenticated: true,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: vi.fn(),
    });

    renderProtectedRoute({ requireAuth: false });

    // Should redirect, so auth page content should not be rendered
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders children when user is not authenticated and auth is not required', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: vi.fn(),
    });

    renderProtectedRoute({ requireAuth: false });

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('uses custom redirect path', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
      requestPasswordReset: vi.fn(),
      resetPassword: vi.fn(),
      clearError: vi.fn(),
    });

    renderProtectedRoute({ 
      requireAuth: true, 
      redirectTo: '/custom-login' 
    });

    // Should redirect, so protected content should not be rendered
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});