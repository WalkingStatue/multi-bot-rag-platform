"""
Unit tests for the Adaptive Threshold Manager.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.adaptive_threshold_manager import (
    AdaptiveThresholdManager,
    ThresholdConfiguration,
    RetrievalContext,
    ThresholdRecommendation,
    RetrievalMetrics,
    ThresholdAdjustmentReason
)


class TestAdaptiveThresholdManager:
    """Test cases for AdaptiveThresholdManager."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def threshold_manager(self, mock_db):
        """Create threshold manager instance."""
        return AdaptiveThresholdManager(mock_db)
    
    @pytest.fixture
    def sample_context(self):
        """Sample retrieval context."""
        return RetrievalContext(
            bot_id=uuid.uuid4(),
            query_text="What is machine learning?",
            content_type="technical",
            document_count=50,
            avg_document_length=2000.0
        )
    
    def test_initialization(self, threshold_manager):
        """Test threshold manager initialization."""
        assert threshold_manager is not None
        assert len(threshold_manager._threshold_configs) > 0
        assert "openai" in threshold_manager._threshold_configs
        assert "gemini" in threshold_manager._threshold_configs
        assert "anthropic" in threshold_manager._threshold_configs
        assert "openrouter" in threshold_manager._threshold_configs
    
    def test_get_provider_threshold_config_openai(self, threshold_manager):
        """Test getting OpenAI threshold configuration."""
        config = threshold_manager.get_provider_threshold_config("openai")
        
        assert config.provider == "openai"
        assert config.default_threshold == 0.7
        assert config.min_threshold == 0.3
        assert config.max_threshold == 0.95
        assert config.adjustment_step == 0.1
        assert len(config.retry_thresholds) > 0
        assert "technical" in config.content_type_adjustments
    
    def test_get_provider_threshold_config_gemini(self, threshold_manager):
        """Test getting Gemini threshold configuration."""
        config = threshold_manager.get_provider_threshold_config("gemini")
        
        assert config.provider == "gemini"
        assert config.default_threshold == 0.01  # Very low for Gemini
        assert config.min_threshold == 0.001
        assert config.max_threshold == 0.5
        assert config.adjustment_step == 0.01
        assert None in config.retry_thresholds  # Should include no-threshold fallback
    
    def test_get_provider_threshold_config_invalid_provider(self, threshold_manager):
        """Test getting configuration for invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            threshold_manager.get_provider_threshold_config("invalid_provider")
    
    def test_calculate_optimal_threshold_base(self, threshold_manager, sample_context):
        """Test basic optimal threshold calculation."""
        threshold = threshold_manager.calculate_optimal_threshold(
            "openai", "text-embedding-3-small", sample_context
        )
        
        # Should be base threshold + technical adjustment
        expected = 0.7 + 0.05  # base + technical adjustment
        assert threshold == expected
    
    def test_calculate_optimal_threshold_with_document_adjustments(self, threshold_manager):
        """Test threshold calculation with document count adjustments."""
        context = RetrievalContext(
            bot_id=uuid.uuid4(),
            query_text="Test query",
            content_type="general",
            document_count=150,  # > 100, should get adjustment
            avg_document_length=3000.0  # > 2000, should get adjustment
        )
        
        threshold = threshold_manager.calculate_optimal_threshold(
            "openai", "text-embedding-3-small", context
        )
        
        # Should be base + document count adjustment - document length adjustment
        # 0.7 + 0.02 - 0.02 = 0.7
        assert threshold == 0.7
    
    def test_calculate_optimal_threshold_gemini_special_case(self, threshold_manager, sample_context):
        """Test threshold calculation for Gemini provider."""
        threshold = threshold_manager.calculate_optimal_threshold(
            "gemini", "text-embedding-004", sample_context
        )
        
        # Should be very low base + technical adjustment
        expected = 0.01 + 0.005  # base + technical adjustment
        assert threshold == expected
    
    def test_get_retry_thresholds_default(self, threshold_manager):
        """Test getting default retry thresholds."""
        thresholds = threshold_manager.get_retry_thresholds("openai", "text-embedding-3-small")
        
        assert len(thresholds) > 0
        assert thresholds[0] == 0.7  # Default threshold
        assert None in thresholds  # Should include no-threshold fallback
        
        # Should be in descending order (except None)
        non_none_thresholds = [t for t in thresholds if t is not None]
        assert non_none_thresholds == sorted(non_none_thresholds, reverse=True)
    
    def test_get_retry_thresholds_custom_initial(self, threshold_manager):
        """Test getting retry thresholds with custom initial threshold."""
        initial_threshold = 0.8
        thresholds = threshold_manager.get_retry_thresholds(
            "openai", "text-embedding-3-small", initial_threshold
        )
        
        assert thresholds[0] == initial_threshold
        assert len(thresholds) > 1
        assert None in thresholds  # Should include no-threshold fallback
        
        # Should be in descending order (except None)
        non_none_thresholds = [t for t in thresholds if t is not None]
        assert non_none_thresholds == sorted(non_none_thresholds, reverse=True)
    
    def test_validate_threshold_configuration_valid(self, threshold_manager):
        """Test validating a valid threshold configuration."""
        is_valid, issues = threshold_manager.validate_threshold_configuration(
            "openai", "text-embedding-3-small", 0.7
        )
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_threshold_configuration_too_low(self, threshold_manager):
        """Test validating a threshold that's too low."""
        is_valid, issues = threshold_manager.validate_threshold_configuration(
            "openai", "text-embedding-3-small", 0.1  # Below minimum of 0.3
        )
        
        assert is_valid is False
        assert len(issues) > 0
        assert "below minimum" in issues[0]
    
    def test_validate_threshold_configuration_too_high(self, threshold_manager):
        """Test validating a threshold that's too high."""
        is_valid, issues = threshold_manager.validate_threshold_configuration(
            "openai", "text-embedding-3-small", 0.99  # Above maximum of 0.95
        )
        
        assert is_valid is False
        assert len(issues) > 0
        assert "above maximum" in issues[0]
    
    def test_validate_threshold_configuration_gemini_warning(self, threshold_manager):
        """Test validating a high threshold for Gemini (should warn)."""
        is_valid, issues = threshold_manager.validate_threshold_configuration(
            "gemini", "text-embedding-004", 0.2  # High for Gemini
        )
        
        assert is_valid is True  # Still valid but with warnings
        assert len(issues) > 0
        assert "Gemini embeddings typically require very low thresholds" in issues[0]
    
    @pytest.mark.asyncio
    async def test_track_retrieval_performance(self, threshold_manager, mock_db):
        """Test tracking retrieval performance."""
        bot_id = uuid.uuid4()
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        await threshold_manager.track_retrieval_performance(
            bot_id=bot_id,
            threshold_used=0.7,
            provider="openai",
            model="text-embedding-3-small",
            query_text="Test query",
            results_found=3,
            result_scores=[0.8, 0.7, 0.6],
            processing_time=0.5,
            success=True,
            adjustment_reason=ThresholdAdjustmentReason.NO_RESULTS_FOUND.value
        )
        
        # Verify database operations were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify cache was updated
        cache_key = f"{bot_id}_openai_text-embedding-3-small"
        assert cache_key in threshold_manager._performance_cache
        assert len(threshold_manager._performance_cache[cache_key]) == 1
    
    def test_get_supported_providers(self, threshold_manager):
        """Test getting list of supported providers."""
        providers = threshold_manager.get_supported_providers()
        
        assert "openai" in providers
        assert "gemini" in providers
        assert "anthropic" in providers
        assert "openrouter" in providers
        assert len(providers) >= 4
    
    def test_get_provider_info(self, threshold_manager):
        """Test getting provider information."""
        info = threshold_manager.get_provider_info("openai")
        
        assert info["provider"] == "openai"
        assert "default_threshold" in info
        assert "threshold_range" in info
        assert "retry_thresholds" in info
        assert "content_type_adjustments" in info
        assert "metadata" in info
    
    def test_get_provider_info_invalid_provider(self, threshold_manager):
        """Test getting info for invalid provider."""
        info = threshold_manager.get_provider_info("invalid_provider")
        
        assert info == {}  # Should return empty dict for invalid provider
    
    @pytest.mark.asyncio
    async def test_get_threshold_recommendations_insufficient_data(self, threshold_manager, mock_db):
        """Test getting recommendations with insufficient data."""
        bot_id = uuid.uuid4()
        
        # Mock database query to return empty results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        recommendations = await threshold_manager.get_threshold_recommendations(
            bot_id, "openai", "text-embedding-3-small", 7
        )
        
        assert len(recommendations) == 0
    
    def test_hash_query(self, threshold_manager):
        """Test query hashing for privacy."""
        query = "What is machine learning?"
        hash1 = threshold_manager._hash_query(query)
        hash2 = threshold_manager._hash_query(query)
        
        # Same query should produce same hash
        assert hash1 == hash2
        
        # Different query should produce different hash
        hash3 = threshold_manager._hash_query("Different query")
        assert hash1 != hash3
        
        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64
    
    def test_calculate_std_dev(self, threshold_manager):
        """Test standard deviation calculation."""
        scores = [0.8, 0.7, 0.6, 0.9, 0.5]
        std_dev = threshold_manager._calculate_std_dev(scores)
        
        assert std_dev > 0
        assert isinstance(std_dev, float)
        
        # Test with single score
        single_score_std = threshold_manager._calculate_std_dev([0.7])
        assert single_score_std == 0.0
        
        # Test with identical scores
        identical_scores_std = threshold_manager._calculate_std_dev([0.7, 0.7, 0.7])
        assert identical_scores_std == 0.0


