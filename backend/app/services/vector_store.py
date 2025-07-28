"""
Vector store abstraction and Qdrant implementation for embedding storage and retrieval.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
from fastapi import HTTPException, status

from ..core.config import settings


logger = logging.getLogger(__name__)


class VectorStoreInterface(ABC):
    """Abstract interface for vector store implementations."""
    
    @abstractmethod
    async def create_collection(self, bot_id: str, dimension: int, **kwargs) -> bool:
        """
        Create a collection/namespace for a bot.
        
        Args:
            bot_id: Bot identifier
            dimension: Embedding dimension
            **kwargs: Additional configuration parameters
            
        Returns:
            True if collection created successfully
        """
        pass
    
    @abstractmethod
    async def delete_collection(self, bot_id: str) -> bool:
        """
        Delete a collection/namespace for a bot.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            True if collection deleted successfully
        """
        pass
    
    @abstractmethod
    async def collection_exists(self, bot_id: str) -> bool:
        """
        Check if a collection/namespace exists for a bot.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            True if collection exists
        """
        pass
    
    @abstractmethod
    async def store_embeddings(
        self,
        bot_id: str,
        embeddings: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Store embeddings with associated texts and metadata.
        
        Args:
            bot_id: Bot identifier
            embeddings: List of embedding vectors
            texts: List of original texts
            metadata: List of metadata dictionaries
            ids: Optional list of custom IDs (generated if None)
            
        Returns:
            List of stored embedding IDs
        """
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        bot_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings.
        
        Args:
            bot_id: Bot identifier
            query_embedding: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            metadata_filter: Optional metadata filter
            
        Returns:
            List of search results with id, score, text, and metadata
        """
        pass
    
    @abstractmethod
    async def delete_embeddings(self, bot_id: str, ids: List[str]) -> bool:
        """
        Delete specific embeddings by ID.
        
        Args:
            bot_id: Bot identifier
            ids: List of embedding IDs to delete
            
        Returns:
            True if embeddings deleted successfully
        """
        pass
    
    @abstractmethod
    async def get_collection_info(self, bot_id: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Dictionary with collection information
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Close the vector store connection and clean up resources."""
        pass


class QdrantVectorStore(VectorStoreInterface):
    """Qdrant vector store implementation with bot-specific namespace isolation."""
    
    def __init__(self, url: str = None):
        """
        Initialize Qdrant vector store.
        
        Args:
            url: Qdrant server URL (uses settings default if None)
        """
        self.url = url or settings.qdrant_url
        self.client = QdrantClient(url=self.url)
        self._collection_prefix = "bot_"
    
    def _get_collection_name(self, bot_id: str) -> str:
        """Get collection name for a bot."""
        return f"{self._collection_prefix}{bot_id}"
    
    async def create_collection(self, bot_id: str, dimension: int, **kwargs) -> bool:
        """Create a collection for a bot with proper configuration."""
        collection_name = self._get_collection_name(bot_id)
        
        try:
            # Check if collection already exists
            if await self.collection_exists(bot_id):
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            # Create collection with vector configuration
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE
                )
            )
            
            logger.info(f"Created collection {collection_name} with dimension {dimension}")
            return True
            
        except ResponseHandlingException as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating collection {collection_name}: {e}")
            return False
    
    async def delete_collection(self, bot_id: str) -> bool:
        """Delete a collection for a bot."""
        collection_name = self._get_collection_name(bot_id)
        
        try:
            if not await self.collection_exists(bot_id):
                logger.info(f"Collection {collection_name} does not exist")
                return True
            
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection {collection_name}")
            return True
            
        except ResponseHandlingException as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting collection {collection_name}: {e}")
            return False
    
    async def collection_exists(self, bot_id: str) -> bool:
        """Check if a collection exists for a bot."""
        collection_name = self._get_collection_name(bot_id)
        
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            return collection_name in collection_names
            
        except Exception as e:
            logger.error(f"Error checking collection existence {collection_name}: {e}")
            return False
    
    async def store_embeddings(
        self,
        bot_id: str,
        embeddings: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Store embeddings in Qdrant with bot isolation."""
        collection_name = self._get_collection_name(bot_id)
        
        if not await self.collection_exists(bot_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection for bot {bot_id} does not exist"
            )
        
        if len(embeddings) != len(texts) or len(embeddings) != len(metadata):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Embeddings, texts, and metadata must have the same length"
            )
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in embeddings]
        elif len(ids) != len(embeddings):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IDs must have the same length as embeddings"
            )
        
        try:
            # Prepare points for insertion
            points = []
            for i, (embedding, text, meta, point_id) in enumerate(zip(embeddings, texts, metadata, ids)):
                # Add text to metadata for retrieval
                full_metadata = {**meta, "text": text, "bot_id": bot_id}
                
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=full_metadata
                    )
                )
            
            # Insert points in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
            
            logger.info(f"Stored {len(embeddings)} embeddings in collection {collection_name}")
            return ids
            
        except ResponseHandlingException as e:
            logger.error(f"Failed to store embeddings in {collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store embeddings: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error storing embeddings in {collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store embeddings: {str(e)}"
            )
    
    async def search_similar(
        self,
        bot_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings in Qdrant."""
        collection_name = self._get_collection_name(bot_id)
        
        if not await self.collection_exists(bot_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection for bot {bot_id} does not exist"
            )
        
        try:
            # Build filter conditions
            filter_conditions = [
                models.FieldCondition(
                    key="bot_id",
                    match=models.MatchValue(value=bot_id)
                )
            ]
            
            # Add metadata filters if provided
            if metadata_filter:
                for key, value in metadata_filter.items():
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            
            # Perform search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=models.Filter(
                    must=filter_conditions
                ) if filter_conditions else None
            )
            
            # Format results
            results = []
            for hit in search_result:
                result = {
                    "id": str(hit.id),
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k not in ["text", "bot_id"]}
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} similar embeddings in collection {collection_name}")
            return results
            
        except ResponseHandlingException as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search embeddings: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error searching in {collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search embeddings: {str(e)}"
            )
    
    async def delete_embeddings(self, bot_id: str, ids: List[str]) -> bool:
        """Delete specific embeddings by ID."""
        collection_name = self._get_collection_name(bot_id)
        
        if not await self.collection_exists(bot_id):
            logger.warning(f"Collection {collection_name} does not exist")
            return True
        
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=ids
                )
            )
            
            logger.info(f"Deleted {len(ids)} embeddings from collection {collection_name}")
            return True
            
        except ResponseHandlingException as e:
            logger.error(f"Failed to delete embeddings from {collection_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting embeddings from {collection_name}: {e}")
            return False
    
    async def get_collection_info(self, bot_id: str) -> Dict[str, Any]:
        """Get information about a collection."""
        collection_name = self._get_collection_name(bot_id)
        
        if not await self.collection_exists(bot_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection for bot {bot_id} does not exist"
            )
        
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "bot_id": bot_id,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": info.status,
                "optimizer_status": info.optimizer_status,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance
                }
            }
            
        except ResponseHandlingException as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get collection info: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting collection info for {collection_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get collection info: {str(e)}"
            )
    
    async def close(self):
        """Close the Qdrant client connection."""
        try:
            if hasattr(self.client, 'close'):
                self.client.close()
            logger.info("Closed Qdrant client connection")
        except Exception as e:
            logger.error(f"Error closing Qdrant client: {e}")


