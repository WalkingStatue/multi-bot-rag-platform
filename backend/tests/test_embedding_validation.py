"""
Tests for embedding configuration validation and metadata management.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.embedding_configuration_validator import (
    EmbeddingConfigurationValidator,
    ValidationReport,
    ValidationIssue,
    ValidationSeverity,
    ProviderModelInfo
)
from app.models.bot import Bot
from app.models.collection_metadata import CollectionMetadata, EmbeddingConfigurationHistory
from app.models.user import User


class TestEmbeddingConfigurationValidator:
    """Test cases for EmbeddingConfigurationValidator."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        mock_service = Mock()
        mock_service.get_supported_providers.return_value = ["openai", "gemini", "anthropic"]
        mock_service.get_available_models.return_value = ["text-embedding-3-small", "text-embedding-3-large"]
        mock_service.get_embedding_dimension.return_value = 1536
        mock_service.validate_api_key = AsyncMock(return_value=True)
        mock_service.close = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def mock_user_service(self):
        """Mock user service."""
        mock_service = Mock()
        mock_service.get_user_api_key.return_value = "test-api-key"
        return mock_service
    
    @pytest.fixture
    def validator(self, mock_db):
        """Create validator instance with mocked dependencies."""
        validator = EmbeddingConfigurationValidator(mock_db)
        return validator
    
    @pytest.mark.asyncio
    async def test_validate_provider_model_combination_success(self, validator, mock_embedding_service, mock_user_service):
        """Test successful provider/model validation."""
        # Mock dependencies
        with patch.object(validator, 'embedding_service', mock_embedding_service), \
             patch.ob