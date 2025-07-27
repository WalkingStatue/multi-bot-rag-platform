"""
Unit tests for individual LLM provider implementations.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from fastapi import HTTPException

from app.services.providers import (
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
    GeminiProvider
)


class TestOpenAIProvider:
    """Test cases for OpenAI provider."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create OpenAI provider instance."""
        return OpenAIProvider(mock_client)
    
    def test_provider_properties(self, provider):
        """Test provider properties."""
        assert provider.provider_name == "openai"
        assert provider.base_url == "https://api.openai.com/v1"
    
    def test_get_headers(self, provider):
        """Test header generation."""
        headers = provider.get_headers("sk-test123")
        expected = {
            "Authorization": "Bearer sk-test123",
            "Content-Type": "application/json"
        }
        assert headers == expected
    
    def test_get_available_models(self, provider):
        """Test getting available models."""
        models = provider.get_available_models()
        assert isinstance(models, list)
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert len(models) > 0
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, provider, mock_client):
        """Test successful API key validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        
        result = await provider.validate_api_key("sk-test123")
        
        assert result is True
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "https://api.openai.com/v1/models" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test123"
    
    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, provider, mock_client):
        """Test API key validation failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response
        
        result = await provider.validate_api_key("invalid-key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_api_key_exception(self, provider, mock_client):
        """Test API key validation with exception."""
        mock_client.get.side_effect = Exception("Network error")
        
        result = await provider.validate_api_key("sk-test123")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, provider, mock_client):
        """Test successful response generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello there!"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        
        result = await provider.generate_response(
            "gpt-3.5-turbo", "Hello", "sk-test123"
        )
        
        assert result == "Hello there!"
        mock_client.post.assert_called_once()
        
        # Check the payload
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "gpt-3.5-turbo"
        assert payload["messages"][0]["content"] == "Hello"
        assert payload["temperature"] == 0.7  # default
    
    @pytest.mark.asyncio
    async def test_generate_response_with_config(self, provider, mock_client):
        """Test response generation with custom config."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello there!"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        
        config = {"temperature": 0.8, "max_tokens": 500}
        result = await provider.generate_response(
            "gpt-3.5-turbo", "Hello", "sk-test123", config
        )
        
        assert result == "Hello there!"
        
        # Check the payload includes custom config
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.8
        assert payload["max_tokens"] == 500
    
    @pytest.mark.asyncio
    async def test_generate_response_auth_error(self, provider, mock_client):
        """Test response generation with auth error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
        mock_client.post.side_effect = error
        
        with pytest.raises(HTTPException) as exc_info:
            await provider.generate_response("gpt-3.5-turbo", "Hello", "invalid-key")
        
        assert exc_info.value.status_code == 401
        assert "Invalid OpenAI API key" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit(self, provider, mock_client):
        """Test response generation with rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        error = httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=mock_response)
        mock_client.post.side_effect = error
        
        with pytest.raises(HTTPException) as exc_info:
            await provider.generate_response("gpt-3.5-turbo", "Hello", "sk-test123")
        
        assert exc_info.value.status_code == 429
        assert "rate limit exceeded" in exc_info.value.detail


class TestAnthropicProvider:
    """Test cases for Anthropic provider."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create Anthropic provider instance."""
        return AnthropicProvider(mock_client)
    
    def test_provider_properties(self, provider):
        """Test provider properties."""
        assert provider.provider_name == "anthropic"
        assert provider.base_url == "https://api.anthropic.com"
    
    def test_get_headers(self, provider):
        """Test header generation."""
        headers = provider.get_headers("sk-ant-test123")
        expected = {
            "x-api-key": "sk-ant-test123",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        assert headers == expected
    
    def test_get_available_models(self, provider):
        """Test getting available models."""
        models = provider.get_available_models()
        assert isinstance(models, list)
        assert "claude-3-opus-20240229" in models
        assert "claude-3-haiku-20240307" in models
        assert len(models) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, provider, mock_client):
        """Test successful response generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Hello there!"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        
        result = await provider.generate_response(
            "claude-3-haiku-20240307", "Hello", "sk-ant-test123"
        )
        
        assert result == "Hello there!"
        mock_client.post.assert_called_once()
        
        # Check the payload
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "claude-3-haiku-20240307"
        assert payload["messages"][0]["content"] == "Hello"
        assert payload["max_tokens"] == 1000  # default


class TestGeminiProvider:
    """Test cases for Gemini provider."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create Gemini provider instance."""
        return GeminiProvider(mock_client)
    
    def test_provider_properties(self, provider):
        """Test provider properties."""
        assert provider.provider_name == "gemini"
        assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
    
    def test_get_available_models(self, provider):
        """Test getting available models."""
        models = provider.get_available_models()
        assert isinstance(models, list)
        assert "gemini-pro" in models
        assert "gemini-1.5-pro" in models
        assert len(models) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, provider, mock_client):
        """Test successful response generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello there!"}]}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        
        result = await provider.generate_response(
            "gemini-pro", "Hello", "AIza-test123"
        )
        
        assert result == "Hello there!"
        mock_client.post.assert_called_once()
        
        # Check the payload
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["contents"][0]["parts"][0]["text"] == "Hello"
        assert "safetySettings" in payload
    
    @pytest.mark.asyncio
    async def test_generate_response_blocked_by_safety(self, provider, mock_client):
        """Test response generation blocked by safety filters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"candidates": []}  # Empty candidates
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            await provider.generate_response("gemini-pro", "Hello", "AIza-test123")
        
        # The provider catches the 400 error and re-raises as 500
        assert exc_info.value.status_code == 500
        assert "safety filters" in exc_info.value.detail


class TestOpenRouterProvider:
    """Test cases for OpenRouter provider."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create OpenRouter provider instance."""
        return OpenRouterProvider(mock_client)
    
    def test_provider_properties(self, provider):
        """Test provider properties."""
        assert provider.provider_name == "openrouter"
        assert provider.base_url == "https://openrouter.ai/api/v1"
    
    def test_get_headers(self, provider):
        """Test header generation."""
        headers = provider.get_headers("sk-or-test123")
        expected = {
            "Authorization": "Bearer sk-or-test123",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://multi-bot-rag-platform.com",
            "X-Title": "Multi-Bot RAG Platform"
        }
        assert headers == expected
    
    def test_get_available_models(self, provider):
        """Test getting available models."""
        models = provider.get_available_models()
        assert isinstance(models, list)
        assert "openai/gpt-4" in models
        assert "anthropic/claude-3-opus" in models
        assert len(models) > 0