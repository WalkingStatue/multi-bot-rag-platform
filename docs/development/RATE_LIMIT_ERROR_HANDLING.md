# Rate Limit Error Handling Implementation

## Problem
The OpenRouter API rate limit error `{"detail":"OpenRouter API rate limit exceeded"}` was not being properly handled in the frontend, leading to poor user experience when rate limits were hit.

## Solution Overview
Implemented comprehensive error handling for API rate limits and other chat-related errors across the frontend application.

## Changes Made

### 1. Enhanced API Client (`frontend/src/services/api.ts`)
- **Improved 429 handling**: Added specific detection for OpenRouter rate limit errors
- **Longer retry delays**: OpenRouter rate limits use 10-second delays vs 5-second for others
- **Fewer retries**: OpenRouter gets 1 retry attempt vs 2 for other rate limits
- **Enhanced error context**: Attached user-friendly error messages to errors

### 2. New Error Types (`frontend/src/types/chat.ts`)
- **ChatError interface**: Structured error handling with type, message, provider, and retry info
- **MessageWithStatus enhancement**: Added error field to messages for display

### 3. Enhanced Chat Service (`frontend/src/services/chatService.ts`)
- **parseApiError function**: Converts API errors into structured ChatError objects
- **Specific error handling**: Different handling for rate limits, auth errors, validation errors, etc.
- **Enhanced sendMessage**: Wraps API calls with proper error parsing

### 4. Updated Chat Store (`frontend/src/stores/chatStore.ts`)
- **Error state management**: Added lastError state and error management actions
- **Global error handling**: Centralized error state for UI components

### 5. Improved Chat Session Hook (`frontend/src/hooks/useChatSession.ts`)
- **Better error handling**: Proper error parsing and user-friendly messages
- **Error state integration**: Uses global error state from store

### 6. New Chat Message Hook (`frontend/src/hooks/useChatMessage.ts`)
- **Message-specific error handling**: Handles errors during message sending
- **Optimistic updates**: Shows messages immediately, updates on success/failure
- **Retry context**: Provides retry information for rate-limited messages

### 7. Error Display Component (`frontend/src/components/chat/ChatErrorDisplay.tsx`)
- **Visual error feedback**: Different icons and colors for different error types
- **Retry functionality**: Built-in retry buttons for retryable errors
- **Dismissible errors**: Users can dismiss error messages
- **Contextual information**: Shows retry delays and specific guidance

### 8. Example Chat Interface (`frontend/src/components/chat/ChatInterface.tsx`)
- **Complete integration**: Shows how to use all error handling components together
- **User experience**: Proper loading states and error recovery

## Error Types Handled

### Rate Limit Errors
- **OpenRouter specific**: 30-second retry delay, specific messaging
- **General rate limits**: 10-second retry delay
- **Visual feedback**: Yellow warning styling
- **User guidance**: Clear instructions on wait times

### API Authentication Errors
- **API key issues**: Clear messaging about checking bot settings
- **Non-retryable**: Prevents infinite retry loops
- **Red error styling**: Indicates critical issues

### Network Errors
- **Connection issues**: Detects network problems
- **Retryable**: Allows users to retry after connection recovery
- **Orange warning styling**: Indicates temporary issues

### Validation Errors
- **Input validation**: Handles malformed requests
- **Non-retryable**: Prevents repeated invalid requests
- **Clear messaging**: Explains what needs to be fixed

## Usage Examples

### Basic Error Handling
```typescript
const { error, clearError } = useChatSession({ botId });

return (
  <ChatErrorDisplay
    error={error}
    onDismiss={clearError}
  />
);
```

### Message Sending with Error Handling
```typescript
const { sendMessage, error, clearError } = useChatMessage({ botId, sessionId });

const handleSend = async () => {
  try {
    await sendMessage(content);
  } catch (err) {
    // Error is automatically handled by the hook
  }
};
```

### Custom Error Handling
```typescript
// Errors are automatically parsed and structured
const chatError: ChatError = {
  type: 'rate_limit',
  message: 'OpenRouter API rate limit exceeded. Please wait before sending another message.',
  provider: 'openrouter',
  retryable: true,
  retryAfter: 30
};
```

## Benefits

1. **Better User Experience**: Clear, actionable error messages
2. **Automatic Recovery**: Built-in retry logic with appropriate delays
3. **Provider-Specific Handling**: Different strategies for different API providers
4. **Visual Feedback**: Color-coded error types with appropriate icons
5. **Centralized Error Management**: Consistent error handling across the app
6. **Graceful Degradation**: App continues to function even with API issues

## Testing Rate Limits

To test the rate limit handling:

1. **Trigger OpenRouter rate limit**: Send multiple rapid requests to a bot using OpenRouter
2. **Observe error display**: Should show yellow warning with specific OpenRouter messaging
3. **Test retry functionality**: Retry button should respect the 30-second delay
4. **Check automatic retry**: API client should automatically retry once with proper delay

## Future Enhancements

1. **Rate limit prediction**: Warn users before hitting limits
2. **Provider switching**: Automatically switch to different providers when one is rate-limited
3. **Usage analytics**: Track rate limit occurrences for optimization
4. **Batch message queuing**: Queue messages during rate limit periods