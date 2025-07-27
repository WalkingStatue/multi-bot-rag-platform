"""
Base abstract class for LLM providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import httpx


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL for the provider API."""
        pass
    
    @abstractmethod
    async def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key for this provider.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if API key is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        model: str,
        prompt: str,
        api_key: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate response using this provider.
        
        Args:
            model: Model name
            prompt: Input prompt
            api_key: API key for the provider
            config: Optional configuration parameters
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of available model names
        """
        pass
    
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Args:
            api_key: API key
            
        Returns:
            Dictionary of headers
        """
        return {"Content-Type": "application/json"}
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for this provider.
        
        Returns:
            Dictionary of default configuration values
        """
        return {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }