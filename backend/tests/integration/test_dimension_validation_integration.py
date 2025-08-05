"""
Integration tests for dimension validation functionality.
"""
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch

from app.services.dimension_validator import DimensionValidator
from app.services.embedding_compatibility_manager import EmbeddingCompatibilityManager
from app.models.bot import Bot
from app.models.collection_metadata import CollectionMetadata


class TestDimensionValidationIntegration:
    """Integration tests for dimension validation system."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def sample_bot(self):
        """Sample bot for testing."""
        return Bot(
            id=uuid.uuid4(),
            name="Test Bot",
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
            owner_id=uuid.uuid4()
        )
    
    @pytest.mark.asyncio
    async def test_dimension_validation_workflow(self, mock_db, sample_bot):
        """Test complete dimension validation workflow."""
        # Mock services
        with patch('app.services.dimension_validator.EmbeddingProviderService') as mock_embedding_service, \
             patch('app.services.dimension_validator.VectorService') as mock_vector_service:
            
            # Setup mocks
            mock_embedding_service.return_value.validate_model_for_provider.return_value = True
            mock_embedding_service.return_value.get_embedding_dimension.side_effect = [1536, 768]  # Different dimensions
            mock_embedding_service.return_value.get_available_models.return_value = ["text-embedding-3-small"]
            
            mock_vector_service.return_value.vector_store.collection_exists = AsyncMock(return_value=True)
            mock_vector_service.return_value.get_bot_collection_stats = AsyncMock(return_value={
                'config': {'vector_size': 1536},
                'points_count': 100
            })
            
            # Setup database mock
            mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
            mock_db.add = Mock()
            mock_db.commit = Mock()
            
            # Create validator
            validator = DimensionValidator(mock_db)
            
            # Test 1: Validate dimension compatibility (should detect mismatch)
            result = await validator.validate_dimension_compatibility(
                sample_bot.id, "gemini", "text-embedding-004"
            )
            
            assert result.is_valid is True
            assert result.dimension_match is False
            assert result.current_dimension == 1536
            assert result.target_dimension == 768
            assert "Migration will be required" in str(result.recommendations)
            
            # Test 2: Store collection metadata
            metadata_stored = await validator.store_collection_metadata(
                sample_bot.id, "openai", "text-embedding-3-small", 1536, 100
            )
            
            assert metadata_stored is True
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_embedding_compatibility_manager_integration(self, mock_db, sample_bot):
        """Test integration between EmbeddingCompatibilityManager and DimensionValidator."""
        # Mock services
        with patch('app.services.embedding_compatibility_manager.EmbeddingProviderService') as mock_embedding_service, \
             patch('app.services.embedding_compatibility_manager.VectorService') as mock_vector_service, \
             patch('app.services.embedding_compatibility_manager.UserService') as mock_user_service:
            
            # Setup mocks
            mock_embedding_service.return_value.validate_model_for_provider.return_value = True
            mock_embedding_service.return_value.get_embedding_dimension.side_effect = [1536, 1536]  # Same dimensions
            
            mock_vector_service.return_value.vector_store.collection_exists = AsyncMock(return_value=True)
            mock_vector_service.return_value.get_bot_collection_stats = AsyncMock(return_value={
                'config': {'vector_size': 1536},
                'points_count': 100
            })
            
            mock_user_service.return_value.get_user_api_key.return_value = "test-api-key"
            mock_embedding_service.return_value.validate_api_key = AsyncMock(return_value=True)
            
            # Setup database mock
            mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
            
            # Create compatibility manager
            manager = EmbeddingCompatibilityManager(mock_db)
            
            # Test provider change validation
            result = await manager.validate_provider_change(
                sample_bot.id, "openai", "text-embedding-3-small"
            )
            
            assert result.compatible is True
            assert result.migration_required is False
            assert len(result.issues or []) == 0
    
    @pytest.mark.asyncio
    async def test_dimension_mismatch_detection(self, mock_db, sample_bot):
        """Test detection of dimension mismatches across collections."""
        # Mock services
        with patch('app.services.dimension_validator.EmbeddingProviderService') as mock_embedding_service, \
             patch('app.services.dimension_validator.VectorService') as mock_vector_service:
            
            # Setup mocks - dimension mismatch scenario
            mock_embedding_service.return_value.get_embedding_dimension.return_value = 1536
            mock_vector_service.return_value.vector_store.collection_exists = AsyncMock(return_value=True)
            mock_vector_service.return_value.get_bot_collection_stats = AsyncMock(return_value={
                'config': {'vector_size': 768},  # Different from configured 1536
                'points_count': 100
            })
            
            # Setup database mock
            mock_db.query.return_value.all.return_value = [sample_bot]
            mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing metadata
            
            # Create validator
            validator = DimensionValidator(mock_db)
            
            # Test mismatch detection
            mismatches = await validator.detect_dimension_mismatches([sample_bot.id])
            
            assert len(mismatches) == 1
            assert mismatches[0].dimension_mismatch is True
            assert mismatches[0].stored_dimension == 768
            assert mismatches[0].configured_dimension == 1536
            assert mismatches[0].bot_id == str(sample_bot.id)
    
    @pytest.mark.asyncio
    async def test_configuration_change_validation_with_history(self, mock_db, sample_bot):
        """Test configuration change validation with history tracking."""
        # Mock services
        with patch('app.services.dimension_validator.EmbeddingProviderService') as mock_embedding_service, \
             patch('app.services.dimension_validator.VectorService') as mock_vector_service:
            
            # Setup mocks
            mock_embedding_service.return_value.validate_model_for_provider.return_value = True
            mock_embedding_service.return_value.get_embedding_dimension.side_effect = [1536, 768]  # Different dimensions
            mock_embedding_service.return_value.get_available_models.return_value = ["text-embedding-004"]
            
            mock_vector_service.return_value.vector_store.collection_exists = AsyncMock(return_value=True)
            mock_vector_service.return_value.get_bot_collection_stats = AsyncMock(return_value={
                'config': {'vector_size': 1536},
                'points_count': 100
            })
            
            # Setup database mock
            mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
            mock_db.add = Mock()
            mock_db.commit = Mock()
            
            # Create validator
            validator = DimensionValidator(mock_db)
            
            # Test configuration change validation
            result = await validator.validate_embedding_configuration_change(
                sample_bot.id, "gemini", "text-embedding-004", "Testing new provider"
            )
            
            assert result.is_valid is True
            assert result.dimension_match is False
            
            # Verify that configuration history was recorded
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            
            # Check that the added object is an EmbeddingConfigurationHistory
            added_object = mock_db.add.call_args[0][0]
            assert hasattr(added_object, 'bot_id')
            assert hasattr(added_object, 'new_provider')
            assert hasattr(added_object, 'new_model')
            assert hasattr(added_object, 'migration_required')
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, mock_db):
        """Test dimension caching functionality."""
        # Mock services
        with patch('app.services.dimension_validator.EmbeddingProviderService') as mock_embedding_service, \
             patch('app.services.dimension_validator.VectorService') as mock_vector_service:
            
            # Setup database mock for cache operations
            mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing cache
            mock_db.add = Mock()
            mock_db.commit = Mock()
            
            # Create validator
            validator = DimensionValidator(mock_db)
            
            # Test caching dimension info
            cache_result = await validator.cache_dimension_info(
                "openai", "text-embedding-3-small", 1536, True
            )
            
            assert cache_result is True
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            
            # Verify the cached object has correct attributes
            cached_object = mock_db.add.call_args[0][0]
            assert hasattr(cached_object, 'provider')
            assert hasattr(cached_object, 'model')
            assert hasattr(cached_object, 'dimension')
            assert hasattr(cached_object, 'is_valid')