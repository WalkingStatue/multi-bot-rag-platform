# Vector Store Usage Guide

This document explains how to use the Qdrant vector store implementation in the Multi-Bot RAG Platform.

## Overview

The vector store system provides:
- **Bot-specific namespace isolation** - Each bot has its own isolated vector space
- **Qdrant integration** - Production-ready vector database with advanced features
- **High-level service interface** - Simplified operations for common tasks
- **Comprehensive error handling** - Robust error management and logging

## Architecture

```
VectorService (High-level API)
    ↓
VectorStoreInterface (Abstract interface)
    ↓
QdrantVectorStore (Qdrant implementation)
```

## Quick Start

### 1. Basic Usage

```python
from app.services.vector_store import VectorService, VectorStoreFactory

# Create vector service with default Qdrant configuration
vector_service = VectorService()

# Or specify Qdrant URL explicitly
vector_service = VectorService(
    vector_store=VectorStoreFactory.create_vector_store(url="http://localhost:6333")
)

# Initialize collection for a bot
bot_id = "your-bot-id"
dimension = 384  # Embedding dimension
await vector_service.initialize_bot_collection(bot_id, dimension)
```

### 2. Storing Document Chunks

```python
# Prepare chunks with embeddings
chunks = [
    {
        "embedding": [0.1, 0.2, 0.3, ...],  # 384-dimensional vector
        "text": "This is the original text chunk",
        "metadata": {
            "document_id": "doc123",
            "chunk_index": 0,
            "page": 1,
            "source": "manual.pdf"
        }
    },
    # ... more chunks
]

# Store chunks
chunk_ids = await vector_service.store_document_chunks(bot_id, chunks)
print(f"Stored {len(chunk_ids)} chunks")
```

### 3. Searching for Relevant Chunks

```python
# Search for similar chunks
query_embedding = [0.1, 0.2, 0.3, ...]  # Your query embedding
results = await vector_service.search_relevant_chunks(
    bot_id=bot_id,
    query_embedding=query_embedding,
    top_k=5,
    score_threshold=0.7,  # Optional minimum similarity score
    document_filter="doc123"  # Optional document filter
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Text: {result['text']}")
    print(f"Metadata: {result['metadata']}")
```

### 4. Managing Collections

```python
# Get collection statistics
stats = await vector_service.get_bot_collection_stats(bot_id)
print(f"Vectors: {stats['vectors_count']}")
print(f"Status: {stats['status']}")

# Delete specific chunks
chunk_ids_to_delete = ["chunk1", "chunk2"]
await vector_service.delete_document_chunks(bot_id, chunk_ids_to_delete)

# Delete entire bot collection
await vector_service.delete_bot_collection(bot_id)

# Clean up
await vector_service.close()
```

## Qdrant Features

### Production-Ready Vector Database

**Advantages:**
- High performance and scalability
- Advanced filtering capabilities
- Built-in clustering and replication
- REST API for external access
- Real-time updates
- ACID transactions
- Horizontal scaling

**Configuration:**
```python
# In settings
qdrant_url = "http://localhost:6333"

# Usage
qdrant_store = VectorStoreFactory.create_vector_store(url="http://localhost:6333")
```

### Advanced Search Features

```python
# Complex metadata filtering
results = await vector_service.search_relevant_chunks(
    bot_id=bot_id,
    query_embedding=query_embedding,
    top_k=10,
    score_threshold=0.8,
    metadata_filter={
        "category": "technical",
        "priority": "high",
        "document_type": "manual"
    }
)

# Score-based filtering
high_quality_results = await vector_service.search_relevant_chunks(
    bot_id=bot_id,
    query_embedding=query_embedding,
    top_k=5,
    score_threshold=0.9  # Only very similar results
)
```

## Bot Isolation

Each bot gets its own isolated namespace in Qdrant:

### Implementation Details
- Collections named `bot_{bot_id}`
- Automatic bot_id filtering in all queries
- Complete data separation at the collection level
- Independent scaling and optimization per bot

### Security Benefits
- No cross-bot data leakage
- Independent access control
- Isolated performance characteristics
- Safe concurrent operations

## Error Handling

The vector store implementation provides comprehensive error handling:

```python
from fastapi import HTTPException

try:
    await vector_service.store_document_chunks(bot_id, chunks)
except HTTPException as e:
    if e.status_code == 404:
        print("Collection not found - create it first")
        await vector_service.initialize_bot_collection(bot_id, dimension)
    elif e.status_code == 400:
        print("Invalid input data")
    else:
        print(f"Server error: {e.detail}")
```

## Integration with Embedding Service