class TestThresholdConfiguration:
    """Test cases for ThresholdConfiguration dataclass."""
    
    def test_threshold_configuration_creation(self):
        """Test creating a threshold configuration."""
        config = ThresholdConfiguration(
            provider="test_provider",
            model="test_model",
            default_threshold=0.5,
            min_threshold=0.1,
            max_threshold=0.9,
            adjustment_step=0.1,
            retry_thresholds=[0.5, 0.3, 0.1],
            content_type_adjustments={"technical": 0.05},
            metadata={"test": "value"}
        )
        
        assert config.provider == "test_provider"
        assert config.model == "test_model"
        assert config.default_threshold == 0.5
        assert config.min_threshold == 0.1
        assert config.max_threshold == 0.9
        assert config.adjustment_step == 0.1
        assert config.retry_thresholds == [0.5, 0.3, 0.1]
        assert config.content_type_adjustments == {"technical": 0.05}
        assert config.metadata == {"test": "value"}


class TestRetrievalContext:
    """Test cases for RetrievalContext dataclass."""
    
    def test_retrieval_context_creation(self):
        """Test creating a retrieval context."""
        bot_id = uuid.uuid4()
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        context = RetrievalContext(
            bot_id=bot_id,
            query_text="Test query",
            content_type="technical",
            document_count=10,
            avg_document_length=1500.0,
            session_id=session_id,
            user_id=user_id
        )
        
        assert context.bot_id == bot_id
        assert context.query_text == "Test query"
        assert context.content_type == "technical"
        assert context.document_count == 10
        assert context.avg_document_length == 1500.0
        assert context.session_id == session_id
        assert context.user_id == user_id