class VectorStoreFactory:
    """Factory for creating vector store instances."""
    
    @staticmethod
    def create_vector_store(url: str = None) -> VectorStoreInterface:
        """
        Create a Qdrant vector store instance.
        
        Args:
            url: Qdrant server URL (uses settings default if None)
            
        Returns:
            QdrantVectorStore instance
        """
        return QdrantVectorStore(url=url)
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """Get list of supported vector store types."""
        return ["qdrant"]


# Service class for high-level vector operations
class VectorService:
    """High-level service for vector store operations with bot isolation."""
    
    def __init__(self, vector_store: VectorStoreInterface = None):
        """
        Initialize vector service.
        
        Args:
            vector_store: Vector store instance (creates default if None)
        """
        self.vector_store = vector_store or VectorStoreFactory.create_vector_store()
    
    async def initialize_bot_collection(self, bot_id: str, dimension: int) -> bool:
        """
        Initialize a collection for a bot.
        
        Args:
            bot_id: Bot identifier
            dimension: Embedding dimension
            
        Returns:
            True if collection initialized successfully
        """
        return await self.vector_store.create_collection(bot_id, dimension)
    
    async def delete_bot_collection(self, bot_id: str) -> bool:
        """
        Delete a bot's collection and all its data.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            True if collection deleted successfully
        """
        return await self.vector_store.delete_collection(bot_id)
    
    async def store_document_chunks(
        self,
        bot_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Store document chunks with embeddings.
        
        Args:
            bot_id: Bot identifier
            chunks: List of chunk dictionaries with 'embedding', 'text', and 'metadata'
            
        Returns:
            List of stored chunk IDs
        """
        if not chunks:
            return []
        
        embeddings = [chunk["embedding"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadata = [chunk["metadata"] for chunk in chunks]
        ids = [chunk.get("id") for chunk in chunks]
        
        # Filter out None IDs
        if any(id is None for id in ids):
            ids = None
        
        return await self.vector_store.store_embeddings(
            bot_id, embeddings, texts, metadata, ids
        )
    
    async def search_relevant_chunks(
        self,
        bot_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        document_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        
        Args:
            bot_id: Bot identifier
            query_embedding: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            document_filter: Optional document ID filter
            
        Returns:
            List of relevant chunks with scores
        """
        metadata_filter = {}
        if document_filter:
            metadata_filter["document_id"] = document_filter
        
        return await self.vector_store.search_similar(
            bot_id, query_embedding, top_k, score_threshold, metadata_filter
        )
    
    async def delete_document_chunks(self, bot_id: str, chunk_ids: List[str]) -> bool:
        """
        Delete specific document chunks.
        
        Args:
            bot_id: Bot identifier
            chunk_ids: List of chunk IDs to delete
            
        Returns:
            True if chunks deleted successfully
        """
        return await self.vector_store.delete_embeddings(bot_id, chunk_ids)
    
    async def get_bot_collection_stats(self, bot_id: str) -> Dict[str, Any]:
        """
        Get statistics about a bot's collection.
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Dictionary with collection statistics
        """
        return await self.vector_store.get_collection_info(bot_id)
    
    async def close(self):
        """Close the vector service and clean up resources."""
        await self.vector_store.close()