```python
from app.services.embedding_service import EmbeddingProviderService

# Generate embeddings
embedding_service = EmbeddingProviderService()
texts = ["Text to embed", "Another text"]

embeddings = await embedding_service.generate_embeddings(
    provider="openai",
    texts=texts,
    model="text-embedding-3-small",
    api_key="your-api-key"
)

# Store with vector service
chunks = [
    {
        "embedding": embeddings[i],
        "text": texts[i],
        "metadata": {"index": i, "timestamp": "2024-01-01"}
    }
    for i in range(len(texts))
]

await vector_service.store_document_chunks(bot_id, chunks)
```

## Configuration

### Environment Variables

```env
# Qdrant configuration
QDRANT_URL=http://localhost:6333
```

### Settings Class

```python
# app/core/config.py
class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:6333"
```

### Docker Setup

```yaml
# docker-compose.yml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333

volumes:
  qdrant_data:
```

## Testing

Run the comprehensive test suite:

```bash
# Run all vector store tests
python -m pytest tests/test_vector_store.py -v

# Run specific test categories
python -m pytest tests/test_vector_store.py::TestBotIsolation -v
python -m pytest tests/test_vector_store.py::TestVectorService -v
python -m pytest tests/test_vector_store.py::TestQdrantVectorStore -v
```

## Performance Considerations

### Batch Operations
- Store embeddings in batches for better performance
- Default batch size: 100 points per batch
- Configurable batch sizes for different use cases

### Memory Management
- Close vector services when done
- Use connection pooling for high-traffic scenarios
- Monitor Qdrant memory usage

### Indexing and Optimization
- Qdrant automatically optimizes collections
- Configure indexing parameters for specific use cases
- Monitor collection segments and optimization status

## Monitoring and Observability

### Collection Statistics
```python
stats = await vector_service.get_bot_collection_stats(bot_id)
print(f"Health: {stats['status']}")
print(f"Vectors: {stats['vectors_count']}")
print(f"Indexed: {stats['indexed_vectors_count']}")
print(f"Segments: {stats['segments_count']}")
print(f"Optimizer: {stats['optimizer_status']}")
```

### Logging
The vector store implementation provides comprehensive logging:
- Collection operations (create, delete, info)
- Search performance and results
- Error conditions and recovery
- Bot isolation events
- Batch operation progress

### Health Checks
```python
# Check if Qdrant is accessible
try:
    await vector_service.initialize_bot_collection("health_check", 128)
    await vector_service.delete_bot_collection("health_check")
    print("✅ Qdrant is healthy")
except Exception as e:
    print(f"❌ Qdrant health check failed: {e}")
```

## Best Practices

1. **Always initialize collections** before storing embeddings
2. **Use consistent embedding dimensions** within a bot
3. **Include meaningful metadata** for filtering and debugging
4. **Clean up collections** when bots are deleted
5. **Monitor collection sizes** and performance metrics
6. **Use appropriate score thresholds** for search quality
7. **Test bot isolation** in your integration tests
8. **Implement proper error handling** for production use
9. **Use batch operations** for better performance
10. **Monitor Qdrant resource usage** in production

## Production Deployment

### Scaling Considerations
- Use Qdrant clustering for high availability
- Configure appropriate resource limits
- Monitor collection performance metrics
- Implement backup and recovery procedures

### Security
- Secure Qdrant endpoints with authentication
- Use network isolation for Qdrant access
- Implement proper access controls
- Monitor for unusual access patterns

### Backup and Recovery
```python
# Export collection data (implement as needed)
async def backup_bot_collection(bot_id: str, backup_path: str):
    stats = await vector_service.get_bot_collection_stats(bot_id)
    # Implement backup logic based on requirements
    pass

# Restore collection data (implement as needed)
async def restore_bot_collection(bot_id: str, backup_path: str):
    # Implement restore logic based on requirements
    pass
```

## Example Integration

See `example_vector_usage.py` for a complete demonstration of:
- Bot isolation
- Document chunk storage
- Similarity search with filtering
- Collection management
- Advanced Qdrant features

This example shows how the vector store integrates with the broader multi-bot RAG system and demonstrates production-ready patterns for vector operations.

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify Qdrant is running on the configured port
   - Check network connectivity
   - Validate URL configuration

2. **Collection Not Found**
   - Ensure collection is created before use
   - Check bot_id consistency
   - Verify collection naming conventions

3. **Performance Issues**
   - Monitor collection size and segments
   - Optimize batch sizes
   - Check Qdrant resource usage

4. **Search Quality**
   - Adjust score thresholds
   - Verify embedding quality
   - Check metadata filtering logic

### Debug Mode
```python
import logging
logging.getLogger('app.services.vector_store').setLevel(logging.DEBUG)
```

This comprehensive guide covers all aspects of using the Qdrant vector store implementation in the multi-bot RAG platform.