#!/usr/bin/env python3
"""
Example usage of the Qdrant vector store implementation with bot isolation.
This demonstrates how to use the vector store services in the multi-bot RAG system.
"""
import asyncio
import uuid

from app.services.vector_store import VectorStoreFactory, VectorService


async def demonstrate_vector_store_usage():
    """Demonstrate vector store usage with bot isolation."""
    print("🚀 Multi-Bot RAG Vector Store Demo")
    print("=" * 50)
    
    # Create two different bots
    bot1_id = str(uuid.uuid4())
    bot2_id = str(uuid.uuid4())
    
    print(f"Bot 1 ID: {bot1_id}")
    print(f"Bot 2 ID: {bot2_id}")
    print()
    
    # Initialize vector service with Qdrant
    print("📦 Initializing Qdrant Vector Store...")
    vector_service = VectorService(
        vector_store=VectorStoreFactory.create_vector_store()
    )
    
    # Initialize embedding service (would use local embeddings for demo)
    embedding_service = EmbeddingProviderService()
    
    # Create collections for both bots
    dimension = 384  # Common embedding dimension
    
    print(f"🏗️  Creating collections for both bots (dimension: {dimension})...")
    await vector_service.initialize_bot_collection(bot1_id, dimension)
    await vector_service.initialize_bot_collection(bot2_id, dimension)
    print("✅ Collections created successfully!")
    print()
    
    # Simulate document chunks for Bot 1 (AI Assistant)
    bot1_chunks = [
        {
            "embedding": [0.1] * dimension,  # Simulated embedding
            "text": "I am an AI assistant designed to help with programming tasks.",
            "metadata": {
                "document_id": "doc1",
                "chunk_index": 0,
                "source": "bot1_manual.pdf"
            }
        },
        {
            "embedding": [0.2] * dimension,
            "text": "I can help you write Python code, debug issues, and explain concepts.",
            "metadata": {
                "document_id": "doc1", 
                "chunk_index": 1,
                "source": "bot1_manual.pdf"
            }
        }
    ]
    
    # Simulate document chunks for Bot 2 (Customer Support)
    bot2_chunks = [
        {
            "embedding": [0.8] * dimension,
            "text": "Our customer support hours are Monday to Friday, 9 AM to 5 PM.",
            "metadata": {
                "document_id": "doc2",
                "chunk_index": 0,
                "source": "support_guide.pdf"
            }
        },
        {
            "embedding": [0.9] * dimension,
            "text": "For billing inquiries, please contact our billing department at billing@company.com.",
            "metadata": {
                "document_id": "doc2",
                "chunk_index": 1,
                "source": "support_guide.pdf"
            }
        }
    ]
    
    # Store chunks for both bots
    print("💾 Storing document chunks...")
    bot1_ids = await vector_service.store_document_chunks(bot1_id, bot1_chunks)
    bot2_ids = await vector_service.store_document_chunks(bot2_id, bot2_chunks)
    
    print(f"✅ Stored {len(bot1_ids)} chunks for Bot 1")
    print(f"✅ Stored {len(bot2_ids)} chunks for Bot 2")
    print()
    
    # Demonstrate bot isolation by searching
    print("🔍 Demonstrating Bot Isolation...")
    print("-" * 30)
    
    # Search in Bot 1's collection
    query_embedding = [0.15] * dimension  # Should be similar to Bot 1's chunks
    
    print("Searching in Bot 1's collection:")
    bot1_results = await vector_service.search_relevant_chunks(
        bot1_id, query_embedding, top_k=2
    )
    
    for i, result in enumerate(bot1_results, 1):
        print(f"  {i}. Score: {result['score']:.3f}")
        print(f"     Text: {result['text'][:60]}...")
        print(f"     Source: {result['metadata']['source']}")
        print()
    
    print("Searching in Bot 2's collection:")
    bot2_results = await vector_service.search_relevant_chunks(
        bot2_id, query_embedding, top_k=2
    )
    
    for i, result in enumerate(bot2_results, 1):
        print(f"  {i}. Score: {result['score']:.3f}")
        print(f"     Text: {result['text'][:60]}...")
        print(f"     Source: {result['metadata']['source']}")
        print()
    
    # Get collection statistics
    print("📊 Collection Statistics...")
    print("-" * 25)
    
    bot1_stats = await vector_service.get_bot_collection_stats(bot1_id)
    bot2_stats = await vector_service.get_bot_collection_stats(bot2_id)
    
    print(f"Bot 1 Collection:")
    print(f"  - Vectors: {bot1_stats['vectors_count']}")
    print(f"  - Points: {bot1_stats['points_count']}")
    print(f"  - Status: {bot1_stats['status']}")
    print()
    
    print(f"Bot 2 Collection:")
    print(f"  - Vectors: {bot2_stats['vectors_count']}")
    print(f"  - Points: {bot2_stats['points_count']}")
    print(f"  - Status: {bot2_stats['status']}")
    print()
    
    # Demonstrate document filtering
    print("🎯 Demonstrating Document Filtering...")
    print("-" * 35)
    
    # Search only in specific document
    filtered_results = await vector_service.search_relevant_chunks(
        bot1_id, query_embedding, top_k=5, document_filter="doc1"
    )
    
    print(f"Results filtered by document 'doc1': {len(filtered_results)} found")
    for result in filtered_results:
        print(f"  - {result['metadata']['document_id']}: {result['text'][:50]}...")
    print()
    
    # Demonstrate chunk deletion
    print("🗑️  Demonstrating Chunk Deletion...")
    print("-" * 32)
    
    # Delete first chunk from Bot 1
    if bot1_ids:
        await vector_service.delete_document_chunks(bot1_id, [bot1_ids[0]])
        print(f"✅ Deleted chunk {bot1_ids[0]} from Bot 1")
        
        # Verify deletion
        remaining_results = await vector_service.search_relevant_chunks(
            bot1_id, query_embedding, top_k=10
        )
        print(f"Bot 1 now has {len(remaining_results)} chunks remaining")
    print()
    
    # Demonstrate collection deletion
    print("🧹 Cleaning up...")
    print("-" * 15)
    
    await vector_service.delete_bot_collection(bot2_id)
    print(f"✅ Deleted Bot 2's collection")
    
    # Verify Bot 1's collection still exists
    try:
        bot1_final_stats = await vector_service.get_bot_collection_stats(bot1_id)
        print(f"✅ Bot 1's collection still exists with {bot1_final_stats['points_count']} points")
    except Exception as e:
        print(f"❌ Error accessing Bot 1's collection: {e}")
    
    # Try to access deleted Bot 2's collection
    try:
        await vector_service.get_bot_collection_stats(bot2_id)
        print("❌ Bot 2's collection should have been deleted!")
    except Exception:
        print("✅ Bot 2's collection successfully deleted (isolation maintained)")
    
    # Clean up
    await vector_service.close()
    print()
    print("🎉 Demo completed successfully!")
    print("Key features demonstrated:")
    print("  ✅ Bot-specific namespace isolation")
    print("  ✅ Embedding storage and retrieval")
    print("  ✅ Similarity search with scoring")
    print("  ✅ Document-based filtering")
    print("  ✅ Chunk deletion")
    print("  ✅ Collection management")
    print("  ✅ Data isolation between bots")


