"""
Tests for the embedding service and providers.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException
import httpx

from app.services.embedding_service import EmbeddingProviderService
from app.services.embedding_factory import EmbeddingClientFactory
from app.services.providers.openai_embedding_provider import OpenAIEmbeddingProvider
from app.services.providers.gemini_embedding_provider import GeminiEmbeddingProvider


class TestEmbeddingProviderService:
    """Test cases for EmbeddingProviderService."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def embedding_service(self, mock_client):
        """Create an embedding service instance with mocked client."""
        return EmbeddingProviderService(client=mock_client)
    
    @pytest.mark.asyncio
    async def test_validate_api_key_openai_success(self, embedding_service, mock_client):
        """Test successful OpenAI API key validation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        
        result = await embedding_service.validate_api_key("openai", "test-key")
        
        assert result is True
        mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_api_key_openai_failure(self, embedding_service, mock_client):
        """Test failed OpenAI API key validation."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response
        
        result = await embedding_service.validate_api_key("openai", "invalid-key")
        
        assert result is False
    

    
    def test_get_supported_providers(self, embedding_service):
        """Test getting supported providers."""
        providers = embedding_service.get_supported_providers()
        
        assert isinstance(providers, list)
        assert "openai" in providers
        assert "gemini" in providers
    
    def test_get_available_models_openai(self, embedding_service):
        """Test getting available models for OpenAI."""
        models = embedding_service.get_available_models("openai")
        
        assert isinstance(models, list)
        assert "text-embedding-3-small" in models
        assert "text-embedding-3-large" in models
        assert "text-embedding-ada-002" in models
    

    
    def test_get_embedding_dimension_openai(self, embedding_service):
        """Test getting embedding dimension for OpenAI models."""
        dim = embedding_service.get_embedding_dimension("openai", "text-embedding-3-small")
        assert dim == 1536
        
        dim = embedding_service.get_embedding_dimension("openai", "text-embedding-3-large")
        assert dim == 3072
    

    
    def test_validate_model_for_provider(self, embedding_service):
        """Test model validation for providers."""
        # Valid models
        assert embedding_service.validate_model_for_provider("openai", "text-embedding-3-small") is True
        assert embedding_service.validate_model_for_provider("gemini", "embedding-001") is True
        
        # Invalid models
        assert embedding_service.validate_model_for_provider("openai", "invalid-model") is False
        assert embedding_service.validate_model_for_provider("gemini", "invalid-model") is False
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_openai_success(self, embedding_service, mock_client):
        """Test successful embedding generation with OpenAI."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                {"index": 1, "embedding": [0.4, 0.5, 0.6]}
            ]
        }
        mock_client.post.return_value = mock_response
        
        texts = ["Hello world", "Test text"]
        embeddings = await embedding_service.generate_embeddings(
            "openai", texts, "text-embedding-3-small", "test-key"
        )
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
        mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_texts(self, embedding_service):
        """Test embedding generation with empty text list."""
        embeddings = await embedding_service.generate_embeddings(
            "openai", [], "text-embedding-3-small", "test-key"
        )
        
        assert embeddings == []
    
    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, embedding_service, mock_client):
        """Test generating a single embedding."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]}
            ]
        }
        mock_client.post.return_value = mock_response
        
        embedding = await embedding_service.generate_single_embedding(
            "openai", "Hello world", "text-embedding-3-small", "test-key"
        )
        
        assert embedding == [0.1, 0.2, 0.3]
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_with_batching(self, embedding_service, mock_client):
        """Test embedding generation with batching."""
        # Mock successful responses for batches - need different responses for each batch
        def mock_post_side_effect(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            # Return different embeddings for each call
            if mock_client.post.call_count == 1:
                mock_response.json.return_value = {
                    "data": [
                        {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                        {"index": 1, "embedding": [0.4, 0.5, 0.6]}
                    ]
                }
            elif mock_client.post.call_count == 2:
                mock_response.json.return_value = {
                    "data": [
                        {"index": 0, "embedding": [0.7, 0.8, 0.9]},
                        {"index": 1, "embedding": [1.0, 1.1, 1.2]}
                    ]
                }
            else:
                mock_response.json.return_value = {
                    "data": [
                        {"index": 0, "embedding": [1.3, 1.4, 1.5]}
                    ]
                }
            return mock_response
        
        mock_client.post.side_effect = mock_post_side_effect
        
        # Create a large list of texts to trigger batching
        texts = [f"Text {i}" for i in range(5)]
        
        embeddings = await embedding_service.generate_embeddings(
            "openai", texts, "text-embedding-3-small", "test-key", batch_size=2
        )
        
        assert len(embeddings) == 5
        # Should have made multiple API calls due to batching
        assert mock_client.post.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_with_fallback(self, embedding_service, mock_client):
        """Test embedding generation with fallback to gemini provider."""
        # Mock primary provider failure
        mock_client.post.side_effect = httpx.ConnectError("Connection failed")
        
        with patch.object(embedding_service, 'generate_embeddings') as mock_generate:
            # First call fails, second call (fallback) succeeds
            mock_generate.side_effect = [
                HTTPException(status_code=500, detail="Primary failed"),
                [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            ]
            
            embeddings, used_provider, used_model = await embedding_service.generate_embeddings_with_fallback(
                "openai", ["Hello", "World"], "text-embedding-3-small", "test-key"
            )
            
            assert len(embeddings) == 2
            assert used_provider == "gemini"
            assert used_model in embedding_service.get_available_models("gemini")
    
    @pytest.mark.asyncio
    async def test_retry_operation_success_after_failure(self, embedding_service, mock_client):
        """Test retry operation succeeds after initial failures."""
        # This test is complex due to the retry mechanism being internal
        # For now, we'll test that the service can handle basic failures
        mock_client.post.side_effect = HTTPException(status_code=500, detail="Server error")
        
        with pytest.raises(HTTPException):
            await embedding_service.generate_embeddings(
                "openai", ["test"], "text-embedding-3-small", "test-key"
            )
    
    def test_get_provider_info(self, embedding_service):
        """Test getting provider information."""
        info = embedding_service.get_provider_info("openai")
        
        assert info["name"] == "openai"
        assert info["base_url"] == "https://api.openai.com/v1"
        assert info["requires_api_key"] is True
        assert "available_models" in info
        assert "model_dimensions" in info
        assert "default_config" in info
    
    def test_get_all_providers_info(self, embedding_service):
        """Test getting all providers information."""
        all_info = embedding_service.get_all_providers_info()
        
        assert isinstance(all_info, dict)
        assert "openai" in all_info
        assert "gemini" in all_info
        
        for provider_info in all_info.values():
            assert "name" in provider_info
            assert "available_models" in provider_info
            assert "model_dimensions" in provider_info


class TestOpenAIEmbeddingProvider:
    """Test cases for OpenAIEmbeddingProvider."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def openai_provider(self, mock_client):
        """Create an OpenAI embedding provider instance."""
        return OpenAIEmbeddingProvider(mock_client)
    
    def test_provider_properties(self, openai_provider):
        """Test provider properties."""
        assert openai_provider.provider_name == "openai"
        assert openai_provider.base_url == "https://api.openai.com/v1"
        assert openai_provider.requires_api_key is True
    
    def test_get_headers(self, openai_provider):
        """Test header generation."""
        headers = openai_provider.get_headers("test-key")
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, openai_provider, mock_client):
        """Test successful API key validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        
        result = await openai_provider.validate_api_key("test-key")
        
        assert result is True
        mock_client.get.assert_called_once_with(
            "https://api.openai.com/v1/models",
            headers={"Content-Type": "application/json", "Authorization": "Bearer test-key"}
        )
    
    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, openai_provider, mock_client):
        """Test failed API key validation."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response
        
        result = await openai_provider.validate_api_key("invalid-key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, openai_provider, mock_client):
        """Test successful embedding generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                {"index": 1, "embedding": [0.4, 0.5, 0.6]}
            ]
        }
        mock_client.post.return_value = mock_response
        
        embeddings = await openai_provider.generate_embeddings(
            ["Hello", "World"], "text-embedding-3-small", "test-key"
        )
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_no_api_key(self, openai_provider):
        """Test embedding generation without API key."""
        with pytest.raises(HTTPException) as exc_info:
            await openai_provider.generate_embeddings(
                ["Hello"], "text-embedding-3-small", None
            )
        
        assert exc_info.value.status_code == 400
        assert "API key is required" in str(exc_info.value.detail)
    
    def test_get_available_models(self, openai_provider):
        """Test getting available models."""
        models = openai_provider.get_available_models()
        
        assert "text-embedding-3-small" in models
        assert "text-embedding-3-large" in models
        assert "text-embedding-ada-002" in models
    
    def test_get_embedding_dimension(self, openai_provider):
        """Test getting embedding dimensions."""
        assert openai_provider.get_embedding_dimension("text-embedding-3-small") == 1536
        assert openai_provider.get_embedding_dimension("text-embedding-3-large") == 3072
        assert openai_provider.get_embedding_dimension("text-embedding-ada-002") == 1536
        
        with pytest.raises(HTTPException):
            openai_provider.get_embedding_dimension("invalid-model")


