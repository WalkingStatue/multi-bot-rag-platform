"""
Enhanced unit tests for LLM service with provider abstraction.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from fastapi import HTTPException

from app.services.llm_service import LLMProviderService
from app.services.llm_factory import LLMClientFactory
from app.services.providers import OpenAIProvider, AnthropicProvider, OpenRouterProvider, GeminiProvider


class TestLLMProviderServiceEnhanced:
    """Test cases for enhanced LLM provider service."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def llm_service(self, mock_client):
        """Create LLM service instance with mock client."""
        return LLMProviderService(client=mock_client)
    
    def test_initialization(self, llm_service):
        """Test service initialization."""
        assert llm_service.factory is not None
        assert isinstance(llm_service.factory, LLMClientFactory)
        assert llm_service.max_retries == 3
        assert llm_service.retry_delay == 1.0
    
    def test_get_supported_providers(self, llm_service):
        """Test getting supported providers."""
        providers = llm_service.get_supported_providers()
        
        expected_providers = ["openai", "anthropic", "openrouter", "gemini"]
        assert set(providers) == set(expected_providers)
        assert len(providers) == 4
    
    def test_get_available_models(self, llm_service):
        """Test getting available models for each provider."""
        # Test OpenAI models
        openai_models = llm_service.get_available_models("openai")
        assert "gpt-4" in openai_models
        assert "gpt-3.5-turbo" in openai_models
        
        # Test Anthropic models
        anthropic_models = llm_service.get_available_models("anthropic")
        assert "claude-3-opus-20240229" in anthropic_models
        assert "claude-3-haiku-20240307" in anthropic_models
        
        # Test OpenRouter models
        openrouter_models = llm_service.get_available_models("openrouter")
        assert "openai/gpt-4" in openrouter_models
        assert "anthropic/claude-3-opus" in openrouter_models
        
        # Test Gemini models
        gemini_models = llm_service.get_available_models("gemini")
        assert "gemini-pro" in gemini_models
        assert "gemini-1.5-pro" in gemini_models
    
    def test_get_all_available_models(self, llm_service):
        """Test getting all available models."""
        all_models = llm_service.get_all_available_models()
        
        assert isinstance(all_models, dict)
        assert "openai" in all_models
        assert "anthropic" in all_models
        assert "openrouter" in all_models
        assert "gemini" in all_models
        
        # Check that each provider has models
        for provider, models in all_models.items():
            assert isinstance(models, list)
            assert len(models) > 0
    
    def test_validate_model_for_provider(self, llm_service):
        """Test model validation for providers."""
        # Valid models
        assert llm_service.validate_model_for_provider("openai", "gpt-4") is True
        assert llm_service.validate_model_for_provider("anthropic", "claude-3-opus-20240229") is True
        assert llm_service.validate_model_for_provider("gemini", "gemini-pro") is True
        
        # Invalid models
        assert llm_service.validate_model_for_provider("openai", "invalid-model") is False
        assert llm_service.validate_model_for_provider("anthropic", "gpt-4") is False
    
    def test_get_provider_info(self, llm_service):
        """Test getting provider information."""
        # Test OpenAI provider info
        openai_info = llm_service.get_provider_info("openai")
        assert openai_info["name"] == "openai"
        assert openai_info["base_url"] == "https://api.openai.com/v1"
        assert "available_models" in openai_info
        assert "default_config" in openai_info
        
        # Test invalid provider
        with pytest.raises(HTTPException) as exc_info:
            llm_service.get_provider_info("invalid_provider")
        assert exc_info.value.status_code == 400
    
    def test_get_all_providers_info(self, llm_service):
        """Test getting all providers information."""
        all_info = llm_service.get_all_providers_info()
        
        assert isinstance(all_info, dict)
        assert len(all_info) == 4
        
        for provider_name, info in all_info.items():
            assert "name" in info
            assert "base_url" in info
            assert "available_models" in info
            assert "default_config" in info
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, llm_service):
        """Test successful API key validation."""
        with patch.object(llm_service.factory, 'validate_api_key', return_value=True) as mock_validate:
            result = await llm_service.validate_api_key("openai", "sk-test123")
            
            assert result is True
            mock_validate.assert_called_once_with("openai", "sk-test123")
    
    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, llm_service):
        """Test API key validation failure."""
        with patch.object(llm_service.factory, 'validate_api_key', return_value=False) as mock_validate:
            result = await llm_service.validate_api_key("openai", "invalid-key")
            
            assert result is False
            mock_validate.assert_called_once_with("openai", "invalid-key")
    
    @pytest.mark.asyncio
    async def test_validate_api_key_exception_handling(self, llm_service):
        """Test API key validation exception handling."""
        with patch.object(llm_service.factory, 'validate_api_key', side_effect=Exception("Network error")):
            result = await llm_service.validate_api_key("openai", "sk-test123")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_service):
        """Test successful response generation."""
        expected_response = "Generated response"
        
        with patch.object(llm_service.factory, 'generate_response', return_value=expected_response) as mock_generate:
            result = await llm_service.generate_response(
                "openai", "gpt-3.5-turbo", "Hello", "sk-test123"
            )
            
            assert result == expected_response
            mock_generate.assert_called_once_with(
                "openai", "gpt-3.5-turbo", "Hello", "sk-test123", None
            )
    
    @pytest.mark.asyncio
    async def test_generate_response_with_config(self, llm_service):
        """Test response generation with custom config."""
        expected_response = "Generated response"
        config = {"temperature": 0.8, "max_tokens": 500}
        
        with patch.object(llm_service.factory, 'generate_response', return_value=expected_response) as mock_generate:
            result = await llm_service.generate_response(
                "openai", "gpt-3.5-turbo", "Hello", "sk-test123", config
            )
            
            assert result == expected_response
            mock_generate.assert_called_once_with(
                "openai", "gpt-3.5-turbo", "Hello", "sk-test123", config
            )
    
    @pytest.mark.asyncio
    async def test_retry_logic_success_after_failure(self, llm_service, mock_client):
        """Test retry logic succeeds after initial failures."""
        # Mock the factory method to fail twice then succeed
        mock_operation = AsyncMock()
        mock_operation.side_effect = [
            httpx.TimeoutException("Timeout 1"),
            httpx.TimeoutException("Timeout 2"),
            "Success"
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up test
            result = await llm_service._retry_operation(mock_operation, "arg1", "arg2")
            
            assert result == "Success"
            assert mock_operation.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_logic_max_retries_exceeded(self, llm_service):
        """Test retry logic when max retries are exceeded."""
        mock_operation = AsyncMock()
        mock_operation.side_effect = httpx.TimeoutException("Persistent timeout")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up test
            with pytest.raises(httpx.TimeoutException):
                await llm_service._retry_operation(mock_operation, "arg1")
            
            assert mock_operation.call_count == 3  # max_retries
    
    @pytest.mark.asyncio
    async def test_retry_logic_no_retry_on_http_exception(self, llm_service):
        """Test that HTTP exceptions are not retried."""
        mock_operation = AsyncMock()
        mock_operation.side_effect = HTTPException(status_code=401, detail="Unauthorized")
        
        with pytest.raises(HTTPException):
            await llm_service._retry_operation(mock_operation, "arg1")
        
        assert mock_operation.call_count == 1  # No retries
    
    @pytest.mark.asyncio
    async def test_close(self, llm_service):
        """Test closing the service."""
        with patch.object(llm_service.factory, 'close', new_callable=AsyncMock) as mock_close:
            await llm_service.close()
            mock_close.assert_called_once()


class TestLLMClientFactory:
    """Test cases for LLM client factory."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def factory(self, mock_client):
        """Create factory instance with mock client."""
        return LLMClientFactory(client=mock_client)
    
    def test_initialization(self, factory):
        """Test factory initialization."""
        assert factory.client is not None
        assert len(factory._providers) == 4
        assert "openai" in factory._providers
        assert "anthropic" in factory._providers
        assert "openrouter" in factory._providers
        assert "gemini" in factory._providers
    
    def test_get_provider_success(self, factory):
        """Test getting a provider successfully."""
        provider = factory.get_provider("openai")
        assert isinstance(provider, OpenAIProvider)
        assert provider.provider_name == "openai"
    
    def test_get_provider_unsupported(self, factory):
        """Test getting an unsupported provider."""
        with pytest.raises(HTTPException) as exc_info:
            factory.get_provider("unsupported")
        
        assert exc_info.value.status_code == 400
        assert "not supported" in exc_info.value.detail
    
    def test_get_supported_providers(self, factory):
        """Test getting supported providers list."""
        providers = factory.get_supported_providers()
        assert set(providers) == {"openai", "anthropic", "openrouter", "gemini"}
    
    def test_get_all_providers(self, factory):
        """Test getting all provider instances."""
        providers = factory.get_all_providers()
        
        assert len(providers) == 4
        assert isinstance(providers["openai"], OpenAIProvider)
        assert isinstance(providers["anthropic"], AnthropicProvider)
        assert isinstance(providers["openrouter"], OpenRouterProvider)
        assert isinstance(providers["gemini"], GeminiProvider)
    
    @pytest.mark.asyncio
    async def test_validate_api_key(self, factory):
        """Test API key validation through factory."""
        with patch.object(factory._providers["openai"], 'validate_api_key', return_value=True) as mock_validate:
            result = await factory.validate_api_key("openai", "sk-test123")
            
            assert result is True
            mock_validate.assert_called_once_with("sk-test123")
    
    @pytest.mark.asyncio
    async def test_generate_response(self, factory):
        """Test response generation through factory."""
        expected_response = "Generated response"
        
        with patch.object(factory._providers["openai"], 'generate_response', return_value=expected_response) as mock_generate:
            result = await factory.generate_response(
                "openai", "gpt-3.5-turbo", "Hello", "sk-test123"
            )
            
            assert result == expected_response
            mock_generate.assert_called_once_with("gpt-3.5-turbo", "Hello", "sk-test123", None)
    
    def test_get_available_models(self, factory):
        """Test getting available models through factory."""
        models = factory.get_available_models("openai")
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gpt-4" in models
    
    def test_get_all_available_models(self, factory):
        """Test getting all available models through factory."""
        all_models = factory.get_all_available_models()
        
        assert isinstance(all_models, dict)
        assert len(all_models) == 4
        for provider, models in all_models.items():
            assert isinstance(models, list)
            assert len(models) > 0
    
    @pytest.mark.asyncio
    async def test_close(self, factory, mock_client):
        """Test closing the factory."""
        await factory.close()
        mock_client.aclose.assert_called_once()