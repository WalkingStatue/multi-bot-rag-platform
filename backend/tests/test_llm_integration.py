"""
Integration tests for the complete LLM provider system.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi import HTTPException

from app.services.llm_service import LLMProviderService
from app.services.llm_factory import LLMClientFactory


class TestLLMIntegration:
    """Integration tests for the complete LLM system."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)
    
    @pytest.fixture
    def llm_service(self, mock_client):
        """Create LLM service instance with mock client."""
        return LLMProviderService(client=mock_client)
    
    @pytest.mark.asyncio
    async def test_complete_workflow_openai(self, llm_service, mock_client):
        """Test complete workflow with OpenAI provider."""
        # Mock API key validation
        validation_response = MagicMock()
        validation_response.status_code = 200
        
        # Mock response generation
        generation_response = MagicMock()
        generation_response.status_code = 200
        generation_response.json.return_value = {
            "choices": [{"message": {"content": "Hello! How can I help you today?"}}]
        }
        generation_response.raise_for_status = MagicMock()
        
        # Configure mock client
        mock_client.get.return_value = validation_response
        mock_client.post.return_value = generation_response
        
        # Test the complete workflow
        provider = "openai"
        model = "gpt-3.5-turbo"
        api_key = "sk-test123"
        prompt = "Hello, how are you?"
        
        # 1. Validate API key
        is_valid = await llm_service.validate_api_key(provider, api_key)
        assert is_valid is True
        
        # 2. Check if model is available
        is_model_valid = llm_service.validate_model_for_provider(provider, model)
        assert is_model_valid is True
        
        # 3. Generate response
        response = await llm_service.generate_response(
            provider, model, prompt, api_key
        )
        assert response == "Hello! How can I help you today?"
        
        # Verify the calls were made correctly
        assert mock_client.get.call_count >= 1  # API key validation
        assert mock_client.post.call_count >= 1  # Response generation
    
    @pytest.mark.asyncio
    async def test_complete_workflow_anthropic(self, llm_service, mock_client):
        """Test complete workflow with Anthropic provider."""
        # Mock API key validation
        validation_response = MagicMock()
        validation_response.status_code = 200
        
        # Mock response generation
        generation_response = MagicMock()
        generation_response.status_code = 200
        generation_response.json.return_value = {
            "content": [{"text": "Hello! I'm Claude, how can I assist you?"}]
        }
        generation_response.raise_for_status = MagicMock()
        
        # Configure mock client
        mock_client.post.return_value = validation_response  # Anthropic uses POST for validation
        mock_client.post.return_value = generation_response
        
        # Test the complete workflow
        provider = "anthropic"
        model = "claude-3-haiku-20240307"
        api_key = "sk-ant-test123"
        prompt = "Hello, how are you?"
        
        # 1. Validate API key
        is_valid = await llm_service.validate_api_key(provider, api_key)
        assert is_valid is True
        
        # 2. Check if model is available
        is_model_valid = llm_service.validate_model_for_provider(provider, model)
        assert is_model_valid is True
        
        # 3. Generate response
        response = await llm_service.generate_response(
            provider, model, prompt, api_key
        )
        assert response == "Hello! I'm Claude, how can I assist you?"
    
    @pytest.mark.asyncio
    async def test_complete_workflow_gemini(self, llm_service, mock_client):
        """Test complete workflow with Gemini provider."""
        # Mock API key validation
        validation_response = MagicMock()
        validation_response.status_code = 200
        
        # Mock response generation
        generation_response = MagicMock()
        generation_response.status_code = 200
        generation_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello! I'm Gemini, ready to help!"}]}}]
        }
        generation_response.raise_for_status = MagicMock()
        
        # Configure mock client
        mock_client.get.return_value = validation_response
        mock_client.post.return_value = generation_response
        
        # Test the complete workflow
        provider = "gemini"
        model = "gemini-pro"
        api_key = "AIza-test123"
        prompt = "Hello, how are you?"
        
        # 1. Validate API key
        is_valid = await llm_service.validate_api_key(provider, api_key)
        assert is_valid is True
        
        # 2. Check if model is available
        is_model_valid = llm_service.validate_model_for_provider(provider, model)
        assert is_model_valid is True
        
        # 3. Generate response
        response = await llm_service.generate_response(
            provider, model, prompt, api_key
        )
        assert response == "Hello! I'm Gemini, ready to help!"
    
    def test_provider_info_retrieval(self, llm_service):
        """Test retrieving information about all providers."""
        # Get all providers info
        all_info = llm_service.get_all_providers_info()
        
        # Verify all providers are present
        expected_providers = ["openai", "anthropic", "openrouter", "gemini"]
        assert set(all_info.keys()) == set(expected_providers)
        
        # Verify each provider has required information
        for provider_name, info in all_info.items():
            assert "name" in info
            assert "base_url" in info
            assert "available_models" in info
            assert "default_config" in info
            assert isinstance(info["available_models"], list)
            assert len(info["available_models"]) > 0
    
    def test_model_validation_across_providers(self, llm_service):
        """Test model validation across different providers."""
        # Test valid models for each provider
        assert llm_service.validate_model_for_provider("openai", "gpt-4") is True
        assert llm_service.validate_model_for_provider("anthropic", "claude-3-opus-20240229") is True
        assert llm_service.validate_model_for_provider("openrouter", "openai/gpt-4") is True
        assert llm_service.validate_model_for_provider("gemini", "gemini-pro") is True
        
        # Test invalid models
        assert llm_service.validate_model_for_provider("openai", "claude-3-opus") is False
        assert llm_service.validate_model_for_provider("anthropic", "gpt-4") is False
        assert llm_service.validate_model_for_provider("gemini", "gpt-3.5-turbo") is False
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, llm_service, mock_client):
        """Test error handling in the complete workflow."""
        # Test with invalid provider - should return False, not raise exception
        is_valid = await llm_service.validate_api_key("invalid_provider", "test-key")
        assert is_valid is False
        
        # Test with network error during validation
        mock_client.get.side_effect = httpx.NetworkError("Network error")
        
        is_valid = await llm_service.validate_api_key("openai", "sk-test123")
        assert is_valid is False  # Should return False on network error
        
        # Reset mock for generation test
        mock_client.reset_mock()
        mock_client.get.side_effect = None
        
        # Test with network error during generation - should raise HTTPException
        mock_client.post.side_effect = httpx.NetworkError("Network error")
        
        with pytest.raises(HTTPException):
            await llm_service.generate_response(
                "openai", "gpt-3.5-turbo", "Hello", "sk-test123"
            )
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, llm_service):
        """Test that the service initializes correctly with all components."""
        # Verify service has factory
        assert llm_service.factory is not None
        
        # Verify factory has all providers
        providers = llm_service.factory.get_all_providers()
        assert len(providers) == 4
        assert "openai" in providers
        assert "anthropic" in providers
        assert "openrouter" in providers
        assert "gemini" in providers
        
        # Verify retry configuration
        assert llm_service.max_retries == 3
        assert llm_service.retry_delay == 1.0
    
    @pytest.mark.asyncio
    async def test_custom_config_integration(self, llm_service, mock_client):
        """Test custom configuration in integration scenario."""
        # Mock response generation
        generation_response = MagicMock()
        generation_response.status_code = 200
        generation_response.json.return_value = {
            "choices": [{"message": {"content": "Custom response"}}]
        }
        generation_response.raise_for_status = MagicMock()
        mock_client.post.return_value = generation_response
        
        # Test with custom configuration
        custom_config = {
            "temperature": 0.9,
            "max_tokens": 500,
            "top_p": 0.8
        }
        
        response = await llm_service.generate_response(
            "openai", "gpt-3.5-turbo", "Hello", "sk-test123", custom_config
        )
        
        assert response == "Custom response"
        
        # Verify custom config was passed to the provider
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.9
        assert payload["max_tokens"] == 500
        assert payload["top_p"] == 0.8