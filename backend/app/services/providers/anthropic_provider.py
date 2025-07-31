"""
Anthropic provider implementation.
"""
from typing import Dict, List, Optional, Any
import httpx
from fastapi import HTTPException, status

from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider implementation."""
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    @property
    def base_url(self) -> str:
        return "https://api.anthropic.com"
    
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Get headers for Anthropic API requests."""
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate Anthropic API key by making a minimal test request."""
        try:
            url = f"{self.base_url}/v1/messages"
            headers = self.get_headers(api_key)
            
            # Make a minimal test request
            test_payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            response = await self.client.post(url, headers=headers, json=test_payload)
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
        """Generate response using Anthropic API."""
        url = f"{self.base_url}/v1/messages"
        headers = self.get_headers(api_key)
        
        # Merge default config with provided config
        default_config = self.get_default_config()
        if config:
            default_config.update(config)
        
        payload = {
            "model": model,
            "max_tokens": default_config.get("max_tokens", 1000),
            "temperature": default_config.get("temperature", 0.7),
            "messages": [{"role": "user", "content": prompt}]
        }
        
        # Add top_p if specified
        if "top_p" in default_config:
            payload["top_p"] = default_config["top_p"]
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data["content"][0]["text"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Anthropic API key"
                )
            elif e.response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Anthropic API rate limit exceeded"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Anthropic API error: {e.response.status_code}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate Anthropic response: {str(e)}"
            )
    
    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models (static fallback)."""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    async def _fetch_models_from_api(self, api_key: str) -> List[str]:
        """
        Fetch available models from Anthropic API.
        Note: Anthropic doesn't have a models endpoint, so we use the static list.
        """
        # Anthropic doesn't provide a models endpoint, so we return the static list
        # but we could potentially test each model to see which ones work
        return self.get_available_models()