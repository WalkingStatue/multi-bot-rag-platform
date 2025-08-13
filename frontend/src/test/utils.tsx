/**
 * Test utilities and helpers
 */

import React from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { ToastProvider } from '../components/common/Toast';
import { ErrorBoundary } from '../components/common/ErrorBoundary';

// Mock data generators
export const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  username: 'testuser',
  firstName: 'Test',
  lastName: 'User',
  role: 'user' as const,
  isActive: true,
  preferences: {
    theme: 'light' as const,
    language: 'en',
    timezone: 'UTC',
    notifications: {
      email: true,
      push: true,
      inApp: true,
      marketing: false,
    },
    privacy: {
      profileVisibility: 'public' as const,
      showOnlineStatus: true,
      allowDirectMessages: true,
    },
  },
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

export const mockBot = {
  id: 'bot-1',
  name: 'Test Bot',
  description: 'A test bot for testing purposes',
  type: 'rag' as const,
  status: 'active' as const,
  config: {
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 1000,
    systemPrompt: 'You are a helpful assistant.',
  },
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

export const mockConversation = {
  id: 'conv-1',
  title: 'Test Conversation',
  botId: 'bot-1',
  userId: 'user-1',
  status: 'active' as const,
  messageCount: 2,
  lastMessageAt: '2024-01-01T00:00:00Z',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

export const mockMessage = {
  id: 'msg-1',
  conversationId: 'conv-1',
  content: 'Hello, how can I help you?',
  role: 'assistant' as const,
  timestamp: '2024-01-01T00:00:00Z',
  metadata: {},
};

export const mockDocument = {
  id: 'doc-1',
  name: 'test-document.pdf',
  type: 'application/pdf',
  size: 1024000,
  status: 'processed' as const,
  uploadedAt: '2024-01-01T00:00:00Z',
  processedAt: '2024-01-01T00:00:00Z',
  metadata: {
    pages: 10,
    wordCount: 5000,
  },
};

// Test wrapper component
interface TestWrapperProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
  initialEntries?: string[];
}

const TestWrapper: React.FC<TestWrapperProps> = ({
  children,
  queryClient,
  initialEntries = ['/'],
}) => {
  const testQueryClient = queryClient || new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <ErrorBoundary>
      <QueryClientProvider client={testQueryClient}>
        <BrowserRouter>
          <ToastProvider>
            {children}
          </ToastProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

// Custom render function
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  initialEntries?: string[];
}

export const renderWithProviders = (
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
): RenderResult => {
  const { queryClient, initialEntries, ...renderOptions } = options;

  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    const wrapperProps: TestWrapperProps = { children };
    if (queryClient) {
      wrapperProps.queryClient = queryClient;
    }
    if (initialEntries) {
      wrapperProps.initialEntries = initialEntries;
    }
    return <TestWrapper {...wrapperProps} />;
  };

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock API responses
export const mockApiResponse = <T,>(data: T, delay = 0) => {
  return new Promise<{ data: T }>((resolve) => {
    setTimeout(() => {
      resolve({ data });
    }, delay);
  });
};

export const mockApiError = (message: string, status = 500, delay = 0) => {
  return new Promise((_, reject) => {
    setTimeout(() => {
      const error = new Error(message);
      (error as any).response = {
        status,
        data: { message },
      };
      reject(error);
    }, delay);
  });
};

// Mock fetch responses
export const mockFetchResponse = (data: any, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
  } as Response);
};

// Mock localStorage
export const mockLocalStorage = () => {
  const store: Record<string, string> = {};

  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
  };
};

// Mock WebSocket
export const mockWebSocket = () => {
  const listeners: Record<string, Function[]> = {};

  return {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn((event: string, callback: Function) => {
      if (!listeners[event]) listeners[event] = [];
      listeners[event].push(callback);
    }),
    removeEventListener: vi.fn((event: string, callback: Function) => {
      if (listeners[event]) {
        const index = listeners[event].indexOf(callback);
        if (index > -1) listeners[event].splice(index, 1);
      }
    }),
    readyState: 1, // OPEN
    trigger: (event: string, data?: any) => {
      if (listeners[event]) {
        listeners[event].forEach(callback => callback(data));
      }
    },
  };
};

// Test helpers
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0));
};

export const createMockIntersectionObserver = () => {
  const mockIntersectionObserver = vi.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  });
  return mockIntersectionObserver;
};

export const createMockResizeObserver = () => {
  const mockResizeObserver = vi.fn();
  mockResizeObserver.mockReturnValue({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  });
  return mockResizeObserver;
};

// Form testing helpers
export const fillForm = async (form: HTMLFormElement, data: Record<string, string>) => {
  const { fireEvent } = await import('@testing-library/react');
  
  Object.entries(data).forEach(([name, value]) => {
    const input = form.querySelector(`[name="${name}"]`) as HTMLInputElement;
    if (input) {
      fireEvent.change(input, { target: { value } });
    }
  });
};

export const submitForm = async (form: HTMLFormElement) => {
  const { fireEvent } = await import('@testing-library/react');
  fireEvent.submit(form);
};

// Async testing helpers
export const flushPromises = () => {
  return new Promise(resolve => setTimeout(resolve, 0));
};

export const advanceTimers = (ms: number) => {
  vi.advanceTimersByTime(ms);
  return flushPromises();
};

// Error boundary testing
export const ThrowError: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow = true }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
};

// Custom matchers
export const customMatchers = {
  toBeInTheDocument: (received: any) => {
    const pass = received && document.body.contains(received);
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to be in the document`,
      pass,
    };
  },
};

// Export everything for easy importing
export * from '@testing-library/react';
export * from '@testing-library/user-event';
export { vi } from 'vitest';