class TestThresholdRecommendation:
    """Test cases for ThresholdRecommendation dataclass."""
    
    def test_threshold_recommendation_creation(self):
        """Test creating a threshold recommendation."""
        recommendation = ThresholdRecommendation(
            current_threshold=0.7,
            recommended_threshold=0.5,
            confidence=0.85,
            reason="Performance analysis shows better results",
            expected_improvement=0.15,
            metadata={"analysis_period": 7}
        )
        
        assert recommendation.current_threshold == 0.7
        assert recommendation.recommended_threshold == 0.5
        assert recommendation.confidence == 0.85
        assert recommendation.reason == "Performance analysis shows better results"
        assert recommendation.expected_improvement == 0.15
        assert recommendation.metadata == {"analysis_period": 7}


class TestRetrievalMetrics:
    """Test cases for RetrievalMetrics dataclass."""
    
    def test_retrieval_metrics_creation(self):
        """Test creating retrieval metrics."""
        bot_id = uuid.uuid4()
        timestamp = datetime.utcnow()
        
        metrics = RetrievalMetrics(
            bot_id=bot_id,
            timestamp=timestamp,
            threshold_used=0.7,
            results_found=3,
            avg_score=0.75,
            max_score=0.9,
            min_score=0.6,
            query_length=20,
            processing_time=0.5,
            success=True,
            adjustment_reason=ThresholdAdjustmentReason.NO_RESULTS_FOUND.value
        )
        
        assert metrics.bot_id == bot_id
        assert metrics.timestamp == timestamp
        assert metrics.threshold_used == 0.7
        assert metrics.results_found == 3
        assert metrics.avg_score == 0.75
        assert metrics.max_score == 0.9
        assert metrics.min_score == 0.6
        assert metrics.query_length == 20
        assert metrics.processing_time == 0.5
        assert metrics.success is True
        assert metrics.adjustment_reason == ThresholdAdjustmentReason.NO_RESULTS_FOUND.value