async def demonstrate_qdrant_features():
    """Demonstrate advanced Qdrant features."""
    print("\n" + "=" * 50)
    print("🔧 Advanced Qdrant Features Demo")
    print("=" * 50)
    
    bot_id = str(uuid.uuid4())
    dimension = 128
    
    # Test with Qdrant
    print("Testing advanced Qdrant features...")
    vector_service = VectorService(
        vector_store=VectorStoreFactory.create_vector_store()
    )
    
    await vector_service.initialize_bot_collection(bot_id, dimension)
    
    # Store chunks with rich metadata
    chunks = [
        {
            "embedding": [0.1] * dimension,
            "text": "Advanced search capabilities in Qdrant",
            "metadata": {
                "source": "qdrant_docs",
                "category": "search",
                "priority": "high",
                "tags": ["vector", "search", "similarity"]
            }
        },
        {
            "embedding": [0.2] * dimension,
            "text": "Bot isolation ensures data security",
            "metadata": {
                "source": "security_guide",
                "category": "security",
                "priority": "critical",
                "tags": ["isolation", "security", "bot"]
            }
        }
    ]
    
    await vector_service.store_document_chunks(bot_id, chunks)
    
    # Test metadata filtering (need to use the vector store directly for advanced filtering)
    print("🔍 Testing metadata filtering...")
    security_results = await vector_service.vector_store.search_similar(
        bot_id, [0.15] * dimension, top_k=5, 
        metadata_filter={"category": "security"}
    )
    print(f"✅ Found {len(security_results)} security-related chunks")
    
    # Test score thresholding
    print("📊 Testing score thresholding...")
    high_score_results = await vector_service.search_relevant_chunks(
        bot_id, [0.1] * dimension, top_k=5, score_threshold=0.8
    )
    print(f"✅ Found {len(high_score_results)} high-score chunks")
    
    await vector_service.close()
    
    # Show supported types
    print(f"\nSupported vector store types: {VectorStoreFactory.get_supported_types()}")
    
    print("🎉 Advanced features demo completed!")


if __name__ == "__main__":
    print("Starting Multi-Bot RAG Vector Store Demonstration...")
    print()
    
    # Run the main demo
    asyncio.run(demonstrate_vector_store_usage())
    
    # Run advanced features demo
    asyncio.run(demonstrate_qdrant_features())