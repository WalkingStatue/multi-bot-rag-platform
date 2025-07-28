"""
Chat service with RAG integration for processing messages and generating responses.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid

from ..models.bot import Bot
from ..models.conversation import ConversationSession, Message
from ..models.user import User
from ..schemas.conversation import ChatRequest, ChatResponse
from .conversation_service import ConversationService
from .permission_service import PermissionService
from .llm_service import LLMProviderService
from .embedding_service import EmbeddingProviderService
from .vector_store import VectorService
from .user_service import UserService


logger = logging.getLogger(__name__)

# Import WebSocket service (avoid circular import by importing at module level)
def get_websocket_service():
    """Get WebSocket service instance to avoid circular imports."""
    from .websocket_service import WebSocketService
    return WebSocketService


class ChatService:
    """Service for processing chat messages with RAG integration."""
    
    def __init__(self, db: Session):
        """
        Initialize chat service with required dependencies.
        
        Args:
            db: Database session
        """
        self.db = db
        self.conversation_service = ConversationService(db)
        self.permission_service = PermissionService(db)
        self.llm_service = LLMProviderService()
        self.embedding_service = EmbeddingProviderService()
        self.vector_service = VectorService()
        self.user_service = UserService(db)
        
        # Configuration
        self.max_history_messages = 10
        self.max_retrieved_chunks = 5
        self.similarity_threshold = 0.7
        self.max_prompt_length = 8000
    
    async def process_message(
        self,
        bot_id: uuid.UUID,
        user_id: uuid.UUID,
        chat_request: ChatRequest
    ) -> ChatResponse:
        """
        Process a chat message through the complete RAG pipeline.
        
        Args:
            bot_id: Bot identifier
            user_id: User identifier
            chat_request: Chat request with message and optional session_id
            
        Returns:
            ChatResponse with generated response and metadata
            
        Raises:
            HTTPException: If permission denied or processing fails
        """
        start_time = time.time()
        
        try:
            # Step 1: Permission validation
            if not self.permission_service.check_bot_permission(
                user_id, bot_id, "view_conversations"
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to chat with this bot"
                )
            
            # Step 2: Get bot configuration
            bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found"
                )
            
            # Step 3: Get or create conversation session
            session = await self._get_or_create_session(
                bot_id, user_id, chat_request.session_id
            )
            
            # Step 4: Store user message
            user_message = await self._store_user_message(
                session.id, bot_id, user_id, chat_request.message
            )
            
            # Step 5: Retrieve relevant document chunks using RAG
            relevant_chunks = await self._retrieve_relevant_chunks(
                bot, chat_request.message
            )
            
            # Step 6: Get conversation history
            conversation_history = await self._get_conversation_history(
                session.id, user_id
            )
            
            # Step 7: Build prompt with context
            prompt = await self._build_prompt(
                bot, conversation_history, relevant_chunks, chat_request.message
            )
            
            # Step 8: Generate response using configured LLM
            response_text, response_metadata = await self._generate_response(
                bot, user_id, prompt
            )
            
            # Step 9: Store assistant response
            assistant_message = await self._store_assistant_message(
                session.id, bot_id, user_id, response_text, {
                    **response_metadata,
                    "chunks_used": [chunk["id"] for chunk in relevant_chunks],
                    "chunks_count": len(relevant_chunks),
                    "prompt_length": len(prompt)
                }
            )
            
            processing_time = time.time() - start_time
            
            # Step 10: Log conversation metadata
            await self._log_conversation_metadata(
                bot_id, user_id, session.id, user_message.id, assistant_message.id,
                processing_time, relevant_chunks, response_metadata
            )
            
            # Step 11: Send real-time WebSocket notifications
            await self._send_chat_notifications(
                bot_id, user_id, user_message, assistant_message, session.id
            )
            
            return ChatResponse(
                message=response_text,
                session_id=session.id,
                chunks_used=[chunk["text"][:100] + "..." if len(chunk["text"]) > 100 else chunk["text"] for chunk in relevant_chunks],
                processing_time=processing_time,
                metadata={
                    "user_message_id": str(user_message.id),
                    "assistant_message_id": str(assistant_message.id),
                    "chunks_count": len(relevant_chunks),
                    "llm_provider": bot.llm_provider,
                    "llm_model": bot.llm_model,
                    **response_metadata
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Chat processing failed for bot {bot_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process chat message: {str(e)}"
            )
    
    async def _get_or_create_session(
        self,
        bot_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID]
    ) -> ConversationSession:
        """Get existing session or create a new one."""
        if session_id:
            session = self.conversation_service.get_session(session_id, user_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or access denied"
                )
            return session
        else:
            # Create new session
            from ..schemas.conversation import ConversationSessionCreate
            session_data = ConversationSessionCreate(
                bot_id=bot_id,
                title="New Conversation"
            )
            return self.conversation_service.create_session(user_id, session_data)
    
    async def _store_user_message(
        self,
        session_id: uuid.UUID,
        bot_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str
    ) -> Message:
        """Store user message in the database."""
        from ..schemas.conversation import MessageCreate
        
        message_data = MessageCreate(
            session_id=session_id,
            role="user",
            content=content,
            message_metadata={"timestamp": time.time()}
        )
        
        return self.conversation_service.add_message(user_id, message_data)
    
    async def _store_assistant_message(
        self,
        session_id: uuid.UUID,
        bot_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        metadata: Dict[str, Any]
    ) -> Message:
        """Store assistant message in the database."""
        from ..schemas.conversation import MessageCreate
        
        message_data = MessageCreate(
            session_id=session_id,
            role="assistant",
            content=content,
            message_metadata=metadata
        )
        
        return self.conversation_service.add_message(user_id, message_data)
    
    async def _retrieve_relevant_chunks(
        self,
        bot: Bot,
        query: str
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks using semantic search."""
        try:
            # Generate query embedding
            user_api_key = self._get_user_api_key_sync(
                bot.owner_id, bot.embedding_provider
            )
            
            query_embedding = await self.embedding_service.generate_single_embedding(
                provider=bot.embedding_provider,
                text=query,
                model=bot.embedding_model,
                api_key=user_api_key
            )
            
            # Search for relevant chunks
            relevant_chunks = await self.vector_service.search_relevant_chunks(
                bot_id=str(bot.id),
                query_embedding=query_embedding,
                top_k=self.max_retrieved_chunks,
                score_threshold=self.similarity_threshold
            )
            
            logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks for bot {bot.id}")
            return relevant_chunks
            
        except Exception as e:
            logger.warning(f"Failed to retrieve chunks for bot {bot.id}: {e}")
            # Return empty list if retrieval fails - bot can still respond without RAG
            return []
    
    async def _get_conversation_history(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> List[Message]:
        """Get recent conversation history for context."""
        messages = self.conversation_service.get_session_messages(
            session_id, user_id, limit=self.max_history_messages
        )
        
        # Return messages in chronological order (oldest first)
        return sorted(messages, key=lambda m: m.created_at)
    
    async def _build_prompt(
        self,
        bot: Bot,
        history: List[Message],
        chunks: List[Dict[str, Any]],
        user_input: str
    ) -> str:
        """Build the complete prompt with system prompt, context, history, and user input."""
        prompt_parts = []
        
        # System prompt
        prompt_parts.append(f"System: {bot.system_prompt}")
        
        # Add retrieved document context if available
        if chunks:
            context_text = "\n\n".join([
                f"Document Context {i+1}:\n{chunk['text']}"
                for i, chunk in enumerate(chunks)
            ])
            prompt_parts.append(f"\nRelevant Context:\n{context_text}")
        
        # Add conversation history
        if history:
            history_text = "\n".join([
                f"{msg.role.title()}: {msg.content}"
                for msg in history[-self.max_history_messages:]  # Limit history
            ])
            prompt_parts.append(f"\nConversation History:\n{history_text}")
        
        # Add current user input
        prompt_parts.append(f"\nUser: {user_input}")
        prompt_parts.append("\nAssistant:")
        
        # Join and truncate if necessary
        full_prompt = "\n".join(prompt_parts)
        
        if len(full_prompt) > self.max_prompt_length:
            # Truncate from the middle (keep system prompt and recent context)
            system_part = prompt_parts[0]
            context_part = prompt_parts[1] if chunks else ""
            user_part = prompt_parts[-2] + "\n" + prompt_parts[-1]  # User input + Assistant:
            
            # Calculate available space for history
            fixed_parts_length = len(system_part) + len(context_part) + len(user_part) + 20  # Extra space for formatting
            remaining_length = self.max_prompt_length - fixed_parts_length
            
            if remaining_length > 100 and history:  # Keep some history if possible
                history_text = "\n".join([
                    f"{msg.role.title()}: {msg.content}"
                    for msg in history[-self.max_history_messages:]
                ])
                
                if len(history_text) > remaining_length:
                    # Truncate history to fit
                    truncated_history = history_text[:remaining_length-10] + "..."
                    full_prompt = f"{system_part}\n{context_part}\n\nConversation History:\n{truncated_history}\n{user_part}"
                else:
                    full_prompt = f"{system_part}\n{context_part}\n\nConversation History:\n{history_text}\n{user_part}"
            else:
                # No space for history, just use system + context + user
                full_prompt = f"{system_part}\n{context_part}\n{user_part}"
                
            # Final check - if still too long, truncate context
            if len(full_prompt) > self.max_prompt_length:
                available_for_context = self.max_prompt_length - len(system_part) - len(user_part) - 20
                if available_for_context > 100 and context_part:
                    truncated_context = context_part[:available_for_context-10] + "..."
                    full_prompt = f"{system_part}\n{truncated_context}\n{user_part}"
                else:
                    full_prompt = f"{system_part}\n{user_part}"
        
        return full_prompt
    
    async def _generate_response(
        self,
        bot: Bot,
        user_id: uuid.UUID,
        prompt: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate response using the configured LLM provider."""
        # Get user's API key for the LLM provider
        user_api_key = await self._get_user_api_key(user_id, bot.llm_provider)
        
        # Prepare LLM configuration
        llm_config = {
            "temperature": bot.temperature,
            "max_tokens": bot.max_tokens,
            "top_p": bot.top_p,
            "frequency_penalty": bot.frequency_penalty,
            "presence_penalty": bot.presence_penalty
        }
        
        # Generate response
        response_text = await self.llm_service.generate_response(
            provider=bot.llm_provider,
            model=bot.llm_model,
            prompt=prompt,
            api_key=user_api_key,
            config=llm_config
        )
        
        # Prepare metadata
        metadata = {
            "llm_provider": bot.llm_provider,
            "llm_model": bot.llm_model,
            "llm_config": llm_config,
            "response_length": len(response_text)
        }
        
        return response_text, metadata
    
    def _get_user_api_key_sync(
        self,
        user_id: uuid.UUID,
        provider: str
    ) -> Optional[str]:
        """Get user's API key for a specific provider (synchronous version)."""
        try:
            api_key = self.user_service.get_user_api_key(user_id, provider)
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No API key configured for provider '{provider}'. Please add your API key in settings."
                )
            return api_key
        except Exception as e:
            logger.error(f"Failed to get API key for user {user_id}, provider {provider}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve API key"
            )
    
    async def _get_user_api_key(
        self,
        user_id: uuid.UUID,
        provider: str
    ) -> Optional[str]:
        """Get user's API key for a specific provider."""
        return self._get_user_api_key_sync(user_id, provider)
    
    async def _log_conversation_metadata(
        self,
        bot_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        user_message_id: uuid.UUID,
        assistant_message_id: uuid.UUID,
        processing_time: float,
        chunks: List[Dict[str, Any]],
        response_metadata: Dict[str, Any]
    ):
        """Log comprehensive conversation metadata for analytics."""
        try:
            # Create activity log entry
            from ..models.activity import ActivityLog
            
            activity_log = ActivityLog(
                bot_id=bot_id,
                user_id=user_id,
                action="chat_interaction",
                details={
                    "session_id": str(session_id),
                    "user_message_id": str(user_message_id),
                    "assistant_message_id": str(assistant_message_id),
                    "processing_time": processing_time,
                    "chunks_used": len(chunks),
                    "chunk_ids": [chunk["id"] for chunk in chunks],
                    "llm_metadata": response_metadata
                }
            )
            
            self.db.add(activity_log)
            self.db.commit()
            
            logger.info(f"Logged chat interaction for bot {bot_id}, session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to log conversation metadata: {e}")
            # Don't raise exception - logging failure shouldn't break chat
    
    async def create_session(
        self,
        bot_id: uuid.UUID,
        user_id: uuid.UUID,
        title: Optional[str] = None
    ) -> ConversationSession:
        """Create a new conversation session."""
        # Check permission
        if not self.permission_service.check_bot_permission(
            user_id, bot_id, "view_conversations"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to create sessions for this bot"
            )
        
        from ..schemas.conversation import ConversationSessionCreate
        session_data = ConversationSessionCreate(
            bot_id=bot_id,
            title=title or "New Conversation"
        )
        
        return self.conversation_service.create_session(user_id, session_data)
    
    async def get_session_messages(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """Get messages from a conversation session."""
        return self.conversation_service.get_session_messages(
            session_id, user_id, limit, offset
        )
    
    async def search_conversations(
        self,
        user_id: uuid.UUID,
        query: str,
        bot_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search conversations across user's accessible bots."""
        return self.conversation_service.search_conversations(
            user_id, query, bot_id, limit, offset
        )
    
    async def _send_chat_notifications(
        self,
        bot_id: uuid.UUID,
        user_id: uuid.UUID,
        user_message: Message,
        assistant_message: Message,
        session_id: uuid.UUID
    ):
        """Send real-time WebSocket notifications for chat messages."""
        try:
            # Import WebSocket service to avoid circular imports
            from .websocket_service import connection_manager
            
            # Get user info
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            # Send user message notification
            user_message_data = {
                "message_id": str(user_message.id),
                "session_id": str(session_id),
                "user_id": str(user_id),
                "username": user.username,
                "content": user_message.content,
                "role": "user",
                "timestamp": user_message.created_at.isoformat(),
                "metadata": user_message.metadata
            }
            
            await connection_manager.broadcast_to_bot_collaborators(
                bot_id=str(bot_id),
                message={
                    "type": "chat_message",
                    "bot_id": str(bot_id),
                    "data": user_message_data
                },
                exclude_user=str(user_id),
                db=self.db
            )
            
            # Send assistant message notification
            assistant_message_data = {
                "message_id": str(assistant_message.id),
                "session_id": str(session_id),
                "user_id": str(user_id),
                "username": "Assistant",
                "content": assistant_message.content,
                "role": "assistant",
                "timestamp": assistant_message.created_at.isoformat(),
                "metadata": assistant_message.metadata
            }
            
            await connection_manager.broadcast_to_bot_collaborators(
                bot_id=str(bot_id),
                message={
                    "type": "chat_message",
                    "bot_id": str(bot_id),
                    "data": assistant_message_data
                },
                db=self.db
            )
            
            logger.info(f"Sent WebSocket notifications for chat in bot {bot_id}")
            
        except Exception as e:
            logger.error(f"Failed to send chat WebSocket notifications: {e}")
            # Don't raise exception - WebSocket failure shouldn't break chat
    
    async def close(self):
        """Close all service connections and clean up resources."""
        try:
            await self.llm_service.close()
            await self.embedding_service.close()
            await self.vector_service.close()
            logger.info("Closed chat service connections")
        except Exception as e:
            logger.error(f"Error closing chat service: {e}")