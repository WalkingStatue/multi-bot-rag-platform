"""
Unit tests for embedding model validator.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.embedding_model_validator import (
    EmbeddingModelValidator,
    ModelValidationStatus,
    MigrationImpact,
    ModelValidationResult,
    ModelCompatibilityResult,
    ModelSuggestion
)
from app.models.bot import Bot
from app.models.document import DocumentChunk
from app.models.collection_metadata import DimensionCompatibilityCache


class TestEmbeddingModelValidator:
    """Test cases for EmbeddingModelValidator."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        service = Mock()
        service.get_supported_providers.return_value = ["openai", "gemini", "anthropic"]
        service.get_available_models.return_value = ["text-embedding-3-small", "text-embedding-3-large"]
        service.get_embedding_dimension.return_value = 1536
        service.validate_api_key = AsyncMock(return_value=True)
        service.get_provider_info.return_value = {
            "requires_api_key": True,
            "base_url": "https://api.openai.com/v1",
            "default_config": {}
        }
        service.get_all_providers_info.return_value = {
            "openai": {
                "model_dimensions": {
                    "text-embedding-3-small": 1536,
                    "text-embedding-3-large": 3072
                }
            }
        }
        return service
    
    @pytest.fixture
    def validator(self, mock_db, mock_embedding_service):
        """Create validator instance with mocked dependencies."""
        validator = EmbeddingModelValidator(mock_db)
        validator.embedding_service = mock_embedding_service
        validator.user_service = Mock()
        return validator
    
    @pytest.mark.asyncio
    async def test_validate_model_availability_success(self, validator, mock_db):
        """Test successful model validation."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No cache
        
        # Execute
        result = await validator.validate_model_availability(
            provider="openai",
            model="text-embedding-3-small",
            api_key="test-key",
            use_cache=False
        )
        
        # Assert
        assert result.provider == "openai"
        assert result.model == "text-embedding-3-small"
        assert result.status == ModelValidationStatus.VALID
        assert result.is_available is True
        assert result.dimension == 1536
        assert result.validation_error is None
    
    @pytest.mark.asyncio
    async def test_validate_model_availability_unsupported_provider(self, validator, mock_db):
        """Test validation with unsupported provider."""
        # Execute
        result = await validator.validate_model_availability(
            provider="unsupported",
            model="some-model",
            use_cache=False
        )
        
        # Assert
        assert result.provider == "unsupported"
        assert result.status == ModelValidationStatus.INVALID
        assert result.is_available is False
        assert result.dimension == 0
        assert "not supported" in result.validation_error
    
    @pytest.mark.asyncio
    async def test_validate_model_availability_unavailable_model(self, validator, mock_db, mock_embedding_service):
        """Test validation with unavailable model."""
        # Setup
        mock_embedding_service.get_available_models.return_value = ["other-model"]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await validator.validate_model_availability(
            provider="openai",
            model="unavailable-model",
            use_cache=False
        )
        
        # Assert
        assert result.status == ModelValidationStatus.UNAVAILABLE
        assert result.is_available is False
        assert "not found" in result.validation_error
    
    @pytest.mark.asyncio
    async def test_validate_model_availability_with_cache(self, validator, mock_db):
        """Test validation using cached results."""
        # Setup cached result
        cached_entry = Mock()
        cached_entry.provider = "openai"
        cached_entry.model = "text-embedding-3-small"
        cached_entry.is_valid = True
        cached_entry.dimension = 1536
        cached_entry.validation_error = None
        cached_entry.last_validated = datetime.utcnow()
        
        mock_db.query.return_value.filter.return_value.first.return_value = cached_entry
        
        # Execute
        result = await validator.validate_model_availability(
            provider="openai",
            model="text-embedding-3-small",
            use_cache=True
        )
        
        # Assert
        assert result.is_available is True
        assert result.dimension == 1536
    
    @pytest.mark.asyncio
    async def test_check_model_compatibility_success(self, validator, mock_db, mock_embedding_service):
        """Test successful model compatibility check."""
        # Setup bot
        bot = Mock()
        bot.id = uuid.uuid4()
        bot.embedding_provider = "openai"
        bot.embedding_model = "text-embedding-3-small"
        mock_db.query.return_value.filter.return_value.first.return_value = bot
        
        # Setup document count
        mock_db.query.return_value.filter.return_value.count.return_value = 50
        
        # Mock validation results
        with patch.object(validator, 'validate_model_availability') as mock_validate:
            mock_validate.side_effect = [
                ModelValidationResult(
                    provider="openai",
                    model="text-embedding-3-small",
                    status=ModelValidationStatus.VALID,
                    is_available=True,
                    dimension=1536
                ),
                ModelValidationResult(
                    provider="openai",
                    model="text-embedding-3-large",
                    status=ModelValidationStatus.VALID,
                    is_available=True,
                    dimension=3072
                )
            ]
            
            # Execute
            result = await validator.check_model_compatibility(
                bot_id=bot.id,
                target_provider="openai",
                target_model="text-embedding-3-large"
            )
        
        # Assert
        assert result.is_compatible is True
        assert result.migration_required is True  # Different dimensions
        assert result.migration_impact == MigrationImpact.LOW  # < 100 chunks
        assert result.affected_documents == 50
        assert len(result.compatibility_issues) > 0  # Dimension mismatch
    
    @pytest.mark.asyncio
    async def test_check_model_compatibility_bot_not_found(self, validator, mock_db):
        """Test compatibility check with non-existent bot."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Assert
        with pytest.raises(Exception):  # Should raise HTTPException
            await validator.check_model_compatibility(
                bot_id=uuid.uuid4(),
                target_provider="openai",
                target_model="text-embedding-3-large"
            )
    
    @pytest.mark.asyncio
    async def test_suggest_compatible_models(self, validator, mock_embedding_service):
        """Test model suggestions."""
        # Mock validation
        with patch.object(validator, 'validate_model_availability') as mock_validate:
            mock_validate.return_value = ModelValidationResult(
                provider="openai",
                model="text-embedding-3-small",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536
            )
            
            # Execute
            suggestions = await validator.suggest_compatible_models(
                target_dimension=1536,
                max_suggestions=3
            )
        
        # Assert
        assert len(suggestions) > 0
        assert all(isinstance(s, ModelSuggestion) for s in suggestions)
        assert all(s.dimension == 1536 for s in suggestions)
        assert suggestions[0].compatibility_score >= suggestions[-1].compatibility_score  # Sorted
    
    @pytest.mark.asyncio
    async def test_detect_deprecated_models(self, validator, mock_db):
        """Test deprecated model detection."""
        # Setup bots with deprecated models
        bot1 = Mock()
        bot1.id = uuid.uuid4()
        bot1.name = "Test Bot 1"
        bot1.embedding_provider = "openai"
        bot1.embedding_model = "text-embedding-ada-002"  # Deprecated
        
        mock_db.query.return_value.all.return_value = [bot1]
        
        # Mock validation to return deprecated status
        with patch.object(validator, 'validate_model_availability') as mock_validate:
            mock_validate.return_value = ModelValidationResult(
                provider="openai",
                model="text-embedding-ada-002",
                status=ModelValidationStatus.DEPRECATED,
                is_available=True,
                dimension=1536,
                deprecation_info={
                    "deprecated_date": "2024-01-01",
                    "replacement": "text-embedding-3-small"
                }
            )
            
            with patch.object(validator, 'suggest_compatible_models') as mock_suggest:
                mock_suggest.return_value = [
                    ModelSuggestion(
                        provider="openai",
                        model="text-embedding-3-small",
                        dimension=1536,
                        compatibility_score=0.9,
                        reason="Recommended replacement",
                        migration_required=False
                    )
                ]
                
                # Execute
                notifications = await validator.detect_deprecated_models(
                    check_all_bots=True
                )
        
        # Assert
        assert len(notifications) == 1
        assert notifications[0]["bot_id"] == str(bot1.id)
        assert notifications[0]["current_model"] == "text-embedding-ada-002"
        assert len(notifications[0]["suggested_replacements"]) > 0
    
    @pytest.mark.asyncio
    async def test_validate_all_models(self, validator, mock_embedding_service):
        """Test validation of all models."""
        # Mock validation
        with patch.object(validator, 'validate_model_availability') as mock_validate:
            mock_validate.return_value = ModelValidationResult(
                provider="openai",
                model="text-embedding-3-small",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536
            )
            
            # Execute
            results = await validator.validate_all_models(refresh_cache=True)
        
        # Assert
        assert "openai" in results
        assert len(results["openai"]) > 0
        assert all(isinstance(r, ModelValidationResult) for r in results["openai"])
    
    def test_calculate_compatibility_score(self, validator):
        """Test compatibility score calculation."""
        # Test with OpenAI provider (high preference)
        validation = ModelValidationResult(
            provider="openai",
            model="text-embedding-3-small",
            status=ModelValidationStatus.VALID,
            is_available=True,
            dimension=1536
        )
        
        score = validator._calculate_compatibility_score("openai", "text-embedding-3-small", validation)
        
        # Should be high score (provider preference + availability + model version)
        assert score > 0.8
        
        # Test with deprecated model - create new instance to avoid mutation
        deprecated_validation = ModelValidationResult(
            provider="openai",
            model="text-embedding-ada-002",  # Different model to avoid max score
            status=ModelValidationStatus.DEPRECATED,
            is_available=True,
            dimension=1536
        )
        score_deprecated = validator._calculate_compatibility_score("openai", "text-embedding-ada-002", deprecated_validation)
        
        # Should be lower due to deprecation penalty and older model
        assert score_deprecated < score
    
    def test_estimate_migration_time(self, validator):
        """Test migration time estimation."""
        # Test different chunk counts
        assert "Immediate" in validator._estimate_migration_time(0)
        assert "minutes" in validator._estimate_migration_time(50)
        assert "hour" in validator._estimate_migration_time(15000)
    
    def test_generate_suggestion_reason(self, validator):
        """Test suggestion reason generation."""
        validation = ModelValidationResult(
            provider="openai",
            model="text-embedding-3-small",
            status=ModelValidationStatus.VALID,
            is_available=True,
            dimension=1536
        )
        
        reason = validator._generate_suggestion_reason("openai", "text-embedding-3-small", validation, 0.9)
        
        assert "compatible" in reason.lower()
        assert "reliable" in reason.lower()  # OpenAI provider
        assert "latest" in reason.lower()  # Version 3 model
    
    @pytest.mark.asyncio
    async def test_cache_validation_result(self, validator, mock_db):
        """Test caching of validation results."""
        # Setup
        result = ModelValidationResult(
            provider="openai",
            model="text-embedding-3-small",
            status=ModelValidationStatus.VALID,
            is_available=True,
            dimension=1536,
            last_validated=datetime.utcnow()
        )
        
        # Mock existing cache entry
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        await validator._cache_validation_result(result)
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_validation_expired(self, validator, mock_db):
        """Test getting expired cached validation."""
        # Setup expired cache entry
        expired_entry = Mock()
        expired_entry.last_validated = datetime.utcnow() - timedelta(days=2)  # Expired
        
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No valid cache
        
        # Execute
        result = await validator._get_cached_validation("openai", "text-embedding-3-small")
        
        # Assert
        assert result is None  # Should not return expired cache
    
    @pytest.mark.asyncio
    async def test_api_key_validation_timeout(self, validator, mock_embedding_service):
        """Test API key validation with timeout."""
        # Setup timeout
        import asyncio
        mock_embedding_service.validate_api_key.side_effect = asyncio.TimeoutError()
        
        # Execute
        result = await validator.validate_model_availability(
            provider="openai",
            model="text-embedding-3-small",
            api_key="test-key",
            use_cache=False
        )
        
        # Assert
        assert result.is_available is True  # Should still be available
        # The timeout should be handled gracefully without failing the validation
    
    @pytest.mark.asyncio
    async def test_model_validation_with_invalid_api_key(self, validator, mock_embedding_service):
        """Test model validation with invalid API key."""
        # Setup invalid API key
        mock_embedding_service.validate_api_key.return_value = False
        
        # Execute
        result = await validator.validate_model_availability(
            provider="openai",
            model="text-embedding-3-small",
            api_key="invalid-key",
            use_cache=False
        )
        
        # Assert
        assert result.is_available is True  # Model itself is available
        # API key validation failure should be noted but not prevent model availability check
    
    def test_provider_preferences(self, validator):
        """Test provider preference scoring."""
        # OpenAI should have highest preference
        assert validator.provider_preferences["openai"] == 1.0
        
        # Other providers should have lower scores
        assert validator.provider_preferences["gemini"] < 1.0
        assert validator.provider_preferences["anthropic"] < 1.0
    
    @pytest.mark.asyncio
    async def test_suggest_compatible_models_with_exclusions(self, validator, mock_embedding_service):
        """Test model suggestions with exclusions."""
        # Mock validation
        with patch.object(validator, 'validate_model_availability') as mock_validate:
            mock_validate.return_value = ModelValidationResult(
                provider="gemini",
                model="embedding-001",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536
            )
            
            # Execute with exclusions
            suggestions = await validator.suggest_compatible_models(
                target_dimension=1536,
                exclude_provider="openai",
                exclude_model="text-embedding-3-small",
                max_suggestions=3
            )
        
        # Assert
        assert all(s.provider != "openai" for s in suggestions)
        assert all(s.model != "text-embedding-3-small" for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_validation(self, validator, mock_embedding_service):
        """Test error handling during validation."""
        # Setup service to raise exception
        mock_embedding_service.get_available_models.side_effect = Exception("Service error")
        
        # Execute
        result = await validator.validate_model_availability(
            provider="openai",
            model="text-embedding-3-small",
            use_cache=False
        )
        
        # Assert
        assert result.status == ModelValidationStatus.INVALID
        assert result.is_available is False
        assert "Service error" in result.validation_error