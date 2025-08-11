"""
Unit tests for the embedding cache service.
"""
import asyncio
import json
import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.services.embedding_cache_service import (
    EmbeddingCacheService,
    EmbeddingCacheEntry,
    CacheStats
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    mock_client.hgetall.return_value = {}
    mock_client.hset.return_value = True
    mock_client.expire.return_value = True
    mock_client.keys.return_value = []
    mock_client.delete.return_value = True
    mock_client.exists.return_value = True
    mock_client.memory_usage.return_value = 1024
    mock_client.close.return_value = None
    return mock_client


@pytest_asyncio.fixture
async def cache_service(mock_redis):
    """Create a cache service with mocked Redis."""
    service = EmbeddingCacheService("redis://localhost:6379")
    
    with patch('redis.asyncio.from_url', return_value=mock_redis):
        await service.initialize()
    
    yield service
    
    # Cleanup
    if service.redis_client:
        await service.close()


@pytest.mark.asyncio
class TestEmbeddingCacheService:
    """Test cases for EmbeddingCacheService."""
    
    async def test_initialization(self, mock_redis):
        """Test cache service initialization."""
        service = EmbeddingCacheService("redis://localhost:6379")
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            await service.initialize()
        
        assert service.redis_client is not None
        mock_redis.ping.assert_called_once()
    
    async def test_initialization_failure(self):
        """Test cache service initialization failure."""
        service = EmbeddingCacheService("redis://invalid:6379")
        
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            with pytest.raises(Exception):
                await service.initialize()
    
    async def test_text_normalization(self, cache_service):
        """Test text normalization for consistent caching."""
        # Test whitespace normalization
        normalized = cache_service._normalize_text("  hello   world  ")
        assert normalized == "hello world"
        
        # Test case insensitive normalization
        normalized = cache_service._normalize_text("Hello World")
        assert normalized == "hello world"
        
        # Test empty text
        normalized = cache_service._normalize_text("")
        assert normalized == ""
        
        # Test None handling
        normalized = cache_service._normalize_text(None)
        assert normalized == ""
    
    async def test_cache_key_generation(self, cache_service):
        """Test cache key generation with content-based hashing."""
        key1 = cache_service._generate_cache_key("hello world", "openai", "text-embedding-ada-002")
        key2 = cache_service._generate_cache_key("hello world", "openai", "text-embedding-ada-002")
        key3 = cache_service._generate_cache_key("hello world", "openai", "text-embedding-3-small")
        
        # Same text, provider, and model should generate same key
        assert key1 == key2
        
        # Different model should generate different key
        assert key1 != key3
        
        # Keys should have the correct prefix
        assert key1.startswith(cache_service.cache_prefix)
    
    async def test_cache_embedding_success(self, cache_service):
        """Test successful embedding caching."""
        text = "hello world"
        provider = "openai"
        model = "text-embedding-ada-002"
        embedding = [0.1, 0.2, 0.3]
        
        result = await cache_service.cache_embedding(text, provider, model, embedding)
        
        assert result is True
        cache_service.redis_client.hset.assert_called()
        cache_service.redis_client.expire.assert_called()
    
    async def test_cache_embedding_empty_text(self, cache_service):
        """Test caching with empty text."""
        result = await cache_service.cache_embedding("", "openai", "model", [0.1, 0.2])
        assert result is False
        
        result = await cache_service.cache_embedding("   ", "openai", "model", [0.1, 0.2])
        assert result is False
    
    async def test_cache_embedding_empty_embedding(self, cache_service):
        """Test caching with empty embedding."""
        result = await cache_service.cache_embedding("text", "openai", "model", [])
        assert result is False
    
    async def test_get_cached_embedding_hit(self, cache_service):
        """Test successful cache hit."""
        text = "hello world"
        provider = "openai"
        model = "text-embedding-ada-002"
        embedding = [0.1, 0.2, 0.3]
        
        # Mock Redis response
        cache_service.redis_client.hgetall.return_value = {
            'text_hash': 'hash123',
            'provider': provider,
            'model': model,
            'embedding': json.dumps(embedding),
            'created_at': str(time.time()),
            'access_count': '1',
            'last_accessed': str(time.time()),
            'text_length': str(len(text))
        }
        
        result = await cache_service.get_cached_embedding(text, provider, model)
        
        assert result == embedding
        assert cache_service.stats.cache_hits == 1
        assert cache_service.stats.total_requests == 1
    
    async def test_get_cached_embedding_miss(self, cache_service):
        """Test cache miss."""
        cache_service.redis_client.hgetall.return_value = {}
        
        result = await cache_service.get_cached_embedding("text", "openai", "model")
        
        assert result is None
        assert cache_service.stats.cache_misses == 1
        assert cache_service.stats.total_requests == 1
    
    async def test_get_cached_embedding_invalid_data(self, cache_service):
        """Test cache hit with invalid data."""
        cache_service.redis_client.hgetall.return_value = {
            'text_hash': 'hash123',
            'provider': 'openai',
            'model': 'model',
            'embedding': 'invalid_json',  # Invalid JSON
            'created_at': str(time.time()),
            'access_count': '1',
            'last_accessed': str(time.time()),
            'text_length': '10'
        }
        
        result = await cache_service.get_cached_embedding("text", "openai", "model")
        
        assert result is None
        assert cache_service.stats.cache_misses == 1
    
    async def test_batch_cache_lookup(self, cache_service):
        """Test batch cache lookup."""
        texts = ["hello", "world", "test"]
        provider = "openai"
        model = "text-embedding-ada-002"
        
        # Mock pipeline execution
        mock_pipeline = AsyncMock()
        cache_service.redis_client.pipeline.return_value = mock_pipeline
        
        # Mock results: first text cached, others not
        mock_pipeline.execute.return_value = [
            {
                'text_hash': 'hash1',
                'provider': provider,
                'model': model,
                'embedding': json.dumps([0.1, 0.2]),
                'created_at': str(time.time()),
                'access_count': '1',
                'last_accessed': str(time.time()),
                'text_length': '5'
            },
            {},  # Cache miss
            {}   # Cache miss
        ]
        
        embeddings, missing_indices = await cache_service.get_cached_embeddings_batch(
            texts, provider, model
        )
        
        assert len(embeddings) == 3
        assert embeddings[0] == [0.1, 0.2]  # Cache hit
        assert embeddings[1] is None        # Cache miss
        assert embeddings[2] is None        # Cache miss
        assert missing_indices == [1, 2]
    
    async def test_batch_cache_storage(self, cache_service):
        """Test batch cache storage."""
        texts = ["hello", "world"]
        provider = "openai"
        model = "text-embedding-ada-002"
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        
        # Mock pipeline
        mock_pipeline = AsyncMock()
        cache_service.redis_client.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [True, True, True, True]  # hset and expire for each
        
        result = await cache_service.cache_embeddings_batch(
            texts, provider, model, embeddings
        )
        
        assert result == 2  # Both embeddings cached
        mock_pipeline.execute.assert_called_once()
    
    async def test_lru_eviction(self, cache_service):
        """Test LRU eviction when cache is full."""
        # Mock cache at capacity
        cache_keys = [f"embedding_cache:key{i}" for i in range(cache_service.max_cache_size)]
        cache_service.redis_client.keys.return_value = cache_keys
        
        # Mock pipeline for access time retrieval
        mock_pipeline = AsyncMock()
        cache_service.redis_client.pipeline.return_value = mock_pipeline
        
        # Mock access times (older entries first)
        access_times = [str(time.time() - i * 100) for i in range(len(cache_keys))]
        mock_pipeline.execute.return_value = access_times
        
        await cache_service._ensure_cache_space()
        
        # Should delete oldest entries
        cache_service.redis_client.delete.assert_called()
    
    async def test_cache_stats_calculation(self, cache_service):
        """Test cache statistics calculation."""
        # Set up some stats
        cache_service.stats.cache_hits = 80
        cache_service.stats.cache_misses = 20
        cache_service.stats.total_requests = 100
        
        # Mock Redis responses for stats calculation
        cache_service.redis_client.keys.return_value = ["key1", "key2", "key3"]
        cache_service.redis_client.memory_usage.return_value = 1024
        
        stats = await cache_service.get_cache_stats()
        
        assert stats.total_requests == 100
        assert stats.cache_hits == 80
        assert stats.cache_misses == 20
        assert stats.hit_rate == 0.8
        assert stats.total_entries == 3
    
    async def test_cache_clear_all(self, cache_service):
        """Test clearing all cache entries."""
        cache_keys = ["key1", "key2", "key3"]
        cache_service.redis_client.keys.return_value = cache_keys
        
        await cache_service.clear_cache()
        
        cache_service.redis_client.delete.assert_called_with(*cache_keys)
    
    async def test_cache_clear_filtered(self, cache_service):
        """Test clearing cache entries with provider/model filter."""
        cache_keys = ["key1", "key2", "key3"]
        cache_service.redis_client.keys.return_value = cache_keys
        
        # Mock entry data
        cache_service.redis_client.hgetall.side_effect = [
            {'provider': 'openai', 'model': 'model1'},
            {'provider': 'openai', 'model': 'model2'},
            {'provider': 'gemini', 'model': 'model1'}
        ]
        
        await cache_service.clear_cache(provider="openai")
        
        # Should delete keys for openai provider
        cache_service.redis_client.delete.assert_called_with("key1", "key2")
    
    async def test_cleanup_expired_entries(self, cache_service):
        """Test cleanup of expired and invalid entries."""
        cache_keys = ["key1", "key2", "key3"]
        cache_service.redis_client.keys.return_value = cache_keys
        
        # Mock exists responses: key1 expired, key2 valid, key3 invalid data
        cache_service.redis_client.exists.side_effect = [False, True, True]
        cache_service.redis_client.hgetall.side_effect = [
            {},  # Won't be called for key1
            {'embedding': json.dumps([0.1, 0.2])},  # Valid
            {'embedding': 'invalid_json'}  # Invalid
        ]
        
        await cache_service.cleanup_expired_entries()
        
        # Should delete key3 (invalid data)
        cache_service.redis_client.delete.assert_called()
    
    async def test_close(self, cache_service):
        """Test cache service cleanup."""
        await cache_service.close()
        cache_service.redis_client.close.assert_called_once()


class TestEmbeddingCacheEntry:
    """Test cases for EmbeddingCacheEntry."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        entry = EmbeddingCacheEntry(
            text_hash="hash123",
            provider="openai",
            model="text-embedding-ada-002",
            embedding=[0.1, 0.2, 0.3],
            created_at=time.time(),
            access_count=1,
            last_accessed=time.time(),
            text_length=10
        )
        
        data = entry.to_dict()
        
        assert isinstance(data, dict)
        assert data['text_hash'] == "hash123"
        assert data['provider'] == "openai"
        assert data['embedding'] == [0.1, 0.2, 0.3]
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'text_hash': "hash123",
            'provider': "openai",
            'model': "text-embedding-ada-002",
            'embedding': [0.1, 0.2, 0.3],
            'created_at': time.time(),
            'access_count': 1,
            'last_accessed': time.time(),
            'text_length': 10
        }
        
        entry = EmbeddingCacheEntry.from_dict(data)
        
        assert entry.text_hash == "hash123"
        assert entry.provider == "openai"
        assert entry.embedding == [0.1, 0.2, 0.3]


class TestCacheStats:
    """Test cases for CacheStats."""
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        
        # Test with no requests
        stats.calculate_hit_rate()
        assert stats.hit_rate == 0.0
        
        # Test with requests
        stats.total_requests = 100
        stats.cache_hits = 80
        stats.calculate_hit_rate()
        assert stats.hit_rate == 0.8
        
        # Test with all misses
        stats.cache_hits = 0
        stats.calculate_hit_rate()
        assert stats.hit_rate == 0.0
        
        # Test with all hits
        stats.cache_hits = 100
        stats.calculate_hit_rate()
        assert stats.hit_rate == 1.0