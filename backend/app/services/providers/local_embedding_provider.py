"""
Local Sentence Transformers embedding provider implementation.
"""
import logging
from typing import List, Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException, status

from .embedding_base import BaseEmbeddingProvider


logger = logging.getLogger(__name__)


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local Sentence Transformers embedding provider implementation."""
    
    def __init__(self, client=None):
        super().__init__(client)
        self._models = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    @property
    def provider_name(self) -> str:
        return "local"
    
    @property
    def base_url(self) -> Optional[str]:
        return None  # Local provider doesn't use HTTP
    
    async def validate_api_key(self, api_key: Optional[str] = None) -> bool:
        """Local provider doesn't require API key."""
        return True
    
    def _load_model(self, model: str):
        """Load a sentence transformer model (runs in thread)."""
        try:
            from sentence_transformers import SentenceTransformer
            
            if model not in self._models:
                logger.info(f"Loading local embedding model: {model}")
                self._models[model] = SentenceTransformer(model)
            
            return self._models[model]
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="sentence-transformers library not installed. Please install it to use local embeddings."
            )
        except Exception as e:
            logger.error(f"Failed to load model {model}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load local embedding model: {str(e)}"
            )
    
    def _generate_embeddings_sync(self, texts: List[str], model: str) -> List[List[float]]:
        """Generate embeddings synchronously (runs in thread)."""
        transformer = self._load_model(model)
        embeddings = transformer.encode(texts, convert_to_tensor=False)
        
        # Convert numpy arrays to lists
        if hasattr(embeddings, 'tolist'):
            return embeddings.tolist()
        else:
            return [embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding) 
                   for embedding in embeddings]
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> List[List[float]]:
        """Generate embeddings using local Sentence Transformers."""
        if not texts:
            return []
        
        try:
            # Run the synchronous embedding generation in a thread
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self._executor,
                self._generate_embeddings_sync,
                texts,
                model
            )
            
            return embeddings
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local embedding generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate local embeddings: {str(e)}"
            )
    
    def get_available_models(self) -> List[str]:
        """Get list of available local embedding models."""
        return [
            "all-MiniLM-L6-v2",
            "all-mpnet-base-v2",
            "multi-qa-MiniLM-L6-cos-v1",
            "paraphrase-MiniLM-L6-v2",
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
        ]
    
    def get_embedding_dimension(self, model: str) -> int:
        """Get embedding dimension for local models."""
        # Common dimensions for popular models
        dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "multi-qa-MiniLM-L6-cos-v1": 384,
            "paraphrase-MiniLM-L6-v2": 384,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/multi-qa-MiniLM-L6-cos-v1": 384
        }
        
        if model in dimensions:
            return dimensions[model]
        
        # For unknown models, try to load and get dimension
        try:
            transformer = self._load_model(model)
            # Get dimension from model
            if hasattr(transformer, 'get_sentence_embedding_dimension'):
                return transformer.get_sentence_embedding_dimension()
            else:
                # Fallback: encode a test string and get dimension
                test_embedding = transformer.encode(["test"])
                return len(test_embedding[0])
        except Exception as e:
            logger.error(f"Failed to get dimension for model {model}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to determine embedding dimension for model: {model}"
            )
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for local embeddings."""
        return {
            "convert_to_tensor": False,
            "normalize_embeddings": False
        }
    
    def cleanup(self):
        """Clean up resources."""
        self._models.clear()
        if self._executor:
            self._executor.shutdown(wait=True)