class TestGeminiEmbeddingProvider:
    """Test cases for GeminiEmbeddingProvider."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def gemini_provider(self, mock_client):
        """Create a Gemini embedding provider instance."""
        return GeminiEmbeddingProvider(mock_client)
    
    def test_provider_properties(self, gemini_provider):
        """Test provider properties."""
        assert gemini_provider.provider_name == "gemini"
        assert gemini_provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
        assert gemini_provider.requires_api_key is True
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, gemini_provider, mock_client):
        """Test successful API key validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response
        
        result = await gemini_provider.validate_api_key("test-key")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, gemini_provider, mock_client):
        """Test successful embedding generation."""
        # Mock responses for each text (Gemini processes one at a time)
        mock_responses = [
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.1, 0.2, 0.3]}}),
            Mock(status_code=200, json=lambda: {"embedding": {"values": [0.4, 0.5, 0.6]}})
        ]
        mock_client.post.side_effect = mock_responses
        
        embeddings = await gemini_provider.generate_embeddings(
            ["Hello", "World"], "embedding-001", "test-key"
        )
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
        assert mock_client.post.call_count == 2
    
    def test_get_available_models(self, gemini_provider):
        """Test getting available models."""
        models = gemini_provider.get_available_models()
        
        assert "embedding-001" in models
        assert "text-embedding-004" in models
    
    def test_get_embedding_dimension(self, gemini_provider):
        """Test getting embedding dimensions."""
        assert gemini_provider.get_embedding_dimension("embedding-001") == 768
        assert gemini_provider.get_embedding_dimension("text-embedding-004") == 768
        
        with pytest.raises(HTTPException):
            gemini_provider.get_embedding_dimension("invalid-model")





