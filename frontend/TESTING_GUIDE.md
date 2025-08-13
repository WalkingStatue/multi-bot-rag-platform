# Testing Guide

This document provides comprehensive guidance for testing the Multi-Bot RAG Platform frontend application.

## Testing Stack

Our testing setup includes:

- **Vitest** - Fast unit test runner with native ES modules support
- **React Testing Library** - Simple and complete testing utilities for React components
- **jsdom** - DOM implementation for Node.js (test environment)
- **@testing-library/jest-dom** - Custom matchers for DOM elements
- **@testing-library/user-event** - Advanced user interaction simulation

## Configuration

### Vitest Configuration (`vitest.config.ts`)

```typescript
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  }
});
```

### Test Setup (`src/test/setup.ts`)

Global test configuration including:
- jest-dom matchers
- Mock implementations for browser APIs
- Global cleanup after each test
- Environment variable mocks

### Test Utilities (`src/test/utils.tsx`)

Comprehensive testing utilities including:
- Custom render function with providers
- Mock data generators
- API response mocks
- Helper functions for common testing patterns

## Writing Tests

### Basic Component Test Structure

```typescript
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, screen, fireEvent } from '../../../test/utils';
import { ComponentName } from '../ComponentName';

describe('ComponentName', () => {
  it('renders correctly', () => {
    renderWithProviders(<ComponentName />);
    
    const element = screen.getByRole('button');
    expect(element).toBeInTheDocument();
  });

  it('handles user interactions', async () => {
    const handleClick = vi.fn();
    renderWithProviders(<ComponentName onClick={handleClick} />);
    
    const button = screen.getByRole('button');
    await fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Testing Patterns

#### 1. Component Rendering Tests

```typescript
describe('Button Component', () => {
  it('renders with default props', () => {
    renderWithProviders(<Button>Click me</Button>);
    
    expect(screen.getByRole('button')).toBeInTheDocument();
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('applies correct CSS classes', () => {
    renderWithProviders(<Button variant="primary" size="lg">Button</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-primary', 'btn-lg');
  });
});
```

#### 2. User Interaction Tests

```typescript
describe('Form Component', () => {
  it('handles form submission', async () => {
    const onSubmit = vi.fn();
    renderWithProviders(<LoginForm onSubmit={onSubmit} />);
    
    // Fill form fields
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    
    // Submit form
    await userEvent.click(screen.getByRole('button', { name: /login/i }));
    
    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    });
  });
});
```

#### 3. API Integration Tests

```typescript
describe('UserProfile Component', () => {
  it('loads and displays user data', async () => {
    const mockUser = { name: 'John Doe', email: 'john@example.com' };
    
    // Mock API response
    vi.mocked(fetch).mockResolvedValueOnce(
      mockFetchResponse({ data: mockUser })
    );
    
    renderWithProviders(<UserProfile userId="123" />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
    
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
});
```

#### 4. Error Handling Tests

```typescript
describe('ErrorBoundary', () => {
  it('catches and displays errors', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };
    
    renderWithProviders(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
```

#### 5. Hook Testing

```typescript
import { renderHook, act } from '@testing-library/react';

describe('useCounter Hook', () => {
  it('increments counter', () => {
    const { result } = renderHook(() => useCounter(0));
    
    act(() => {
      result.current.increment();
    });
    
    expect(result.current.count).toBe(1);
  });
});
```

### Testing Async Operations

#### 1. API Calls

```typescript
it('handles API loading states', async () => {
  renderWithProviders(<DataComponent />);
  
  // Check loading state
  expect(screen.getByText(/loading/i)).toBeInTheDocument();
  
  // Wait for data to load
  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument();
  });
  
  // Loading indicator should be gone
  expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
});
```

#### 2. User Events

```typescript
it('handles async user interactions', async () => {
  const user = userEvent.setup();
  renderWithProviders(<AsyncButton />);
  
  const button = screen.getByRole('button');
  await user.click(button);
  
  await waitFor(() => {
    expect(screen.getByText('Success')).toBeInTheDocument();
  });
});
```

### Mocking Strategies

#### 1. API Mocks

```typescript
// Mock entire API module
vi.mock('../services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock specific API calls
beforeEach(() => {
  vi.mocked(apiClient.get).mockResolvedValue({ data: mockData });
});
```

#### 2. Component Mocks

```typescript
// Mock child components
vi.mock('../components/ComplexChild', () => ({
  ComplexChild: ({ onAction }: { onAction: () => void }) => (
    <button onClick={onAction}>Mocked Child</button>
  )
}));
```

#### 3. Hook Mocks

```typescript
// Mock custom hooks
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: mockUser,
    login: vi.fn(),
    logout: vi.fn(),
    isAuthenticated: true,
  })
}));
```

### Testing Best Practices

#### 1. Test Structure

- **Arrange**: Set up test data and mocks
- **Act**: Perform the action being tested
- **Assert**: Verify the expected outcome

#### 2. Descriptive Test Names

```typescript
// ❌ Bad
it('works', () => { ... });

// ✅ Good
it('displays error message when login fails', () => { ... });
```

#### 3. Test User Behavior, Not Implementation

```typescript
// ❌ Testing implementation details
expect(component.state.isLoading).toBe(true);

// ✅ Testing user-visible behavior
expect(screen.getByText(/loading/i)).toBeInTheDocument();
```

#### 4. Use Semantic Queries

```typescript
// Preferred query methods (in order):
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText(/email address/i)
screen.getByText(/welcome/i)
screen.getByDisplayValue('John')
screen.getByAltText('Profile picture')
screen.getByTitle('Close dialog')

// Avoid when possible:
screen.getByTestId('submit-button') // Only when semantic queries don't work
```

#### 5. Async Testing

```typescript
// ❌ Don't use arbitrary timeouts
await new Promise(resolve => setTimeout(resolve, 1000));

// ✅ Use waitFor for dynamic waits
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});
```

### Coverage Requirements

Our coverage thresholds are set to:
- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test Button.test.tsx

# Run tests matching pattern
npm test -- --grep "Button"
```

