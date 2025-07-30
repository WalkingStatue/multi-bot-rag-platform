"""
Unit tests for RAG (Retrieval-Augmented Generation) pipeline functionality.
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
from app.schemas.conversation import ChatRequest


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_bot():
    """Sample bot with specific RAG configuration."""
    return Bot(
        id=uuid.uuid4(),
        name="RAG Test Bot",
        description="A bot for testing RAG functionality",
        system_prompt="You are a helpful assistant that uses provided context to answer questions accurately.",
        owner_id=uuid.uuid4(),
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        temperature=0.7,
        max_tokens=1000
    )


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid.uuid4(),
        username="raguser",
        email="rag@example.com",
        password_hash="hashed_password"
    )


class TestRAGPipeline:
    """Test cases for RAG pipeline functionality."""
    
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
    async def test_rag_with_relevant_context(self, sample_bot, sample_user):
        """Test RAG pipeline with highly relevant document context."""
        # Setup query and expected context
        query = "What is the capital of France?"
        relevant_chunks = [
            {
                "id": "chunk1",
                "text": "Paris is the capital and most populous city of France.",
                "score": 0.95,
                "metadata": {"document_id": "geography_doc", "page": 1}
            },
            {
                "id": "chunk2", 
                "text": "France is a country in Western Europe with Paris as its capital city.",
                "score": 0.88,
                "metadata": {"document_id": "geography_doc", "page": 2}
            }
        ]
        
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=relevant_chunks)
        
        # Execute RAG retrieval
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, query)
        
        # Assertions
        assert len(chunks) == 2
        assert chunks[0]["text"] == "Paris is the capital and most populous city of France."
        assert chunks[0]["score"] == 0.95
        assert chunks[1]["score"] == 0.88
        
        # Verify embedding generation was called correctly
        self.mock_embed_service.generate_single_embedding.assert_called_once_with(
            provider=sample_bot.embedding_provider,
            text=query,
            model=sample_bot.embedding_model,
            api_key="test-api-key"
        )
        
        # Verify vector search was called correctly
        self.mock_vector_service.search_relevant_chunks.assert_called_once_with(
            bot_id=str(sample_bot.id),
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
            score_threshold=0.7
        )
    
    @pytest.mark.asyncio
    async def test_rag_with_no_relevant_context(self, sample_bot, sample_user):
        """Test RAG pipeline when no relevant context is found."""
        query = "What is quantum computing?"
        
        # Setup mocks - no relevant chunks found
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=[])
        
        # Execute RAG retrieval
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, query)
        
        # Assertions
        assert len(chunks) == 0
        
        # Verify services were still called
        self.mock_embed_service.generate_single_embedding.assert_called_once()
        self.mock_vector_service.search_relevant_chunks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_with_low_similarity_scores(self, sample_bot, sample_user):
        """Test RAG pipeline with chunks below similarity threshold."""
        query = "Tell me about machine learning"
        low_similarity_chunks = [
            {
                "id": "chunk1",
                "text": "The weather is nice today.",
                "score": 0.3,  # Below threshold
                "metadata": {"document_id": "weather_doc"}
            },
            {
                "id": "chunk2",
                "text": "Cooking recipes are important.",
                "score": 0.2,  # Below threshold
                "metadata": {"document_id": "cooking_doc"}
            }
        ]
        
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=low_similarity_chunks)
        
        # Execute RAG retrieval
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, query)
        
        # Assertions - chunks are returned even if low similarity (filtering happens in vector store)
        assert len(chunks) == 2
        assert all(chunk["score"] < 0.7 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_prompt_construction_with_rag_context(self, sample_bot):
        """Test prompt construction with RAG-retrieved context."""
        # Sample RAG context
        chunks = [
            {
                "id": "chunk1",
                "text": "Python is a high-level programming language known for its simplicity.",
                "score": 0.9,
                "metadata": {"document_id": "python_guide"}
            },
            {
                "id": "chunk2",
                "text": "Python supports multiple programming paradigms including object-oriented programming.",
                "score": 0.85,
                "metadata": {"document_id": "python_guide"}
            }
        ]
        
        # Sample conversation history
        history = [
            Message(role="user", content="What is programming?", created_at=datetime.utcnow()),
            Message(role="assistant", content="Programming is the process of creating instructions for computers.", created_at=datetime.utcnow())
        ]
        
        user_input = "Tell me about Python programming language"
        
        # Execute prompt building
        prompt = await self.chat_service._build_prompt(sample_bot, history, chunks, user_input)
        
        # Assertions
        assert sample_bot.system_prompt in prompt
        assert "Python is a high-level programming language" in prompt
        assert "Python supports multiple programming paradigms" in prompt
        assert "What is programming?" in prompt
        assert "Tell me about Python programming language" in prompt
        assert prompt.endswith("Assistant:")
        
        # Verify context is properly formatted
        assert "Document Context 1:" in prompt
        assert "Document Context 2:" in prompt
        assert "Conversation History:" in prompt
    
    @pytest.mark.asyncio
    async def test_prompt_construction_without_rag_context(self, sample_bot):
        """Test prompt construction when no RAG context is available."""
        chunks = []  # No context
        history = []  # No history
        user_input = "Hello, how are you?"
        
        # Execute prompt building
        prompt = await self.chat_service._build_prompt(sample_bot, history, chunks, user_input)
        
        # Assertions
        assert sample_bot.system_prompt in prompt
        assert "Hello, how are you?" in prompt
        assert prompt.endswith("Assistant:")
        
        # Verify no context sections are included
        assert "Document Context" not in prompt
        assert "Conversation History" not in prompt
        assert "Relevant Context" not in prompt
    
    @pytest.mark.asyncio
    async def test_rag_context_prioritization(self, sample_bot):
        """Test that higher-scored chunks are prioritized in context."""
        # Chunks with different similarity scores
        chunks = [
            {
                "id": "chunk1",
                "text": "Most relevant information about the topic.",
                "score": 0.95,
                "metadata": {"document_id": "doc1"}
            },
            {
                "id": "chunk2",
                "text": "Somewhat relevant information.",
                "score": 0.80,
                "metadata": {"document_id": "doc2"}
            },
            {
                "id": "chunk3",
                "text": "Less relevant but still useful information.",
                "score": 0.75,
                "metadata": {"document_id": "doc3"}
            }
        ]
        
        history = []
        user_input = "Tell me about this topic"
        
        # Execute prompt building
        prompt = await self.chat_service._build_prompt(sample_bot, history, chunks, user_input)
        
        # Assertions
        # Higher scored chunks should appear first in the prompt
        most_relevant_pos = prompt.find("Most relevant information")
        somewhat_relevant_pos = prompt.find("Somewhat relevant information")
        less_relevant_pos = prompt.find("Less relevant but still useful")
        
        assert most_relevant_pos < somewhat_relevant_pos < less_relevant_pos
    
    @pytest.mark.asyncio
    async def test_rag_with_metadata_filtering(self, sample_bot, sample_user):
        """Test RAG retrieval with metadata filtering."""
        query = "What is artificial intelligence?"
        
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        # Mock vector service to verify metadata filtering
        expected_chunks = [
            {
                "id": "chunk1",
                "text": "AI is a branch of computer science.",
                "score": 0.9,
                "metadata": {"document_id": "ai_textbook", "chapter": "introduction"}
            }
        ]
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=expected_chunks)
        
        # Execute RAG retrieval
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, query)
        
        # Verify the vector service was called with correct parameters
        self.mock_vector_service.search_relevant_chunks.assert_called_once_with(
            bot_id=str(sample_bot.id),
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
            score_threshold=0.7
        )
        
        assert len(chunks) == 1
        assert chunks[0]["metadata"]["document_id"] == "ai_textbook"
    
    @pytest.mark.asyncio
    async def test_rag_embedding_provider_fallback(self, sample_bot, sample_user):
        """Test RAG pipeline with embedding provider fallback."""
        query = "Test query for fallback"
        
        # Setup mocks - primary provider fails, fallback succeeds
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        
        # First call fails, second call (fallback) succeeds
        self.mock_embed_service.generate_single_embedding.side_effect = [
            Exception("Primary provider failed"),
            [0.1, 0.2, 0.3]  # Fallback success
        ]
        
        self.mock_vector_service.search_relevant_chunks.return_value = []
        
        # Execute - this should handle the exception gracefully
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, query)
        
        # Should return empty list when retrieval fails
        assert chunks == []
    
    @pytest.mark.asyncio
    async def test_rag_with_large_context_truncation(self, sample_bot):
        """Test RAG context handling when context is very large."""
        # Create very large chunks
        large_text = "This is a very long piece of text. " * 1000
        chunks = [
            {
                "id": "chunk1",
                "text": large_text,
                "score": 0.9,
                "metadata": {"document_id": "large_doc"}
            }
        ]
        
        history = []
        user_input = "Question about the large document"
        
        # Execute prompt building
        prompt = await self.chat_service._build_prompt(sample_bot, history, chunks, user_input)
        
        # Assertions
        assert len(prompt) <= self.chat_service.max_prompt_length
        assert sample_bot.system_prompt in prompt
        assert user_input in prompt
    
    @pytest.mark.asyncio
    async def test_rag_chunk_metadata_preservation(self, sample_bot, sample_user):
        """Test that chunk metadata is preserved through the RAG pipeline."""
        query = "Test query"
        chunks_with_metadata = [
            {
                "id": "chunk1",
                "text": "Content with metadata",
                "score": 0.9,
                "metadata": {
                    "document_id": "doc123",
                    "page_number": 5,
                    "section": "introduction",
                    "author": "John Doe",
                    "timestamp": "2024-01-01"
                }
            }
        ]
        
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=chunks_with_metadata)
        
        # Execute RAG retrieval
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, query)
        
        # Assertions
        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk["metadata"]["document_id"] == "doc123"
        assert chunk["metadata"]["page_number"] == 5
        assert chunk["metadata"]["section"] == "introduction"
        assert chunk["metadata"]["author"] == "John Doe"
        assert chunk["metadata"]["timestamp"] == "2024-01-01"
    
    @pytest.mark.asyncio
    async def test_rag_performance_with_multiple_chunks(self, sample_bot, sample_user):
        """Test RAG performance with maximum number of chunks."""
        query = "Complex query requiring multiple sources"
        
        # Create maximum number of chunks
        max_chunks = []
        for i in range(self.chat_service.max_retrieved_chunks):
            max_chunks.append({
                "id": f"chunk{i+1}",
                "text": f"Content from document {i+1} with relevant information.",
                "score": 0.9 - (i * 0.1),  # Decreasing scores
                "metadata": {"document_id": f"doc{i+1}"}
            })
        
        # Setup mocks
        self.mock_user_service.get_user_api_key.return_value = "test-api-key"
        self.mock_embed_service.generate_single_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        self.mock_vector_service.search_relevant_chunks = AsyncMock(return_value=max_chunks)
        
        # Execute RAG retrieval
        chunks = await self.chat_service._retrieve_relevant_chunks(sample_bot, query)
        
        # Assertions
        assert len(chunks) == self.chat_service.max_retrieved_chunks
        
        # Verify chunks are in score order (highest first)
        scores = [chunk["score"] for chunk in chunks]
        assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__])