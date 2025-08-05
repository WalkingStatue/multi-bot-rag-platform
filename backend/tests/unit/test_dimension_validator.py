"""
Unit tests for DimensionValidator service.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.dimension_validator import (
    DimensionValidator,
    DimensionValidationResult,
    CollectionDimensionInfo,
    DimensionMismatchType
)
from app.models.bot import Bot
from app.models.collection_metadata import CollectionMetadata, EmbeddingConfigurationHistory


class TestDimensionValidator:
    """Test cases for DimensionValidator."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        mock_service = Mock()
        mock_service.validate_model_for_provider = Mock(return_value=True)
        mock_service.get_embedding_dimension = Mock(return_value=1536)
        mock_service.get_available_models = Mock(return_value=["text-embedding-3-small", "text-embedding-ada-002"])
        mock_service.get_supported_providers = Mock(return_value=["openai", "gemini"])
        return mock_service
    
    @pytest.fixture
    def mock_vector_service(self):
        """Mock vector service."""
        mock_service = Mock()
        mock_service.vector_store = Mock()
        mock_service.vector_store.collection_exists = AsyncMock(return_value=True)
        mock_service.get_bot_collection_stats = AsyncMock(return_value={
            'config': {'vector_size': 1536},
            'points_count': 100,
            'status': 'green'
        })
        return mock_service
    
    @pytest.fixture
    def sample_bot(self):
        """Sample bot for testing."""
        bot = Bot(
            id=uuid.uuid4(),
            name="Test Bot",
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
            owner_id=uuid.uuid4()
        )
        return bot
    
    @pytest.fixture
    def dimension_validator(self, mock_db, mock_embedding_service, mock_vector_service):
        """DimensionValidator instance with mocked dependencies."""
        with patch('app.services.dimension_validator.EmbeddingProviderService', return_value=mock_embedding_service), \
             patch('app.services.dimension_validator.VectorService', return_value=mock_vector_service):
            validator = DimensionValidator(mock_db)
            return validator
    
    @pytest.mark.asyncio
    async def test_validate_dimension_compatibility_success(self, dimension_validator, mock_db, sample_bot):
        """Test successful dimension compatibility validation."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
        
        # Execute
        result = await dimension_validator.validate_dimension_compatibility(
            sample_bot.id, "openai", "text-embedding-3-small"
        )
        
        # Assert
        assert result.is_valid is True
        assert result.dimension_match is True
        assert result.current_dimension == 1536
        assert result.target_dimension == 1536
        assert len(result.issues or []) == 0
    
    @pytest.mark.asyncio
    async def test_validate_dimension_compatibility_mismatch(self, dimension_validator, mock_db, sample_bot):
        """Test dimension compatibility validation with mismatch."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
        dimension_validator.embedding_service.get_embedding_dimension.side_effect = [1536, 768]  # Different dimensions
        
        # Execute
        result = await dimension_validator.validate_dimension_compatibility(
            sample_bot.id, "gemini", "text-embedding-004"
        )
        
        # Assert
        assert result.is_valid is True  # Valid but requires migration
        assert result.dimension_match is False
        assert result.current_dimension == 1536
        assert result.target_dimension == 768
        assert "Dimension mismatch" in str(result.issues)
        assert "Migration will be required" in str(result.recommendations)
    
    @pytest.mark.asyncio
    async def test_validate_dimension_compatibility_invalid_model(self, dimension_validator, mock_db, sample_bot):
        """Test validation with invalid model."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
        dimension_validator.embedding_service.validate_model_for_provider.return_value = False
        dimension_validator.embedding_service.get_available_models.return_value = ["valid-model-1", "valid-model-2"]
        
        # Execute
        result = await dimension_validator.validate_dimension_compatibility(
            sample_bot.id, "openai", "invalid-model"
        )
        
        # Assert
        assert result.is_valid is False
        assert "not available for provider" in str(result.issues)
        assert "Available models" in str(result.recommendations)
    
    @pytest.mark.asyncio
    async def test_validate_dimension_compatibility_bot_not_found(self, dimension_validator, mock_db):
        """Test validation when bot is not found."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await dimension_validator.validate_dimension_compatibility(
            uuid.uuid4(), "openai", "text-embedding-3-small"
        )
        
        # Assert
        assert result.is_valid is False
        assert "Bot not found" in result.issues
    
    @pytest.mark.asyncio
    async def test_detect_dimension_mismatches(self, dimension_validator, mock_db, sample_bot):
        """Test detection of dimension mismatches."""
        # Setup
        mock_db.query.return_value.all.return_value = [sample_bot]
        dimension_validator.vector_service.get_bot_collection_stats.return_value = {
            'config': {'vector_size': 768},  # Different from configured 1536
            'points_count': 100
        }
        
        # Execute
        mismatches = await dimension_validator.detect_dimension_mismatches()
        
        # Assert
        assert len(mismatches) == 1
        assert mismatches[0].dimension_mismatch is True
        assert mismatches[0].stored_dimension == 768
        assert mismatches[0].configured_dimension == 1536
    
    @pytest.mark.asyncio
    async def test_detect_dimension_mismatches_no_issues(self, dimension_validator, mock_db, sample_bot):
        """Test detection when no mismatches exist."""
        # Setup
        mock_db.query.return_value.all.return_value = [sample_bot]
        dimension_validator.vector_service.get_bot_collection_stats.return_value = {
            'config': {'vector_size': 1536},  # Matches configured dimension
            'points_count': 100
        }
        
        # Execute
        mismatches = await dimension_validator.detect_dimension_mismatches()
        
        # Assert
        assert len(mismatches) == 0
    
    @pytest.mark.asyncio
    async def test_validate_embedding_configuration_change(self, dimension_validator, mock_db, sample_bot):
        """Test validation of embedding configuration change."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Execute
        result = await dimension_validator.validate_embedding_configuration_change(
            sample_bot.id, "gemini", "text-embedding-004", "Testing new provider"
        )
        
        # Assert
        assert result.is_valid is True
        mock_db.add.assert_called_once()  # Configuration history should be recorded
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_collection_metadata(self, dimension_validator, mock_db):
        """Test storing collection metadata."""
        # Setup
        bot_id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing metadata
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Execute
        result = await dimension_validator.store_collection_metadata(
            bot_id, "openai", "text-embedding-3-small", 1536, 100
        )
        
        # Assert
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_collection_metadata_update_existing(self, dimension_validator, mock_db):
        """Test updating existing collection metadata."""
        # Setup
        bot_id = uuid.uuid4()
        existing_metadata = CollectionMetadata(
            bot_id=bot_id,
            collection_name=str(bot_id),
            embedding_provider="openai",
            embedding_model="text-embedding-ada-002",
            embedding_dimension=1536
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_metadata
        mock_db.commit = Mock()
        
        # Execute
        result = await dimension_validator.store_collection_metadata(
            bot_id, "openai", "text-embedding-3-small", 1536, 150
        )
        
        # Assert
        assert result is True
        assert existing_metadata.embedding_model == "text-embedding-3-small"
        assert existing_metadata.points_count == 150
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collection_metadata(self, dimension_validator, mock_db):
        """Test retrieving collection metadata."""
        # Setup
        bot_id = uuid.uuid4()
        metadata = Mock()
        metadata.bot_id = bot_id
        metadata.collection_name = str(bot_id)
        metadata.embedding_provider = "openai"
        metadata.embedding_model = "text-embedding-3-small"
        metadata.embedding_dimension = 1536
        metadata.points_count = 100
        metadata.status = "active"
        metadata.configuration_history = []
        metadata.migration_info = {}
        metadata.last_updated = datetime.utcnow()
        metadata.created_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = metadata
        
        # Execute
        result = await dimension_validator.get_collection_metadata(bot_id)
        
        # Assert
        assert result is not None
        assert result["bot_id"] == str(bot_id)
        assert result["embedding_provider"] == "openai"
        assert result["embedding_model"] == "text-embedding-3-small"
        assert result["embedding_dimension"] == 1536
        assert result["points_count"] == 100
    
    @pytest.mark.asyncio
    async def test_get_collection_metadata_not_found(self, dimension_validator, mock_db):
        """Test retrieving collection metadata when not found."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await dimension_validator.get_collection_metadata(uuid.uuid4())
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_dimension_info(self, dimension_validator, mock_db):
        """Test caching dimension information."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing cache
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Execute
        result = await dimension_validator.cache_dimension_info(
            "openai", "text-embedding-3-small", 1536, True
        )
        
        # Assert
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_dimension_validation_result_creation(self):
        """Test DimensionValidationResult creation."""
        result = DimensionValidationResult(
            is_valid=True,
            current_dimension=1536,
            target_dimension=1536,
            dimension_match=True,
            issues=[],
            recommendations=[]
        )
        
        assert result.is_valid is True
        assert result.current_dimension == 1536
        assert result.target_dimension == 1536
        assert result.dimension_match is True
        assert result.issues == []
        assert result.recommendations == []
    
    def test_collection_dimension_info_creation(self):
        """Test CollectionDimensionInfo creation."""
        bot_id = str(uuid.uuid4())
        info = CollectionDimensionInfo(
            bot_id=bot_id,
            collection_name=bot_id,
            stored_dimension=1536,
            configured_dimension=1536,
            points_count=100,
            dimension_mismatch=False
        )
        
        assert info.bot_id == bot_id
        assert info.collection_name == bot_id
        assert info.stored_dimension == 1536
        assert info.configured_dimension == 1536
        assert info.points_count == 100
        assert info.dimension_mismatch is False
    
    def test_dimension_mismatch_type_enum(self):
        """Test DimensionMismatchType enum values."""
        assert DimensionMismatchType.NO_MISMATCH.value == "no_mismatch"
        assert DimensionMismatchType.CONFIG_VS_STORED.value == "config_vs_stored"
        assert DimensionMismatchType.MODEL_CHANGED.value == "model_changed"
        assert DimensionMismatchType.PROVIDER_CHANGED.value == "provider_changed"
        assert DimensionMismatchType.COLLECTION_CORRUPTED.value == "collection_corrupted"