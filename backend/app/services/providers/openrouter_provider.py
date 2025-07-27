"""
OpenRouter provider implementation.
"""
from typing import Dict, List, Optional, Any
import httpx
from fastapi import HTTPException, status

from .base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider implementation."""
    
    @property
    def provider_name(self) -> str:
        return "openrouter"
    
    @property
    def base_url(self) -> str:
        return "https://openrouter.ai/api/v1"
    
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Get headers for OpenRouter API requests."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://multi-bot-rag-platform.com",  # Required by OpenRouter
            "X-Title": "Multi-Bot RAG Platform"  # Optional but recommended
        }
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate OpenRouter API key by listing models."""
        try:
            url = f"{self.base_url}/models"
            headers = self.get_headers(api_key)
            
            response = await self.client.get(url, headers=headers)
            return response.status_code == 200
        except Exception:
            return False
    
    async def generate_response(
        self,
        model: str,
        prompt: str,
        api_key: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate response using OpenRouter API."""
        url = f"{self.base_url}/chat/completions"
        headers = self.get_headers(api_key)
        
        # Merge default config with provided config
        default_config = self.get_default_config()
        if config:
            default_config.update(config)
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": default_config.get("temperature", 0.7),
            "max_tokens": default_config.get("max_tokens", 1000),
            "top_p": default_config.get("top_p", 1.0)
        }
        
        # Add frequency and presence penalty if supported by the model
        if "frequency_penalty" in default_config:
            payload["frequency_penalty"] = default_config["frequency_penalty"]
        if "presence_penalty" in default_config:
            payload["presence_penalty"] = default_config["presence_penalty"]
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid OpenRouter API key"
                )
            elif e.response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="OpenRouter API rate limit exceeded"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"OpenRouter API error: {e.response.status_code}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate OpenRouter response: {str(e)}"
            )
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenRouter models."""
        return [
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "anthropic/claude-2",
            "anthropic/claude-instant-1",
            "meta-llama/llama-2-70b-chat",
            "meta-llama/llama-2-13b-chat",
            "mistralai/mixtral-8x7b-instruct",
            "mistralai/mistral-7b-instruct",
            "google/gemini-pro",
            "google/palm-2-chat-bison",
            "cohere/command",
            "cohere/command-light"
        ]