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

  // Initialize chat for the bot
  useEffect(() => {
    const token = authService.getAccessToken();
    if (!bot || !user || !token || isInitialized.current) return;

    const initializeChat = async () => {
      try {
        setLoading(true);
        setCurrentBot(bot.id);

        // Load existing sessions for this bot
        const botSessions = await chatService.getSessions(bot.id);
        setSessions(botSessions);

        // Connect to WebSocket
        chatWebSocketService.connectToBot(bot.id, token);

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
        return () => {
          unsubscribeChat();
          unsubscribeTyping();
          unsubscribeConnection();
        };

      } catch (error) {
        console.error('Failed to initialize chat:', error);
        setConnectionStatus({
          status: 'error',
          error: 'Failed to initialize chat'
        });
      } finally {
        setLoading(false);
      }
    };

    initializeChat();
    isInitialized.current = true;

    // Cleanup on unmount
    return () => {
      chatWebSocketService.disconnect();
      isInitialized.current = false;
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading chat...</span>
      </div>
    );
  }

  return (
    <div className={`flex h-full bg-white rounded-lg shadow-lg ${className}`}>
      {/* Session sidebar */}
      <div className="w-1/4 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Chat with {bot.name}
          </h3>
          <ConnectionStatus status={uiState.connectionStatus} />
        </div>
        <SessionList bot={bot} />
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {currentSessionId ? (
          <>
            <MessageList messages={currentMessages} />
            <TypingIndicator users={uiState.typingUsers} />
            <MessageInput botId={bot.id} sessionId={currentSessionId} />
          </>
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
  );
};