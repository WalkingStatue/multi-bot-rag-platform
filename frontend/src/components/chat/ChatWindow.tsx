/**
 * Main chat window component
 */
import React, { useEffect, useRef } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { chatService } from '../../services/chatService';
import { chatWebSocketService } from '../../services/chatWebSocketService';
import { authService } from '../../services/authService';
import { useAuth } from '../../hooks/useAuth';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { SessionList } from './SessionList';
import { ConnectionStatus } from './ConnectionStatus';
import { TypingIndicator } from './TypingIndicator';
import { ErrorBoundary, ChatErrorFallback } from '../common/ErrorBoundary';
import { runWebSocketDiagnostics } from '../../utils/websocketDiagnostics';

import { BotResponse } from '../../types/bot';

interface ChatWindowProps {
  bot: BotResponse;
  className?: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ bot, className = '' }) => {
  const { user } = useAuth();
  const {
    currentSessionId,
    currentBotId,
    sessions,
    uiState,
    setSessions,
    setCurrentBot,
    setCurrentSession,
    setLoading,
    setConnectionStatus,
    getCurrentMessages
  } = useChatStore();

  const isInitialized = useRef(false);
  const cleanupFunctions = useRef<(() => void)[]>([]);

  // Fallback to prevent infinite loading
  useEffect(() => {
    const fallbackTimer = setTimeout(() => {
      if (uiState.isLoading) {
        console.warn('Chat initialization taking too long, forcing completion');
        setLoading(false);
      }
    }, 10000); // 10 second fallback

    return () => clearTimeout(fallbackTimer);
  }, [uiState.isLoading, setLoading]);

  // Initialize chat for the bot
  useEffect(() => {
    console.log('ChatWindow useEffect triggered', { 
      botId: bot?.id, 
      userId: user?.id, 
      hasToken: !!authService.getAccessToken(),
      isInitialized: isInitialized.current,
      currentBotId 
    });
    
    const token = authService.getAccessToken();
    if (!bot || !user || !token) {
      console.log('Missing required data for chat initialization', { bot: !!bot, user: !!user, token: !!token });
      return;
    }

    // Prevent multiple initializations for the same bot
    if (isInitialized.current && currentBotId === bot.id) {
      console.log('Chat already initialized for this bot, skipping');
      return;
    }

    let isCancelled = false;

    const initializeChat = async () => {
      // Add a timeout to prevent hanging
      const timeoutId = setTimeout(() => {
        if (!isCancelled) {
          console.error('Chat initialization timed out');
          setLoading(false);
          setConnectionStatus({
            status: 'error',
            error: 'Initialization timed out'
          });
        }
      }, 15000); // 15 second timeout
      try {
        if (isCancelled) return;
        
        console.log('Starting chat initialization for bot:', bot.id);
        setLoading(true);
        setCurrentBot(bot.id);

        // Load existing sessions for this bot
        console.log('Loading sessions for bot:', bot.id);
        try {
          const botSessions = await chatService.getSessions(bot.id);
          if (isCancelled) return;
          
          console.log('Loaded sessions:', botSessions.length);
          setSessions(botSessions);
        } catch (sessionError) {
          console.error('Failed to load sessions:', sessionError);
          // Continue with empty sessions rather than failing completely
          setSessions([]);
        }

        // Connect to WebSocket only if not already connected to this bot
        if (chatWebSocketService.getCurrentBotId() !== bot.id && !isCancelled) {
          try {
            console.log('Connecting to WebSocket for bot:', bot.id);
            await chatWebSocketService.connectToBot(bot.id, token);
            console.log('WebSocket connected successfully');
          } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            if (!isCancelled) {
              setConnectionStatus({
                status: 'error',
                error: 'Failed to connect to WebSocket'
              });
              // Run diagnostics to help debug the issue
              await runWebSocketDiagnostics(bot.id, token);
              // Don't throw the error - continue with initialization
              // The chat can still work without real-time updates
            }
          }
        }

        if (isCancelled) return;

        console.log('Setting up WebSocket event listeners');
        // Set up WebSocket event listeners
        const unsubscribeChat = chatWebSocketService.onChatMessage((message) => {
          // Handle incoming chat messages
          if (message.bot_id === bot.id) {
            const { addMessage } = useChatStore.getState();
            addMessage(message.data.session_id, {
              id: message.data.message_id,
              session_id: message.data.session_id,
              bot_id: message.bot_id,
              user_id: message.data.user_id,
              role: message.data.role,
              content: message.data.content,
              message_metadata: message.data.metadata,
              created_at: message.data.timestamp,
              status: 'sent'
            });
          }
        });

        const unsubscribeTyping = chatWebSocketService.onTypingIndicator((indicator) => {
          if (indicator.bot_id === bot.id) {
            const { addTypingUser, removeTypingUser } = useChatStore.getState();
            if (indicator.data.is_typing) {
              addTypingUser(indicator.data.username);
            } else {
              removeTypingUser(indicator.data.username);
            }
          }
        });

        const unsubscribeConnection = chatWebSocketService.onConnectionStatus((status) => {
          setConnectionStatus(status);
        });

        // Store cleanup functions
        cleanupFunctions.current = [
          unsubscribeChat,
          unsubscribeTyping,
          unsubscribeConnection
        ];

        console.log('Chat initialization completed successfully');
        if (!isCancelled) {
          isInitialized.current = true;
        }

      } catch (error) {
        console.error('Failed to initialize chat:', error);
        if (!isCancelled) {
          setConnectionStatus({
            status: 'error',
            error: 'Failed to initialize chat'
          });
        }
      } finally {
        clearTimeout(timeoutId);
        if (!isCancelled) {
          console.log('Setting loading to false');
          setLoading(false);
        }
      }
    };

    initializeChat();

    // Cleanup on unmount or bot change
    return () => {
      isCancelled = true;
      
      // Run cleanup functions
      cleanupFunctions.current.forEach(cleanup => {
        try {
          cleanup();
        } catch (error) {
          console.error('Error during cleanup:', error);
        }
      });
      cleanupFunctions.current = [];
      
      // Only disconnect if we're changing bots or unmounting
      if (currentBotId !== bot.id) {
        chatWebSocketService.disconnect();
        isInitialized.current = false;
      }
    };
  }, [bot?.id, user?.id]);

  // Auto-select first session if none selected
  useEffect(() => {
    if (sessions.length > 0 && !currentSessionId && currentBotId === bot.id) {
      setCurrentSession(sessions[0].id);
    }
  }, [sessions, currentSessionId, currentBotId, bot.id]);

  const currentMessages = getCurrentMessages();

  if (uiState.isLoading) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <span className="text-gray-600">Loading chat...</span>
          <div className="mt-4">
            <button 
              onClick={() => {
                console.log('Force stopping loading state');
                setLoading(false);
              }}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              Taking too long? Click here to continue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary fallback={<ChatErrorFallback error="Chat failed to load" />}>
      <div className={`flex h-full bg-white rounded-lg shadow-lg ${className}`}>
        {/* Session sidebar */}
        <div className="w-1/4 border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Chat with {bot.name}
            </h3>
            <div className="mt-2">
              <ConnectionStatus />
            </div>
          </div>
          <SessionList bot={bot} />
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          {currentSessionId ? (
            <ErrorBoundary fallback={<ChatErrorFallback error="Chat messages failed to load" />}>
              <MessageList messages={currentMessages} />
              <TypingIndicator users={uiState.typingUsers} />
              <MessageInput botId={bot.id} sessionId={currentSessionId} />
            </ErrorBoundary>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <p className="text-lg mb-2">No conversation selected</p>
                <p className="text-sm">Select a conversation or start a new one</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
};