"""
Unit tests for Qdrant vector store implementation and bot isolation.
"""
import asyncio
import uuid
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

import pytest
from fastapi import HTTPException

from app.services.vector_store import (
    VectorStoreInterface,
    QdrantVectorStore,
    VectorStoreFactory,
    VectorService
)


class TestVectorStoreInterface:
    """Test the vector store interface contract."""
    
    def test_interface_methods_exist(self):
        """Test that all required methods exist in the interface."""
        required_methods = [
            'create_collection',
            'delete_collection',
            'collection_exists',
            'store_embeddings',
            'search_similar',
            'delete_embeddings',
            'get_collection_info',
            'close'
        ]
        
        for method in required_methods:
            assert hasattr(VectorStoreInterface, method)
            assert callable(getattr(VectorStoreInterface, method))


class TestQdrantVectorStore:
    """Test Qdrant vector store implementation."""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client."""
        with patch('app.services.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def qdrant_store(self, mock_qdrant_client):
        """Create Qdrant vector store with mocked client."""
        return QdrantVectorStore(url="http://test:6333")
    
    @pytest.mark.asyncio
    async def test_create_collection_success(self, qdrant_store, mock_qdrant_client):
        """Test successful collection creation."""
        bot_id = str(uuid.uuid4())
        dimension = 384
        
        # Mock collection doesn't exist
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        # Mock successful creation
        mock_qdrant_client.create_collection.return_value = None
        
        result = await qdrant_store.create_collection(bot_id, dimension)
        
        assert result is True
        mock_qdrant_client.create_collection.assert_called_once()
        
        # Verify collection name format
        call_args = mock_qdrant_client.create_collection.call_args
        assert call_args[1]['collection_name'] == f"bot_{bot_id}"
    
    @pytest.mark.asyncio
    async def test_create_collection_already_exists(self, qdrant_store, mock_qdrant_client):
        """Test collection creation when collection already exists."""
        bot_id = str(uuid.uuid4())
        dimension = 384
        
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.name = f"bot_{bot_id}"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        result = await qdrant_store.create_collection(bot_id, dimension)
        
        assert result is True
        mock_qdrant_client.create_collection.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_collection_exists(self, qdrant_store, mock_qdrant_client):
        """Test collection existence check."""
        bot_id = str(uuid.uuid4())
        
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.name = f"bot_{bot_id}"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        result = await qdrant_store.collection_exists(bot_id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_collection_not_exists(self, qdrant_store, mock_qdrant_client):
        """Test collection existence check when collection doesn't exist."""
        bot_id = str(uuid.uuid4())
        
        # Mock collection doesn't exist
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        result = await qdrant_store.collection_exists(bot_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_store_embeddings_success(self, qdrant_store, mock_qdrant_client):
        """Test successful embedding storage."""
        bot_id = str(uuid.uuid4())
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        texts = ["text1", "text2"]
        metadata = [{"doc_id": "1"}, {"doc_id": "2"}]
        
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.name = f"bot_{bot_id}"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        # Mock successful upsert
        mock_qdrant_client.upsert.return_value = None
        
        result = await qdrant_store.store_embeddings(bot_id, embeddings, texts, metadata)
        
        assert len(result) == 2
        assert all(isinstance(id, str) for id in result)
        mock_qdrant_client.upsert.assert_called()
    
    @pytest.mark.asyncio
    async def test_store_embeddings_collection_not_exists(self, qdrant_store, mock_qdrant_client):
        """Test embedding storage when collection doesn't exist."""
        bot_id = str(uuid.uuid4())
        embeddings = [[0.1, 0.2, 0.3]]
        texts = ["text1"]
        metadata = [{"doc_id": "1"}]
        
        # Mock collection doesn't exist
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        with pytest.raises(HTTPException) as exc_info:
            await qdrant_store.store_embeddings(bot_id, embeddings, texts, metadata)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_search_similar_success(self, qdrant_store, mock_qdrant_client):
        """Test successful similarity search."""
        bot_id = str(uuid.uuid4())
        query_embedding = [0.1, 0.2, 0.3]
        
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.name = f"bot_{bot_id}"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        # Mock search results
        mock_hit = Mock()
        mock_hit.id = "test_id"
        mock_hit.score = 0.95
        mock_hit.payload = {"text": "test text", "bot_id": bot_id, "doc_id": "1"}
        mock_qdrant_client.search.return_value = [mock_hit]
        
        results = await qdrant_store.search_similar(bot_id, query_embedding, top_k=5)
        
        assert len(results) == 1
        assert results[0]["id"] == "test_id"
        assert results[0]["score"] == 0.95
        assert results[0]["text"] == "test text"
        assert "doc_id" in results[0]["metadata"]
        assert "bot_id" not in results[0]["metadata"]  # Should be filtered out
    
    @pytest.mark.asyncio
    async def test_delete_embeddings_success(self, qdrant_store, mock_qdrant_client):
        """Test successful embedding deletion."""
        bot_id = str(uuid.uuid4())
        ids = ["id1", "id2"]
        
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.name = f"bot_{bot_id}"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        # Mock successful deletion
        mock_qdrant_client.delete.return_value = None
        
        result = await qdrant_store.delete_embeddings(bot_id, ids)
        
        assert result is True
        mock_qdrant_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_collection_success(self, qdrant_store, mock_qdrant_client):
        """Test successful collection deletion."""
        bot_id = str(uuid.uuid4())
        
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.name = f"bot_{bot_id}"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        # Mock successful deletion
        mock_qdrant_client.delete_collection.return_value = None
        
        result = await qdrant_store.delete_collection(bot_id)
        
        assert result is True
        mock_qdrant_client.delete_collection.assert_called_once_with(f"bot_{bot_id}")
    
    @pytest.mark.asyncio
    async def test_get_collection_info_success(self, qdrant_store, mock_qdrant_client):
        """Test successful collection info retrieval."""
        bot_id = str(uuid.uuid4())
        
        # Mock collection exists
        mock_collection = Mock()
        mock_collection.name = f"bot_{bot_id}"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        # Mock collection info
        mock_info = Mock()
        mock_info.vectors_count = 100
        mock_info.indexed_vectors_count = 100
        mock_info.points_count = 100
        mock_info.segments_count = 1
        mock_info.status = "green"
        mock_info.optimizer_status = "ok"
        mock_info.config = Mock()
        mock_info.config.params = Mock()
        mock_info.config.params.vectors = Mock()
        mock_info.config.params.vectors.size = 384
        mock_info.config.params.vectors.distance = "Cosine"
        
        mock_qdrant_client.get_collection.return_value = mock_info
        
        result = await qdrant_store.get_collection_info(bot_id)
        
        assert result["bot_id"] == bot_id
        assert result["vectors_count"] == 100
        assert result["config"]["vector_size"] == 384


class TestVectorStoreFactory:
    """Test vector store factory."""
    
    def test_create_qdrant_store(self):
        """Test creating Qdrant store."""
        with patch('app.services.vector_store.QdrantClient'):
            store = VectorStoreFactory.create_vector_store()
            assert isinstance(store, QdrantVectorStore)
    
    def test_create_qdrant_store_with_url(self):
        """Test creating Qdrant store with custom URL."""
        with patch('app.services.vector_store.QdrantClient'):
            store = VectorStoreFactory.create_vector_store(url="http://custom:6333")
            assert isinstance(store, QdrantVectorStore)
            assert store.url == "http://custom:6333"
    
    def test_get_supported_types(self):
        """Test getting supported store types."""
        types = VectorStoreFactory.get_supported_types()
        assert types == ["qdrant"]


class TestVectorService:
    """Test high-level vector service."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        mock_store = Mock(spec=VectorStoreInterface)
        mock_store.create_collection = AsyncMock(return_value=True)
        mock_store.delete_collection = AsyncMock(return_value=True)
        mock_store.store_embeddings = AsyncMock(return_value=["id1", "id2"])
        mock_store.search_similar = AsyncMock(return_value=[
            {"id": "id1", "score": 0.95, "text": "test", "metadata": {}}
        ])
        mock_store.delete_embeddings = AsyncMock(return_value=True)
        mock_store.get_collection_info = AsyncMock(return_value={"bot_id": "test"})
        mock_store.close = AsyncMock()
        return mock_store
    
    @pytest.fixture
    def vector_service(self, mock_vector_store):
        """Create vector service with mock store."""
        return VectorService(vector_store=mock_vector_store)
    
    @pytest.mark.asyncio
    async def test_initialize_bot_collection(self, vector_service, mock_vector_store):
        """Test bot collection initialization."""
        bot_id = str(uuid.uuid4())
        dimension = 384
        
        result = await vector_service.initialize_bot_collection(bot_id, dimension)
        
        assert result is True
        mock_vector_store.create_collection.assert_called_once_with(bot_id, dimension)
    
    @pytest.mark.asyncio
    async def test_delete_bot_collection(self, vector_service, mock_vector_store):
        """Test bot collection deletion."""
        bot_id = str(uuid.uuid4())
        
        result = await vector_service.delete_bot_collection(bot_id)
        
        assert result is True
        mock_vector_store.delete_collection.assert_called_once_with(bot_id)
    
    @pytest.mark.asyncio
    async def test_store_document_chunks(self, vector_service, mock_vector_store):
        """Test storing document chunks."""
        bot_id = str(uuid.uuid4())
        chunks = [
            {
                "embedding": [0.1, 0.2, 0.3],
                "text": "chunk1",
                "metadata": {"doc_id": "1", "chunk_index": 0}
            },
            {
                "embedding": [0.4, 0.5, 0.6],
                "text": "chunk2",
                "metadata": {"doc_id": "1", "chunk_index": 1}
            }
        ]
        
        result = await vector_service.store_document_chunks(bot_id, chunks)
        
        assert result == ["id1", "id2"]
        mock_vector_store.store_embeddings.assert_called_once()
        
        # Verify call arguments
        call_args = mock_vector_store.store_embeddings.call_args
        assert call_args[0][0] == bot_id  # bot_id
        assert len(call_args[0][1]) == 2  # embeddings
        assert len(call_args[0][2]) == 2  # texts
        assert len(call_args[0][3]) == 2  # metadata
    
    @pytest.mark.asyncio
    async def test_search_relevant_chunks(self, vector_service, mock_vector_store):
        """Test searching for relevant chunks."""
        bot_id = str(uuid.uuid4())
        query_embedding = [0.1, 0.2, 0.3]
        
        result = await vector_service.search_relevant_chunks(
            bot_id, query_embedding, top_k=5
        )
        
        assert len(result) == 1
        assert result[0]["id"] == "id1"
        mock_vector_store.search_similar.assert_called_once_with(
            bot_id, query_embedding, 5, None, {}
        )
    
    @pytest.mark.asyncio
    async def test_search_relevant_chunks_with_document_filter(self, vector_service, mock_vector_store):
        """Test searching with document filter."""
        bot_id = str(uuid.uuid4())
        query_embedding = [0.1, 0.2, 0.3]
        document_filter = "doc123"
        
        await vector_service.search_relevant_chunks(
            bot_id, query_embedding, document_filter=document_filter
        )
        
        # Verify metadata filter was applied
        call_args = mock_vector_store.search_similar.call_args
        metadata_filter = call_args[0][4]  # 5th argument
        assert metadata_filter["document_id"] == document_filter
    
    @pytest.mark.asyncio
    async def test_delete_document_chunks(self, vector_service, mock_vector_store):
        """Test deleting document chunks."""
        bot_id = str(uuid.uuid4())
        chunk_ids = ["id1", "id2"]
        
        result = await vector_service.delete_document_chunks(bot_id, chunk_ids)
        
        assert result is True
        mock_vector_store.delete_embeddings.assert_called_once_with(bot_id, chunk_ids)
    
    @pytest.mark.asyncio
    async def test_get_bot_collection_stats(self, vector_service, mock_vector_store):
        """Test getting bot collection statistics."""
        bot_id = str(uuid.uuid4())
        
        result = await vector_service.get_bot_collection_stats(bot_id)
        
        assert result["bot_id"] == "test"
        mock_vector_store.get_collection_info.assert_called_once_with(bot_id)


class TestBotIsolation:
    """Test bot data isolation in Qdrant implementation."""
    
    @pytest.mark.asyncio
    async def test_qdrant_bot_isolation(self):
        """Test that bots are isolated in Qdrant implementation."""
        with patch('app.services.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            store = QdrantVectorStore()
            
            bot1_id = str(uuid.uuid4())
            bot2_id = str(uuid.uuid4())
            
            # Mock collections exist
            mock_collection1 = Mock()
            mock_collection1.name = f"bot_{bot1_id}"
            mock_collection2 = Mock()
            mock_collection2.name = f"bot_{bot2_id}"
            mock_collections = Mock()
            mock_collections.collections = [mock_collection1, mock_collection2]
            mock_client.get_collections.return_value = mock_collections
            
            # Mock search results with bot_id filter
            def mock_search(collection_name, query_vector, limit, score_threshold, query_filter):
                # Verify that bot_id filter is applied
                assert query_filter is not None
                filter_conditions = query_filter.must
                bot_id_condition = next(
                    (cond for cond in filter_conditions if hasattr(cond, 'key') and cond.key == 'bot_id'),
                    None
                )
                assert bot_id_condition is not None
                
                # Return mock results based on collection
                if collection_name == f"bot_{bot1_id}":
                    mock_hit = Mock()
                    mock_hit.id = "bot1_result"
                    mock_hit.score = 0.95
                    mock_hit.payload = {"text": "bot1 text", "bot_id": bot1_id}
                    return [mock_hit]
                elif collection_name == f"bot_{bot2_id}":
                    mock_hit = Mock()
                    mock_hit.id = "bot2_result"
                    mock_hit.score = 0.90
                    mock_hit.payload = {"text": "bot2 text", "bot_id": bot2_id}
                    return [mock_hit]
                return []
            
            mock_client.search.side_effect = mock_search
            
            # Search in each bot's collection
            query_embedding = [0.1, 0.2, 0.3]
            
            bot1_results = await store.search_similar(bot1_id, query_embedding, top_k=5)
            assert len(bot1_results) == 1
            assert bot1_results[0]["id"] == "bot1_result"
            assert bot1_results[0]["text"] == "bot1 text"
            
            bot2_results = await store.search_similar(bot2_id, query_embedding, top_k=5)
            assert len(bot2_results) == 1
            assert bot2_results[0]["id"] == "bot2_result"
            assert bot2_results[0]["text"] == "bot2 text"
            
            # Verify that searches were made to correct collections
            search_calls = mock_client.search.call_args_list
            assert len(search_calls) == 2
            assert search_calls[0][1]['collection_name'] == f"bot_{bot1_id}"
            assert search_calls[1][1]['collection_name'] == f"bot_{bot2_id}"
    
    @pytest.mark.asyncio
    async def test_collection_deletion_isolation(self):
        """Test that deleting one bot's collection doesn't affect others."""
        with patch('app.services.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            store = QdrantVectorStore()
            
            bot1_id = str(uuid.uuid4())
            bot2_id = str(uuid.uuid4())
            
            # Mock both collections exist initially
            mock_collection1 = Mock()
            mock_collection1.name = f"bot_{bot1_id}"
            mock_collection2 = Mock()
            mock_collection2.name = f"bot_{bot2_id}"
            mock_collections = Mock()
            mock_collections.collections = [mock_collection1, mock_collection2]
            mock_client.get_collections.return_value = mock_collections
            
            # Verify both exist
            assert await store.collection_exists(bot1_id)
            assert await store.collection_exists(bot2_id)
            
            # Mock successful deletion
            mock_client.delete_collection.return_value = None
            
            # Delete bot1's collection
            result = await store.delete_collection(bot1_id)
            assert result is True
            
            # Verify deletion was called with correct collection name
            mock_client.delete_collection.assert_called_once_with(f"bot_{bot1_id}")
            
            # Mock collections after deletion (only bot2 remains)
            mock_collection2_only = Mock()
            mock_collection2_only.name = f"bot_{bot2_id}"
            mock_collections_after = Mock()
            mock_collections_after.collections = [mock_collection2_only]
            mock_client.get_collections.return_value = mock_collections_after
            
            # Verify bot1 is deleted but bot2 still exists
            assert not await store.collection_exists(bot1_id)
            assert await store.collection_exists(bot2_id)


if __name__ == "__main__":
    pytest.main([__file__])