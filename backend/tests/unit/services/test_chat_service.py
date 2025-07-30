"""
Unit tests for chat service with RAG integration.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.services.chat_service import ChatService
from app.models.bot import Bot
from app.models.user import User
from app.models.conversation import ConversationSession, Message
from app.schemas.conversation import ChatRequest, ChatResponse


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )


@pytest.fixture
def sample_bot():
    """Sample bot for testing."""
    return Bot(
        id=uuid.uuid4(),
        name="Test Bot",
        description="A test bot",
        system_prompt="You are a helpful assistant.",
        owner_id=uuid.uuid4(),
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        temperature=0.7,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )


@pytest.fixture
def sample_session():
    """Sample conversation session for testing."""
    return ConversationSession(
        id=uuid.uuid4(),
        bot_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Test Session",
        is_shared=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return ChatRequest(
        message="Hello, how are you?",
        session_id=None
    )


class TestChatService:
    """Test cases for ChatService."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, mock_db):
        """Set up test method with mocked dependencies."""
        self.db = mock_db
        
        # Mock all service dependencies
        with patch('app.services.chat_service.ConversationService') as mock_conv_service, \
             patch('app.services.chat_service.PermissionService') as mock_perm_service, \
             patch('app.services.chat_service.LLMProviderService') as mock_llm_service, \
             patch('app.services.chat_service.EmbeddingProviderService') as mock_embed_service, \
             patch('app.services.chat_service.VectorService') as mock_vector_service, \
             patch('app.services.chat_service.UserService') as mock_user_service:
            
            self.chat_service = ChatService(self.db)
            
            # Store mocked services for test access
            self.mock_conv_service = self.chat_service.conversation_service
            self.mock_perm_service = self.chat_service.permission_service
            self.mock_llm_service = self.chat_service.llm_service
            self.mock_embed_service = self.chat_service.embedding_service
            self.mock_vector_service = self.chat_service.vector_service
            self.mock_user_service = self.chat_service.user_service
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, sample_user, sample_bot, sample_session, sample_chat_request):
        """Test successful message processing through RAG pipeline."""
        # Setup mocks
        self.mock_perm_service.check_bot_permission.return_value = True
        self.db.query.return_value.filter.return_value.first.return_value = sample_bot
        
        # Mock session creation
        self.mock_conv_service.create_session.return_value = sample_session
        
        # Mock message storage
        user_message = Message(
            id=uuid.uuid4(),
            session_id=sample_session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="user",
            content=sample_chat_request.message,
            created_at=datetime.utcnow()
        )
        assistant_message = Message(
            id=uuid.uuid4(),
            session_id=sample_session.id,
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="assistant",
            content="Hello! I'm doing well, thank you for asking.",
            created_at=datetime.utcnow()
        )
        
        self.mock_conv_service.add_message.side_effect = [user_message, assistant_message]
        
        # Mock RAG components
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        relevant_chunks = [
            {
                "id": "chunk1",
                "text": "This is relevant context",
                "score": 0.8,
                "metadata": {"document_id": "doc1"}
            }
        ]
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=relevant_chunks)
        
        # Mock conversation history
        self.mock_conv_service.get_session_messages.return_value = []
        
        # Mock LLM response
        self.mock_llm_service.generate_response = AsyncMock(return_value="Hello! I'm doing well, thank you for asking.")
        
        # Execute
        response = await self.chat_service.process_message(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            chat_request=sample_chat_request
        )
        
        # Assertions
        assert isinstance(response, ChatResponse)
        assert response.message == "Hello! I'm doing well, thank you for asking."
        assert response.session_id == sample_session.id
        assert len(response.chunks_used) == 1
        assert response.processing_time > 0
        assert "user_message_id" in response.metadata
        assert "assistant_message_id" in response.metadata
        
        # Verify service calls
        self.mock_perm_service.check_bot_permission.assert_called_once_with(
            sample_user.id, sample_bot.id, "view_conversations"
        )
        self.mock_embed_service.generate_single_embedding.assert_called_once()
        self.mock_vector_service.search_relevant_chunks.assert_called_once()
        self.mock_llm_service.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_permission_denied(self, sample_user, sample_bot, sample_chat_request):
        """Test message processing with permission denied."""
        # Setup mocks
        self.mock_perm_service.check_bot_permission.return_value = False
        
        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            await self.chat_service.process_message(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                chat_request=sample_chat_request
            )
        
        assert "permission" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_process_message_bot_not_found(self, sample_user, sample_chat_request):
        """Test message processing with bot not found."""
        # Setup mocks
        self.mock_perm_service.check_bot_permission.return_value = True
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            await self.chat_service.process_message(
                bot_id=uuid.uuid4(),
                user_id=sample_user.id,
                chat_request=sample_chat_request
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_process_message_with_existing_session(self, sample_user, sample_bot, sample_session):
        """Test message processing with existing session."""
        chat_request = ChatRequest(
            message="Follow-up message",
            session_id=sample_session.id
        )
        
        # Setup mocks
        self.mock_perm_service.check_bot_permission.return_value = True
        self.db.query.return_value.filter.return_value.first.return_value = sample_bot
        self.mock_conv_service.get_session.return_value = sample_session
        
        # Mock other components
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=[])
        self.mock_conv_service.get_session_messages.return_value = []
        self.mock_llm_service.generate_response = AsyncMock(return_value="This is a follow-up response.")
        
        # Mock message storage
        user_message = Message(id=uuid.uuid4(), role="user", content=chat_request.message)
        assistant_message = Message(id=uuid.uuid4(), role="assistant", content="This is a follow-up response.")
        self.mock_conv_service.add_message.side_effect = [user_message, assistant_message]
        
        # Execute
        response = await self.chat_service.process_message(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            chat_request=chat_request
        )
        
        # Assertions
        assert response.session_id == sample_session.id
        self.mock_conv_service.get_session.assert_called_once_with(sample_session.id, sample_user.id)
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_chunks_success(self, sample_bot):
        """Test successful retrieval of relevant chunks."""
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        expected_chunks = [
            {
                "id": "chunk1",
                "text": "Relevant context 1",
                "score": 0.9,
                "metadata": {"document_id": "doc1"}
            },
            {
                "id": "chunk2",
                "text": "Relevant context 2",
                "score": 0.8,
                "metadata": {"document_id": "doc2"}
            }
        ]
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=expected_chunks)
        
        # Execute
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, "test query")
        
        # Assertions
        assert len(chunks) == 2
        assert chunks[0]["text"] == "Relevant context 1"
        assert chunks[1]["text"] == "Relevant context 2"
        
        self.mock_embed_service.generate_single_embedding.assert_called_once_with(
            provider=sample_bot.embedding_provider,
            text="test query",
            model=sample_bot.embedding_model,
            api_key="test-api-key"
        )
        
        self.mock_vector_service.search_relevant_chunks.assert_called_once_with(
            bot_id=str(sample_bot.id),
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,  # default max_retrieved_chunks
            score_threshold=0.7  # default similarity_threshold
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_chunks_failure_returns_empty(self, sample_bot):
        """Test that chunk retrieval failure returns empty list instead of raising."""
        # Setup mocks to fail
        self.mock_user_service.get_user_api_key.side_effect = Exception("API key error")
        
        # Execute
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, "test query")
        
        # Assertions
        assert chunks == []
    
    @pytest.mark.asyncio
    async def test_build_prompt_with_context_and_history(self, sample_bot):
        """Test prompt building with context and conversation history."""
        # Sample data
        chunks = [
            {"id": "chunk1", "text": "Context 1", "metadata": {}},
            {"id": "chunk2", "text": "Context 2", "metadata": {}}
        ]
        
        history = [
            Message(role="user", content="Previous question", created_at=datetime.utcnow()),
            Message(role="assistant", content="Previous answer", created_at=datetime.utcnow())
        ]
        
        user_input = "Current question"
        
        # Execute
        prompt = await self.chat_service._build_prompt(sample_bot, history, chunks, user_input)
        
        # Assertions
        assert sample_bot.system_prompt in prompt
        assert "Context 1" in prompt
        assert "Context 2" in prompt
        assert "Previous question" in prompt
        assert "Previous answer" in prompt
        assert "Current question" in prompt
        assert prompt.endswith("Assistant:")
    
    @pytest.mark.asyncio
    async def test_build_prompt_without_context(self, sample_bot):
        """Test prompt building without document context."""
        history = []
        chunks = []
        user_input = "Simple question"
        
        # Execute
        prompt = await self.chat_service._build_prompt(sample_bot, history, chunks, user_input)
        
        # Assertions
        assert sample_bot.system_prompt in prompt
        assert "Simple question" in prompt
        assert "Context" not in prompt
        assert "History" not in prompt
    
    @pytest.mark.asyncio
    async def test_build_prompt_truncation(self, sample_bot):
        """Test prompt truncation when exceeding max length."""
        # Create very long content
        long_text = "Very long text " * 1000
        chunks = [{"id": "chunk1", "text": long_text, "metadata": {}}]
        history = [Message(role="user", content=long_text, created_at=datetime.utcnow())]
        user_input = "Question"
        
        # Execute
        prompt = await self.chat_service._build_prompt(sample_bot, history, chunks, user_input)
        
        # Assertions
        assert len(prompt) <= self.chat_service.max_prompt_length
        assert sample_bot.system_prompt in prompt
        assert "Question" in prompt
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, sample_bot, sample_user):
        """Test successful response generation."""
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_llm_service.generate_response = AsyncMock(return_value="Generated response")
        
        prompt = "Test prompt"
        
        # Execute
        response_text, metadata = await self.chat_service._generate_response(
            sample_bot, sample_user.id, prompt
        )
        
        # Assertions
        assert response_text == "Generated response"
        assert metadata["llm_provider"] == sample_bot.llm_provider
        assert metadata["llm_model"] == sample_bot.llm_model
        assert "llm_config" in metadata
        assert "response_length" in metadata
        
        # Verify LLM service call
        expected_config = {
            "temperature": sample_bot.temperature,
            "max_tokens": sample_bot.max_tokens,
            "top_p": sample_bot.top_p,
            "frequency_penalty": sample_bot.frequency_penalty,
            "presence_penalty": sample_bot.presence_penalty
        }
        
        self.mock_llm_service.generate_response.assert_called_once_with(
            provider=sample_bot.llm_provider,
            model=sample_bot.llm_model,
            prompt=prompt,
            api_key="test-api-key",
            config=expected_config
        )
    
    @pytest.mark.asyncio
    async def test_generate_response_no_api_key(self, sample_bot, sample_user):
        """Test response generation with missing API key."""
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = None
        
        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            await self.chat_service._generate_response(
                sample_bot, sample_user.id, "test prompt"
            )
        
        assert "api key" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, sample_user, sample_bot):
        """Test successful session creation."""
        # Setup mocks
        self.mock_perm_service.check_bot_permission.return_value = True
        expected_session = ConversationSession(
            id=uuid.uuid4(),
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Test Session"
        )
        self.mock_conv_service.create_session.return_value = expected_session
        
        # Execute
        session = await self.chat_service.create_session(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            title="Test Session"
        )
        
        # Assertions
        assert session == expected_session
        self.mock_perm_service.check_bot_permission.assert_called_once_with(
            sample_user.id, sample_bot.id, "view_conversations"
        )
    
    @pytest.mark.asyncio
    async def test_create_session_permission_denied(self, sample_user, sample_bot):
        """Test session creation with permission denied."""
        # Setup mocks
        self.mock_perm_service.check_bot_permission.return_value = False
        
        # Execute and assert
        with pytest.raises(Exception) as exc_info:
            await self.chat_service.create_session(
                bot_id=sample_bot.id,
                user_id=sample_user.id
            )
        
        assert "permission" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_session_messages(self, sample_user, sample_session):
        """Test getting session messages."""
        # Setup mocks
        expected_messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!")
        ]
        self.mock_conv_service.get_session_messages.return_value = expected_messages
        
        # Execute
        messages = await self.chat_service.get_session_messages(
            session_id=sample_session.id,
            user_id=sample_user.id,
            limit=50,
            offset=0
        )
        
        # Assertions
        assert messages == expected_messages
        self.mock_conv_service.get_session_messages.assert_called_once_with(
            sample_session.id, sample_user.id, 50, 0
        )
    
    @pytest.mark.asyncio
    async def test_search_conversations(self, sample_user):
        """Test conversation search."""
        # Setup mocks
        expected_results = [
            {"message_id": "msg1", "content": "Test message 1"},
            {"message_id": "msg2", "content": "Test message 2"}
        ]
        self.mock_conv_service.search_conversations.return_value = expected_results
        
        # Execute
        results = await self.chat_service.search_conversations(
            user_id=sample_user.id,
            query="test query",
            bot_id=None,
            limit=50,
            offset=0
        )
        
        # Assertions
        assert results == expected_results
        self.mock_conv_service.search_conversations.assert_called_once_with(
            sample_user.id, "test query", None, 50, 0
        )
    
    @pytest.mark.asyncio
    async def test_close_services(self):
        """Test closing all service connections."""
        # Mock close methods
        self.mock_llm_service.close = AsyncMock()
        self.mock_embed_service.close = AsyncMock()
        self.mock_vector_service.close = AsyncMock()
        
        # Execute
        await self.chat_service.close()
        
        # Assertions
        self.mock_llm_service.close.assert_called_once()
        self.mock_embed_service.close.assert_called_once()
        self.mock_vector_service.close.assert_called_once()


class TestChatServiceIntegration:
    """Integration tests for ChatService with real-like scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_rag_pipeline_integration(self, mock_db):
        """Test the complete RAG pipeline integration."""
        # This would be a more comprehensive integration test
        # that tests the full flow with more realistic data
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_chat_processing(self, mock_db):
        """Test handling multiple concurrent chat requests."""
        # This would test the service's ability to handle
        # multiple simultaneous chat requests
        pass
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self, mock_db):
        """Test various error recovery scenarios."""
        # This would test how the service handles various
        # failure modes and recovers gracefully
        pass


if __name__ == "__main__":
    pytest.main([__file__])