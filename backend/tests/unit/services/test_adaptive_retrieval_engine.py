"""
Unit tests for the Adaptive Retrieval Engine.
"""
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch

from app.services.adaptive_retrieval_engine import (
    AdaptiveRetrievalEngine,
    RetrievalResult,
    OptimizationSuggestion,
    RetrievalContext
)
from app.models.bot import Bot


class TestAdaptiveRetrievalEngine:
    """Test cases for AdaptiveRetrievalEngine."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_vector_service(self):
        """Mock vector service."""
        return Mock()
    
    @pytest.fixture
    def retrieval_engine(self, mock_db, mock_vector_service):
        """Create retrieval engine instance."""
        return AdaptiveRetrievalEngine(mock_db, mock_vector_service)
    
    @pytest.fixture
    def sample_bot(self):
        """Sample bot for testing."""
        bot = Mock(spec=Bot)
        bot.id = uuid.uuid4()
        bot.embedding_provider = "openai"
        bot.embedding_model = "text-embedding-3-small"
        return bot
    
    @pytest.fixture
    def sample_context(self):
        """Sample retrieval context."""
        return RetrievalContext(
            bot_id=uuid.uuid4(),
            query_text="What is machine learning?",
            content_type="technical",
            document_count=50
        )
    
    @pytest.fixture
    def sample_embedding(self):
        """Sample query embedding."""
        return [0.1] * 1536  # OpenAI embedding dimension
    
    def test_initialization(self, retrieval_engine):
        """Test retrieval engine initialization."""
        assert retrieval_engine is not None
        assert retrieval_engine.max_retry_attempts == 4
        assert retrieval_engine.enable_performance_tracking is True
        assert retrieval_engine.enable_adaptive_adjustment is True
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_chunks_success_first_attempt(
        self, retrieval_engine, mock_db, mock_vector_service, sample_bot, sample_context, sample_embedding
    ):
        """Test successful retrieval on first attempt."""
        # Mock database query for bot
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_bot
        mock_db.query.return_value = mock_query
        
        # Mock vector service search
        mock_chunks = [
            {"id": "1", "text": "ML is...", "score": 0.8, "metadata": {}},
            {"id": "2", "text": "Machine learning...", "score": 0.7, "metadata": {}}
        ]
        mock_vector_service.search_relevant_chunks = AsyncMock(return_value=mock_chunks)
        
        # Mock threshold manager
        with patch.object(retrieval_engine.threshold_manager, 'calculate_optimal_threshold', return_value=0.7), \
             patch.object(retrieval_engine.threshold_manager, 'get_retry_thresholds', return_value=[0.7, 0.5, 0.3]), \
             patch.object(retrieval_engine.threshold_manager, 'track_retrieval_performance', new_callable=AsyncMock):
            
            result = await retrieval_engine.retrieve_relevant_chunks(
                bot_id=sample_bot.id,
                query_embedding=sample_embedding,
                context=sample_context
            )
        
        assert result.success is True
        assert len(result.chunks) == 2
        assert result.threshold_used == 0.7
        assert result.total_attempts == 1
        assert result.fallback_used is False
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_chunks_success_after_retry(
        self, retrieval_engine, mock_db, mock_vector_service, sample_bot, sample_context, sample_embedding
    ):
        """Test successful retrieval after retry with lower threshold."""
        # Mock database query for bot
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_bot
        mock_db.query.return_value = mock_query
        
        # Mock vector service search - first call returns empty, second returns results
        mock_chunks = [
            {"id": "1", "text": "ML is...", "score": 0.4, "metadata": {}}
        ]
        mock_vector_service.search_relevant_chunks = AsyncMock(side_effect=[[], mock_chunks])
        
        # Mock threshold manager
        with patch.object(retrieval_engine.threshold_manager, 'calculate_optimal_threshold', return_value=0.7), \
             patch.object(retrieval_engine.threshold_manager, 'get_retry_thresholds', return_value=[0.7, 0.5, 0.3]), \
             patch.object(retrieval_engine.threshold_manager, 'track_retrieval_performance', new_callable=AsyncMock):
            
            result = await retrieval_engine.retrieve_relevant_chunks(
                bot_id=sample_bot.id,
                query_embedding=sample_embedding,
                context=sample_context
            )
        
        assert result.success is True
        assert len(result.chunks) == 1
        assert result.threshold_used == 0.5  # Second threshold tried
        assert result.total_attempts == 2
        assert result.fallback_used is True
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_chunks_no_results(
        self, retrieval_engine, mock_db, mock_vector_service, sample_bot, sample_context, sample_embedding
    ):
        """Test retrieval when no results are found with any threshold."""
        # Mock database query for bot
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_bot
        mock_db.query.return_value = mock_query
        
        # Mock vector service search - always returns empty
        mock_vector_service.search_relevant_chunks = AsyncMock(return_value=[])
        
        # Mock threshold manager
        with patch.object(retrieval_engine.threshold_manager, 'calculate_optimal_threshold', return_value=0.7), \
             patch.object(retrieval_engine.threshold_manager, 'get_retry_thresholds', return_value=[0.7, 0.5, 0.3]), \
             patch.object(retrieval_engine.threshold_manager, 'track_retrieval_performance', new_callable=AsyncMock):
            
            result = await retrieval_engine.retrieve_relevant_chunks(
                bot_id=sample_bot.id,
                query_embedding=sample_embedding,
                context=sample_context
            )
        
        assert result.success is True  # Success but no results
        assert len(result.chunks) == 0
        assert result.total_attempts == 3  # Tried all thresholds
        assert result.error is None
        assert "no_relevant_content" in result.metadata["reason"]
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_chunks_bot_not_found(
        self, retrieval_engine, mock_db, mock_vector_service, sample_context, sample_embedding
    ):
        """Test retrieval when bot is not found."""
        # Mock database query for bot - returns None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = await retrieval_engine.retrieve_relevant_chunks(
            bot_id=uuid.uuid4(),
            query_embedding=sample_embedding,
            context=sample_context
        )
        
        assert result.success is False
        assert len(result.chunks) == 0
        assert result.error == "Bot not found"
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_chunks_with_custom_threshold(
        self, retrieval_engine, mock_db, mock_vector_service, sample_bot, sample_context, sample_embedding
    ):
        """Test retrieval with custom threshold."""
        # Mock database query for bot
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_bot
        mock_db.query.return_value = mock_query
        
        # Mock vector service search
        mock_chunks = [{"id": "1", "text": "ML is...", "score": 0.6, "metadata": {}}]
        mock_vector_service.search_relevant_chunks = AsyncMock(return_value=mock_chunks)
        
        # Mock threshold manager
        with patch.object(retrieval_engine.threshold_manager, 'validate_threshold_configuration', return_value=(True, [])), \
             patch.object(retrieval_engine.threshold_manager, 'get_retry_thresholds', return_value=[0.6, 0.4, 0.2]), \
             patch.object(retrieval_engine.threshold_manager, 'track_retrieval_performance', new_callable=AsyncMock):
            
            result = await retrieval_engine.retrieve_relevant_chunks(
                bot_id=sample_bot.id,
                query_embedding=sample_embedding,
                context=sample_context,
                custom_threshold=0.6
            )
        
        assert result.success is True
        assert len(result.chunks) == 1
        assert result.threshold_used == 0.6
        assert result.metadata["custom_threshold_used"] is True
    
    @pytest.mark.asyncio
    async def test_optimize_retrieval_parameters(
        self, retrieval_engine, mock_db, sample_bot
    ):
        """Test optimization parameter suggestions."""
        # Mock database query for bot
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_bot
        mock_db.query.return_value = mock_query
        
        # Mock document count query
        mock_doc_query = Mock()
        mock_doc_query.filter.return_value = mock_doc_query
        mock_doc_query.count.return_value = 2  # Few documents
        mock_db.query.return_value = mock_doc_query
        
        # Mock threshold manager recommendations
        mock_recommendations = [
            Mock(
                suggestion_type="similarity_threshold",
                current_threshold=0.7,
                recommended_threshold=0.5,
                reason="Better performance",
                confidence=0.8,
                metadata={}
            )
        ]
        
        with patch.object(retrieval_engine.threshold_manager, 'get_threshold_recommendations', 
                         new_callable=AsyncMock, return_value=mock_recommendations):
            
            suggestions = await retrieval_engine.optimize_retrieval_parameters(sample_bot.id)
        
        assert len(suggestions) >= 1  # At least threshold recommendation
        
        # Should include suggestion about few documents
        doc_suggestions = [s for s in suggestions if s.suggestion_type == "document_collection"]
        assert len(doc_suggestions) > 0
        assert "Add more documents" in doc_suggestions[0].suggested_value
    
    def test_get_threshold_info(self, retrieval_engine):
        """Test getting threshold information."""
        with patch.object(retrieval_engine.threshold_manager, 'get_provider_info', 
                         return_value={"provider": "openai", "default_threshold": 0.7}):
            
            info = retrieval_engine.get_threshold_info("openai", "text-embedding-3-small")
        
        assert "provider" in info
        assert info["provider"] == "openai"
    
    def test_calculate_adaptive_threshold(self, retrieval_engine):
        """Test calculating adaptive threshold."""
        with patch.object(retrieval_engine.threshold_manager, 'calculate_optimal_threshold', 
                         return_value=0.75):
            
            threshold = retrieval_engine.calculate_adaptive_threshold(
                provider="openai",
                model="text-embedding-3-small",
                content_type="technical",
                document_count=100,
                avg_document_length=2000.0
            )
        
        assert threshold == 0.75
    
    @pytest.mark.asyncio
    async def test_get_performance_summary_no_data(self, retrieval_engine, mock_db):
        """Test getting performance summary with no data."""
        # Mock database query to return empty results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        summary = await retrieval_engine.get_performance_summary(uuid.uuid4())
        
        assert summary["total_queries"] == 0
        assert summary["success_rate"] == 0.0
        assert summary["performance_trend"] == "insufficient_data"
    
    @pytest.mark.asyncio
    async def test_get_performance_summary_with_data(self, retrieval_engine, mock_db):
        """Test getting performance summary with data."""
        # Mock performance logs
        mock_logs = [
            Mock(success=True, results_found=3, processing_time=0.5, threshold_used=0.7),
            Mock(success=True, results_found=2, processing_time=0.3, threshold_used=0.7),
            Mock(success=False, results_found=0, processing_time=0.2, threshold_used=0.5)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_logs
        mock_db.query.return_value = mock_query
        
        summary = await retrieval_engine.get_performance_summary(uuid.uuid4())
        
        assert summary["total_queries"] == 3
        assert summary["success_rate"] == 2/3  # 2 successful out of 3
        assert summary["avg_results_per_query"] == 5/3  # (3+2+0)/3
        assert summary["most_used_threshold"] == 0.7  # Used twice


class TestRetrievalResult:
    """Test cases for RetrievalResult dataclass."""
    
    def test_retrieval_result_creation(self):
        """Test creating a retrieval result."""
        chunks = [{"id": "1", "text": "test", "score": 0.8}]
        metadata = {"provider": "openai"}
        
        result = RetrievalResult(
            success=True,
            chunks=chunks,
            threshold_used=0.7,
            total_attempts=2,
            processing_time=0.5,
            metadata=metadata,
            fallback_used=True,
            error=None
        )
        
        assert result.success is True
        assert result.chunks == chunks
        assert result.threshold_used == 0.7
        assert result.total_attempts == 2
        assert result.processing_time == 0.5
        assert result.metadata == metadata
        assert result.fallback_used is True
        assert result.error is None


class TestOptimizationSuggestion:
    """Test cases for OptimizationSuggestion dataclass."""
    
    def test_optimization_suggestion_creation(self):
        """Test creating an optimization suggestion."""
        metadata = {"analysis_period": 7}
        
        suggestion = OptimizationSuggestion(
            suggestion_type="similarity_threshold",
            current_value=0.7,
            suggested_value=0.5,
            expected_improvement="Better retrieval performance",
            confidence=0.85,
            metadata=metadata
        )
        
        assert suggestion.suggestion_type == "similarity_threshold"
        assert suggestion.current_value == 0.7
        assert suggestion.suggested_value == 0.5
        assert suggestion.expected_improvement == "Better retrieval performance"
        assert suggestion.confidence == 0.85
        assert suggestion.metadata == metadata