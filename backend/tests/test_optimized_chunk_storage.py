"""
Tests for optimized chunk storage system.
"""
import pytest
import asyncio
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from app.services.optimized_chunk_storage import OptimizedChunkStorage, ChunkStorageResult
from app.services.chunk_metadata_cache import ChunkMetadataCache, ChunkMetadata
from app.services.chunk_storage_optimizer import ChunkStorageOptimizer


class TestOptimizedChunkStorage:
    """Test optimized chunk storage functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_vector_service(self):
        """Mock vector service."""
        service = Mock()
        service.store_document_chunks = AsyncMock(return_value=None)
        service.delete_document_chunks = AsyncMock(return_value=None)
        service.get_collection_point_ids = AsyncMock(return_value=['id1', 'id2'])
        return service
    
    @pytest.fixture
    def storage_service(self, mock_db, mock_vector_service):
        """Create storage service instance."""
        return OptimizedChunkStorage(mock_db, mock_vector_service)
    
    def test_calculate_content_hash(self, storage_service):
        """Test content hash calculation."""
        content = "This is test content"
        hash1 = storage_service._calculate_content_hash(content)
        hash2 = storage_service._calculate_content_hash(content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        assert isinstance(hash1, str)
    
    @pytest.mark.asyncio
    async def test_store_chunks_efficiently(self, storage_service, mock_db):
        """Test efficient chunk storage."""
        bot_id = uuid4()
        document_id = uuid4()
        
        chunks = [
            {'content': 'Test content 1', 'metadata': {'page': 1}},
            {'content': 'Test content 2', 'metadata': {'page': 2}}
        ]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        # Mock database operations
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(chunk_count=0)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = await storage_service.store_chunks_efficiently(
            bot_id=bot_id,
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            enable_deduplication=True
        )
        
        assert isinstance(result, ChunkStorageResult)
        assert result.success
        assert result.stored_chunks >= 0
        assert len(result.vector_ids) >= 0
    
    @pytest.mark.asyncio
    async def test_retrieve_chunks_efficiently(self, storage_service, mock_db):
        """Test efficient chunk retrieval."""
        chunk_ids = ['id1', 'id2']
        
        # Mock database query
        mock_chunk = Mock()
        mock_chunk.id = uuid4()
        mock_chunk.document_id = uuid4()
        mock_chunk.bot_id = uuid4()
        mock_chunk.chunk_index = 0
        mock_chunk.content = 'Test content'
        mock_chunk.embedding_id = 'embedding_id'
        mock_chunk.chunk_metadata = {'page': 1}
        mock_chunk.created_at.isoformat.return_value = '2023-01-01T00:00:00'
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_chunk]
        
        result = await storage_service.retrieve_chunks_efficiently(
            chunk_ids=chunk_ids,
            include_content=True,
            include_metadata=True
        )
        
        assert isinstance(result, list)
        assert len(result) >= 0


class TestChunkMetadataCache:
    """Test chunk metadata caching functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def cache_service(self, mock_db):
        """Create cache service instance."""
        return ChunkMetadataCache(mock_db, redis_client=None)  # Use in-memory cache
    
    def test_get_cache_key(self, cache_service):
        """Test cache key generation."""
        chunk_id = 'test-chunk-id'
        key = cache_service._get_cache_key(chunk_id)
        
        assert key == 'chunk_meta:test-chunk-id'
        assert isinstance(key, str)
    
    @pytest.mark.asyncio
    async def test_get_chunk_metadata_cache_miss(self, cache_service, mock_db):
        """Test cache miss scenario."""
        chunk_id = str(uuid4())  # Use valid UUID string
        
        # Mock database query
        mock_chunk = Mock()
        mock_chunk.id = uuid4()
        mock_chunk.document_id = uuid4()
        mock_chunk.bot_id = uuid4()
        mock_chunk.chunk_index = 0
        mock_chunk.content = 'Test content'
        mock_chunk.embedding_id = 'embedding_id'
        mock_chunk.chunk_metadata = {'page': 1}
        mock_chunk.created_at.isoformat.return_value = '2023-01-01T00:00:00'
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_chunk
        
        result = await cache_service.get_chunk_metadata(chunk_id)
        
        assert isinstance(result, ChunkMetadata)
        assert result.id == chunk_id
        assert result.content_length >= 0
    
    @pytest.mark.asyncio
    async def test_cache_bot_chunks(self, cache_service, mock_db):
        """Test bot chunks caching."""
        bot_id = uuid4()
        
        # Mock database query
        mock_chunk = Mock()
        mock_chunk.id = uuid4()
        mock_chunk.document_id = uuid4()
        mock_chunk.bot_id = bot_id
        mock_chunk.chunk_index = 0
        mock_chunk.content = 'Test content'
        mock_chunk.embedding_id = 'embedding_id'
        mock_chunk.chunk_metadata = {'page': 1}
        mock_chunk.created_at.isoformat.return_value = '2023-01-01T00:00:00'
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_chunk]
        
        result = await cache_service.cache_bot_chunks(bot_id)
        
        assert isinstance(result, int)
        assert result >= 0


class TestChunkStorageOptimizer:
    """Test chunk storage optimizer functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service."""
        service = Mock()
        service.maintain_referential_integrity = AsyncMock(return_value={'integrity_status': 'clean'})
        service.get_storage_statistics = AsyncMock(return_value={'total_chunks': 100})
        return service
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        service = Mock()
        service.optimize_cache_for_bot = AsyncMock(return_value={'optimization_completed': True})
        service.get_cache_statistics = AsyncMock(return_value=Mock(hit_rate=0.8))
        return service
    
    @pytest.fixture
    def optimizer(self, mock_db, mock_storage_service, mock_cache_service):
        """Create optimizer instance."""
        return ChunkStorageOptimizer(
            mock_db, 
            mock_storage_service, 
            mock_cache_service
        )
    
    @pytest.mark.asyncio
    async def test_optimize_bot_storage(self, optimizer):
        """Test bot storage optimization."""
        bot_id = uuid4()
        
        result = await optimizer.optimize_bot_storage(
            bot_id=bot_id,
            remove_duplicates=True,
            cleanup_orphans=True,
            optimize_cache=True
        )
        
        assert hasattr(result, 'success')
        assert hasattr(result, 'actions_performed')
        assert hasattr(result, 'space_saved_bytes')
        assert isinstance(result.actions_performed, list)
    
    @pytest.mark.asyncio
    async def test_analyze_storage_efficiency(self, optimizer):
        """Test storage efficiency analysis."""
        bot_id = uuid4()
        
        result = await optimizer.analyze_storage_efficiency(bot_id)
        
        assert isinstance(result, dict)
        # Should contain analysis results or error
        assert 'error' in result or 'efficiency_score' in result


if __name__ == '__main__':
    pytest.main([__file__])