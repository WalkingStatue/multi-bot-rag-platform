/**
 * Unit tests for AuthService
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authService } from '../../services/authService';
import { apiClient } from '../../services/api';

// Mock the API client
vi.mock('../../services/api');

const mockApiClient = vi.mocked(apiClient);

describe('AuthService', () => {
  beforeEach(() => {
    // Clear localStorage mock
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('should login user successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'access123',
          refresh_token: 'refresh123',
          token_type: 'bearer',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.post.mockResolvedValueOnce(mockResponse);

      const result = await authService.login({
        username: 'testuser',
        password: 'password123',
      });

      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/login', {
        username: 'testuser',
        password: 'password123',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle login error', async () => {
      const mockError = new Error('Invalid credentials');
      mockApiClient.post.mockRejectedValueOnce(mockError);

      await expect(
        authService.login({
          username: 'testuser',
          password: 'wrongpassword',
        })
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('register', () => {
    it('should register user successfully', async () => {
      const mockResponse = {
        data: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          full_name: 'Test User',
          avatar_url: null,
          is_active: true,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
        },
        status: 201,
        statusText: 'Created',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.post.mockResolvedValueOnce(mockResponse);

      const result = await authService.register({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        full_name: 'Test User',
      });

      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/register', {
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        full_name: 'Test User',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('logout', () => {
    it('should logout user successfully', async () => {
      mockApiClient.post.mockResolvedValueOnce({ 
        data: {},
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      await authService.logout();

      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/logout');
    });
  });

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'newaccess123',
          refresh_token: 'newrefresh123',
          token_type: 'bearer',
          expires_in: 3600,
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.post.mockResolvedValueOnce(mockResponse);

      const result = await authService.refreshToken('refresh123');

      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/refresh', {
        refresh_token: 'refresh123',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getCurrentUser', () => {
    it('should get current user successfully', async () => {
      const mockResponse = {
        data: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          full_name: 'Test User',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.get.mockResolvedValueOnce(mockResponse);

      const result = await authService.getCurrentUser();

      expect(mockApiClient.get).toHaveBeenCalledWith('/users/profile');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('updateProfile', () => {
    it('should update profile successfully', async () => {
      const mockResponse = {
        data: {
          id: '1',
          username: 'newusername',
          email: 'newemail@example.com',
          full_name: 'New Name',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any;

      mockApiClient.put.mockResolvedValueOnce(mockResponse);

      const result = await authService.updateProfile({
        username: 'newusername',
        email: 'newemail@example.com',
        full_name: 'New Name',
      });

      expect(mockApiClient.put).toHaveBeenCalledWith('/users/profile', {
        username: 'newusername',
        email: 'newemail@example.com',
        full_name: 'New Name',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('requestPasswordReset', () => {
    it('should request password reset successfully', async () => {
      mockApiClient.post.mockResolvedValueOnce({ 
        data: {},
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      await authService.requestPasswordReset('test@example.com');

      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/forgot-password', {
        email: 'test@example.com',
      });
    });
  });

  describe('resetPassword', () => {
    it('should reset password successfully', async () => {
      mockApiClient.post.mockResolvedValueOnce({ 
        data: {},
        status: 200,
        statusText: 'OK',
        headers: {},
        config: { headers: {} },
      } as any);

      await authService.resetPassword('token123', 'newpassword123');

      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/reset-password', {
        token: 'token123',
        new_password: 'newpassword123',
      });
    });
  });

  describe('token management', () => {
    it('should check if user is authenticated', () => {
      localStorage.setItem('access_token', 'token123');
      expect(authService.isAuthenticated()).toBe(true);

      localStorage.removeItem('access_token');
      expect(authService.isAuthenticated()).toBe(false);
    });

    it('should get access token', () => {
      localStorage.setItem('access_token', 'token123');
      expect(authService.getAccessToken()).toBe('token123');

      localStorage.removeItem('access_token');
      expect(authService.getAccessToken()).toBeNull();
    });

    it('should get refresh token', () => {
      localStorage.setItem('refresh_token', 'refresh123');
      expect(authService.getRefreshToken()).toBe('refresh123');

      localStorage.removeItem('refresh_token');
      expect(authService.getRefreshToken()).toBeNull();
    });

    it('should store tokens', () => {
      const tokens = {
        access_token: 'access123',
        refresh_token: 'refresh123',
        token_type: 'bearer',
        expires_in: 3600,
      };

      authService.storeTokens(tokens);

      expect(localStorage.getItem('access_token')).toBe('access123');
      expect(localStorage.getItem('refresh_token')).toBe('refresh123');
    });

    it('should clear tokens', () => {
      localStorage.setItem('access_token', 'access123');
      localStorage.setItem('refresh_token', 'refresh123');

      authService.clearTokens();

      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });
});