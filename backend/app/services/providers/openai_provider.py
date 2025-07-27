"""
OpenAI provider implementation.
"""
from typing import Dict, List, Optional, Any
import httpx
from fastapi import HTTPException, status

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation."""
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def base_url(self) -> str:
        return "https://api.openai.com/v1"
    
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Get headers for OpenAI API requests."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate OpenAI API key by listing models."""
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
        """Generate response using OpenAI API."""
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
            "top_p": default_config.get("top_p", 1.0),
            "frequency_penalty": default_config.get("frequency_penalty", 0.0),
            "presence_penalty": default_config.get("presence_penalty", 0.0)
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid OpenAI API key"
                )
            elif e.response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="OpenAI API rate limit exceeded"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"OpenAI API error: {e.response.status_code}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate OpenAI response: {str(e)}"
            )
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4-0125-preview",
            "gpt-4-1106-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-0125"
        ]