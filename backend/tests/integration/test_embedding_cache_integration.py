"""
Integration tests for the embedding cache service using real Redis.
"""
import asyncio
import pytest
import time
from app.services.embedding_cache_service import EmbeddingCacheService


@pytest.mark.asyncio
class TestEmbeddingCacheIntegration:
    """Integration test cases for EmbeddingCacheService with real Redis."""
    
    @pytest.fixture
    async def cache_service(self):
        """Create a cache service with real Redis connection."""
        service = EmbeddingCacheService("redis://redis:6379")
        await service.initialize()
        
        # Clear any existing cache data
        await service.clear_cache()
        
        yield service
        
        # Cleanup
        await service.clear_cache()
        await service.close()
    
    async def test_cache_embedding_and_retrieval(self, cache_service):
        """Test caching and retrieving embeddings."""
        text = "hello world"
        provider = "openai"
        model = "text-embedding-ada-002"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Cache the embedding
        result = await cache_service.cache_embedding(text, provider, model, embedding)
        assert result is True
        
        # Retrieve the cached embedding
        cached_embedding = await cache_service.get_cached_embedding(text, provider, model)
        assert cached_embedding == embedding
        
        # Check stats
        stats = await cache_service.get_cache_stats()
        assert stats.cache_hits == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 1.0
    
    async def test_cache_miss(self, cache_service):
        """Test cache miss scenario."""
        text = "nonexistent text"
        provider = "openai"
        model = "text-embedding-ada-002"
        
        # Try to retrieve non-cached embedding
        cached_embedding = await cache_service.get_cached_embedding(text, provider, model)
        assert cached_embedding is None
        
        # Check stats
        stats = await cache_service.get_cache_stats()
        assert stats.cache_misses == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 0.0
    
    async def test_batch_caching_and_retrieval(self, cache_service):
        """Test batch caching and retrieval."""
        texts = ["hello", "world", "test"]
        provider = "openai"
        model = "text-embedding-ada-002"
        embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        
        # Cache embeddings in batch
        cached_count = await cache_service.cache_embeddings_batch(
            texts, provider, model, embeddings
        )
        assert cached_count == 3
        
        # Retrieve embeddings in batch
        retrieved_embeddings, missing_indices = await cache_service.get_cached_embeddings_batch(
            texts, provider, model
        )
        
        assert len(retrieved_embeddings) == 3
        assert missing_indices == []  # No missing embeddings
        assert retrieved_embeddings[0] == [0.1, 0.2]
        assert retrieved_embeddings[1] == [0.3, 0.4]
        assert retrieved_embeddings[2] == [0.5, 0.6]
    
    async def test_partial_batch_cache_hit(self, cache_service):
        """Test batch retrieval with partial cache hits."""
        texts = ["cached", "not_cached", "also_cached"]
        provider = "openai"
        model = "text-embedding-ada-002"
        
        # Cache only first and third texts
        await cache_service.cache_embedding("cached", provider, model, [0.1, 0.2])
        await cache_service.cache_embedding("also_cached", provider, model, [0.5, 0.6])
        
        # Retrieve batch
        retrieved_embeddings, missing_indices = await cache_service.get_cached_embeddings_batch(
            texts, provider, model
        )
        
        assert len(retrieved_embeddings) == 3
        assert missing_indices == [1]  # Only middle text is missing
        assert retrieved_embeddings[0] == [0.1, 0.2]
        assert retrieved_embeddings[1] is None
        assert retrieved_embeddings[2] == [0.5, 0.6]
    
    async def test_text_normalization_consistency(self, cache_service):
        """Test that text normalization provides consistent cache keys."""
        provider = "openai"
        model = "text-embedding-ada-002"
        embedding = [0.1, 0.2, 0.3]
        
        # Cache with extra whitespace
        await cache_service.cache_embedding("  hello   world  ", provider, model, embedding)
        
        # Retrieve with normalized text
        cached_embedding = await cache_service.get_cached_embedding("hello world", provider, model)
        assert cached_embedding == embedding
        
        # Retrieve with different case (should work due to case insensitive normalization)
        cached_embedding = await cache_service.get_cached_embedding("Hello World", provider, model)
        assert cached_embedding == embedding
    
    async def test_provider_model_isolation(self, cache_service):
        """Test that different providers/models are isolated."""
        text = "hello world"
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.4, 0.5, 0.6]
        
        # Cache same text with different providers
        await cache_service.cache_embedding(text, "openai", "model1", embedding1)
        await cache_service.cache_embedding(text, "gemini", "model1", embedding2)
        
        # Retrieve should return different embeddings
        cached1 = await cache_service.get_cached_embedding(text, "openai", "model1")
        cached2 = await cache_service.get_cached_embedding(text, "gemini", "model1")
        
        assert cached1 == embedding1
        assert cached2 == embedding2
        assert cached1 != cached2
    
    async def test_cache_clear_all(self, cache_service):
        """Test clearing all cache entries."""
        # Cache some embeddings
        await cache_service.cache_embedding("text1", "openai", "model1", [0.1, 0.2])
        await cache_service.cache_embedding("text2", "gemini", "model1", [0.3, 0.4])
        
        # Verify they're cached
        cached1 = await cache_service.get_cached_embedding("text1", "openai", "model1")
        cached2 = await cache_service.get_cached_embedding("text2", "gemini", "model1")
        assert cached1 is not None
        assert cached2 is not None
        
        # Clear all cache
        await cache_service.clear_cache()
        
        # Verify cache is empty
        cached1 = await cache_service.get_cached_embedding("text1", "openai", "model1")
        cached2 = await cache_service.get_cached_embedding("text2", "gemini", "model1")
        assert cached1 is None
        assert cached2 is None
    
    async def test_cache_clear_filtered(self, cache_service):
        """Test clearing cache entries with provider filter."""
        # Cache embeddings for different providers
        await cache_service.cache_embedding("text1", "openai", "model1", [0.1, 0.2])
        await cache_service.cache_embedding("text2", "gemini", "model1", [0.3, 0.4])
        
        # Clear only openai cache
        await cache_service.clear_cache(provider="openai")
        
        # Verify only openai cache is cleared
        cached1 = await cache_service.get_cached_embedding("text1", "openai", "model1")
        cached2 = await cache_service.get_cached_embedding("text2", "gemini", "model1")
        assert cached1 is None
        assert cached2 == [0.3, 0.4]
    
    async def test_cache_stats_tracking(self, cache_service):
        """Test cache statistics tracking."""
        # Start with clean stats
        stats = await cache_service.get_cache_stats()
        initial_requests = stats.total_requests
        
        # Cache an embedding
        await cache_service.cache_embedding("text1", "openai", "model1", [0.1, 0.2])
        
        # Hit the cache
        await cache_service.get_cached_embedding("text1", "openai", "model1")
        
        # Miss the cache
        await cache_service.get_cached_embedding("text2", "openai", "model1")
        
        # Check updated stats
        stats = await cache_service.get_cache_stats()
        assert stats.total_requests == initial_requests + 2
        assert stats.cache_hits >= 1
        assert stats.cache_misses >= 1
        assert stats.total_entries >= 1
    
    async def test_empty_text_handling(self, cache_service):
        """Test handling of empty or whitespace-only text."""
        # Try to cache empty text
        result = await cache_service.cache_embedding("", "openai", "model1", [0.1, 0.2])
        assert result is False
        
        # Try to cache whitespace-only text
        result = await cache_service.cache_embedding("   ", "openai", "model1", [0.1, 0.2])
        assert result is False
        
        # Try to retrieve empty text
        cached = await cache_service.get_cached_embedding("", "openai", "model1")
        assert cached is None
    
    async def test_empty_embedding_handling(self, cache_service):
        """Test handling of empty embeddings."""
        # Try to cache empty embedding
        result = await cache_service.cache_embedding("text", "openai", "model1", [])
        assert result is False
    
    async def test_concurrent_access(self, cache_service):
        """Test concurrent cache access."""
        text = "concurrent test"
        provider = "openai"
        model = "model1"
        embedding = [0.1, 0.2, 0.3]
        
        # Cache the embedding
        await cache_service.cache_embedding(text, provider, model, embedding)
        
        # Concurrent retrieval
        async def retrieve_embedding():
            return await cache_service.get_cached_embedding(text, provider, model)
        
        # Run multiple concurrent retrievals
        tasks = [retrieve_embedding() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should return the same embedding
        for result in results:
            assert result == embedding