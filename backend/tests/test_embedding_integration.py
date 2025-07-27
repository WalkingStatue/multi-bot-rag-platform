"""
Integration tests for the embedding system.
"""
import pytest
from unittest.mock import Mock, AsyncMock
import httpx

from app.services.embedding_service import EmbeddingProviderService


class TestEmbeddingIntegration:
    """Integration tests for the embedding system."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def embedding_service(self, mock_client):
        """Create an embedding service instance."""
        return EmbeddingProviderService(client=mock_client)
    
    @pytest.mark.asyncio
    async def test_full_embedding_workflow_openai(self, embedding_service, mock_client):
        """Test complete embedding workflow with OpenAI provider."""
        # Mock API key validation
        mock_validation_response = Mock()
        mock_validation_response.status_code = 200
        
        # Mock embedding generation
        mock_embedding_response = Mock()
        mock_embedding_response.status_code = 200
        mock_embedding_response.json.return_value = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3, 0.4]},
                {"index": 1, "embedding": [0.5, 0.6, 0.7, 0.8]}
            ]
        }
        
        # Set up mock responses
        mock_client.get.return_value = mock_validation_response
        mock_client.post.return_value = mock_embedding_response
        
        # Test API key validation
        is_valid = await embedding_service.validate_api_key("openai", "test-key")
        assert is_valid is True
        
        # Test model validation
        assert embedding_service.validate_model_for_provider("openai", "text-embedding-3-small") is True
        
        # Test embedding dimension
        dimension = embedding_service.get_embedding_dimension("openai", "text-embedding-3-small")
        assert dimension == 1536
        
        # Test embedding generation
        texts = ["Hello world", "Test embedding"]
        embeddings = await embedding_service.generate_embeddings(
            "openai", texts, "text-embedding-3-small", "test-key"
        )
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3, 0.4]
        assert embeddings[1] == [0.5, 0.6, 0.7, 0.8]
        
        # Verify API calls were made
        mock_client.get.assert_called_once()
        mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_full_embedding_workflow_gemini(self, embedding_service, mock_client):
        """Test complete embedding workflow with Gemini provider."""
        # Mock API key validation
        mock_validation_response = Mock()
        mock_validation_response.status_code = 200
        
        # Mock embedding generation (Gemini processes one at a time)
        mock_embedding_responses = [
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1, 0.2, 0.3]}}),
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.4, 0.5, 0.6]}})
        ]
        
        # Set up mock responses
        mock_client.post.side_effect = [mock_validation_response] + mock_embedding_responses
        
        # Test API key validation
        is_valid = await embedding_service.validate_api_key("gemini", "test-key")
        assert is_valid is True
        
        # Test model validation
        assert embedding_service.validate_model_for_provider("gemini", "embedding-001") is True
        
        # Test embedding dimension
        dimension = embedding_service.get_embedding_dimension("gemini", "embedding-001")
        assert dimension == 768
        
        # Test embedding generation
        texts = ["Hello world", "Test embedding"]
        embeddings = await embedding_service.generate_embeddings(
            "gemini", texts, "embedding-001", "test-key"
        )
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
        
        # Verify API calls were made (1 for validation + 2 for embeddings)
        assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_local_provider_workflow(self, embedding_service):
        """Test complete embedding workflow with local provider."""
        # Test API key validation (should always be True)
        is_valid = await embedding_service.validate_api_key("local", None)
        assert is_valid is True
        
        # Test model validation
        assert embedding_service.validate_model_for_provider("local", "all-MiniLM-L6-v2") is True
        
        # Test embedding dimension
        dimension = embedding_service.get_embedding_dimension("local", "all-MiniLM-L6-v2")
        assert dimension == 384
        
        # Test available models
        models = embedding_service.get_available_models("local")
        assert "all-MiniLM-L6-v2" in models
        assert "all-mpnet-base-v2" in models
    
    def test_provider_switching(self, embedding_service):
        """Test switching between different providers."""
        # Test getting provider information
        openai_info = embedding_service.get_provider_info("openai")
        assert openai_info["name"] == "openai"
        assert openai_info["requires_api_key"] is True
        assert "text-embedding-3-small" in openai_info["available_models"]
        
        gemini_info = embedding_service.get_provider_info("gemini")
        assert gemini_info["name"] == "gemini"
        assert gemini_info["requires_api_key"] is True
        assert "embedding-001" in gemini_info["available_models"]
        
        local_info = embedding_service.get_provider_info("local")
        assert local_info["name"] == "local"
        assert local_info["requires_api_key"] is False
        assert "all-MiniLM-L6-v2" in local_info["available_models"]
    
    def test_get_all_providers_info(self, embedding_service):
        """Test getting information for all providers."""
        all_info = embedding_service.get_all_providers_info()
        
        assert isinstance(all_info, dict)
        assert "openai" in all_info
        assert "gemini" in all_info
        assert "local" in all_info
        
        # Verify each provider has required fields
        for provider_name, info in all_info.items():
            assert "name" in info
            assert "requires_api_key" in info
            assert "available_models" in info
            assert "model_dimensions" in info
            assert "default_config" in info
    
    def test_get_all_available_models(self, embedding_service):
        """Test getting all available models across providers."""
        all_models = embedding_service.get_all_available_models()
        
        assert isinstance(all_models, dict)
        assert "openai" in all_models
        assert "gemini" in all_models
        assert "local" in all_models
        
        # Verify specific models exist
        assert "text-embedding-3-small" in all_models["openai"]
        assert "embedding-001" in all_models["gemini"]
        assert "all-MiniLM-L6-v2" in all_models["local"]
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, embedding_service):
        """Test the fallback mechanism to local provider."""
        fallback_provider, fallback_model = await embedding_service.get_fallback_provider()
        
        assert fallback_provider == "local"
        assert fallback_model in embedding_service.get_available_models("local")
    
    def test_supported_providers(self, embedding_service):
        """Test getting supported providers."""
        providers = embedding_service.get_supported_providers()
        
        assert isinstance(providers, list)
        assert len(providers) == 3
        assert "openai" in providers
        assert "gemini" in providers
        assert "local" in providers
    
    @pytest.mark.asyncio
    async def test_single_embedding_generation(self, embedding_service, mock_client):
        """Test generating a single embedding."""
        # Mock embedding response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]
        }
        mock_client.post.return_value = mock_response
        
        embedding = await embedding_service.generate_single_embedding(
            "openai", "Hello world", "text-embedding-3-small", "test-key"
        )
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embedding_service_cleanup(self, embedding_service):
        """Test proper cleanup of embedding service resources."""
        # This should not raise any exceptions
        await embedding_service.close()


if __name__ == "__main__":
    pytest.main([__file__])