### Test Organization

```
src/
├── components/
│   └── common/
│       ├── Button.tsx
│       └── __tests__/
│           └── Button.test.tsx
├── hooks/
│   ├── useAuth.ts
│   └── __tests__/
│       └── useAuth.test.ts
├── services/
│   ├── api.ts
│   └── __tests__/
│       └── api.test.ts
└── test/
    ├── setup.ts
    ├── utils.tsx
    └── mocks/
        ├── api.ts
        └── localStorage.ts
```

### Common Testing Scenarios

#### 1. Form Validation

```typescript
it('shows validation errors for invalid input', async () => {
  renderWithProviders(<ContactForm />);
  
  const emailInput = screen.getByLabelText(/email/i);
  const submitButton = screen.getByRole('button', { name: /submit/i });
  
  await userEvent.type(emailInput, 'invalid-email');
  await userEvent.click(submitButton);
  
  expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
});
```

#### 2. Loading States

```typescript
it('shows loading spinner during API call', async () => {
  // Mock delayed API response
  vi.mocked(fetch).mockImplementation(
    () => new Promise(resolve => setTimeout(() => resolve(mockResponse), 100))
  );
  
  renderWithProviders(<DataList />);
  
  expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  
  await waitFor(() => {
    expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
  });
});
```

#### 3. Error States

```typescript
it('displays error message when API call fails', async () => {
  vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));
  
  renderWithProviders(<DataList />);
  
  await waitFor(() => {
    expect(screen.getByText(/failed to load data/i)).toBeInTheDocument();
  });
});
```

#### 4. Accessibility Testing

```typescript
it('has proper accessibility attributes', () => {
  renderWithProviders(<Modal title="Settings" />);
  
  const modal = screen.getByRole('dialog');
  expect(modal).toHaveAttribute('aria-labelledby');
  expect(modal).toHaveAttribute('aria-modal', 'true');
});
```

### Debugging Tests

#### 1. Debug Rendered Output

```typescript
import { screen } from '@testing-library/react';

it('debug test', () => {
  renderWithProviders(<Component />);
  
  // Print current DOM
  screen.debug();
  
  // Print specific element
  screen.debug(screen.getByRole('button'));
});
```

#### 2. Query Debugging

```typescript
// Find out why a query is failing
screen.getByRole('button'); // Throws error with available roles
screen.logTestingPlaygroundURL(); // Get Testing Playground URL
```

### Performance Testing

```typescript
it('renders large lists efficiently', () => {
  const items = Array.from({ length: 1000 }, (_, i) => ({ id: i, name: `Item ${i}` }));
  
  const startTime = performance.now();
  renderWithProviders(<ItemList items={items} />);
  const endTime = performance.now();
  
  expect(endTime - startTime).toBeLessThan(100); // Should render in under 100ms
});
```

### Integration Testing

```typescript
describe('Login Flow Integration', () => {
  it('completes full login process', async () => {
    renderWithProviders(<App />);
    
    // Navigate to login
    await userEvent.click(screen.getByText(/login/i));
    
    // Fill login form
    await userEvent.type(screen.getByLabelText(/email/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password');
    
    // Submit form
    await userEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Verify redirect to dashboard
    await waitFor(() => {
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });
  });
});
```

This comprehensive testing setup ensures high code quality, catches regressions early, and provides confidence in the application's reliability.