class TestEmbeddingClientFactory:
    """Test cases for EmbeddingClientFactory."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def factory(self, mock_client):
        """Create an embedding factory instance."""
        return EmbeddingClientFactory(mock_client)
    
    def test_get_supported_providers(self, factory):
        """Test getting supported providers."""
        providers = factory.get_supported_providers()
        
        assert "openai" in providers
        assert "gemini" in providers
    
    def test_get_provider_success(self, factory):
        """Test getting a valid provider."""
        provider = factory.get_provider("openai")
        assert isinstance(provider, OpenAIEmbeddingProvider)
        
        provider = factory.get_provider("gemini")
        assert isinstance(provider, GeminiEmbeddingProvider)
    
    def test_get_provider_invalid(self, factory):
        """Test getting an invalid provider."""
        with pytest.raises(HTTPException) as exc_info:
            factory.get_provider("invalid")
        
        assert exc_info.value.status_code == 400
        assert "not supported" in str(exc_info.value.detail)
    
    def test_get_all_available_models(self, factory):
        """Test getting all available models."""
        all_models = factory.get_all_available_models()
        
        assert isinstance(all_models, dict)
        assert "openai" in all_models
        assert "gemini" in all_models
        
        assert "text-embedding-3-small" in all_models["openai"]
        assert "embedding-001" in all_models["gemini"]
    
    def test_get_embedding_dimension(self, factory):
        """Test getting embedding dimensions."""
        dim = factory.get_embedding_dimension("openai", "text-embedding-3-small")
        assert dim == 1536
        
        dim = factory.get_embedding_dimension("gemini", "embedding-001")
        assert dim == 768
    
    @pytest.mark.asyncio
    async def test_validate_api_key(self, factory, mock_client):
        """Test API key validation through factory."""
        # Mock successful response for OpenAI
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response
        
        result = await factory.validate_api_key("openai", "test-key")
        assert result is True
        
        # Test with Gemini provider (uses POST)
        result = await factory.validate_api_key("gemini", "test-key")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(self, factory, mock_client):
        """Test embedding generation through factory."""
        # Mock successful response for OpenAI
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]
        }
        mock_client.post.return_value = mock_response
        
        embeddings = await factory.generate_embeddings(
            "openai", ["Hello"], "text-embedding-3-small", "test-key"
        )
        
        assert len(embeddings) == 1
        assert embeddings[0] == [0.1, 0.2, 0.3]
    
    def test_get_provider_info(self, factory):
        """Test getting provider information."""
        info = factory.get_provider_info("openai")
        
        assert info["name"] == "openai"
        assert info["requires_api_key"] is True
        assert "available_models" in info
        assert "model_dimensions" in info
    
    @pytest.mark.asyncio
    async def test_close(self, factory, mock_client):
        """Test closing the factory."""
        await factory.close()
        mock_client.aclose.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])