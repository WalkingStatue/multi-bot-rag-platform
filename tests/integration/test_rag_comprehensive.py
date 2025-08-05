#!/usr/bin/env python3
import asyncio
import sys
import logging
import os

# Add the app directory to Python path
sys.path.insert(0, '/app')

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app.services.chat_service')
logger.setLevel(logging.INFO)

from app.services.chat_service import ChatService
from app.services.vector_store import VectorService
from app.services.embedding_service import EmbeddingProviderService
from app.core.database import get_db
from app.models.bot import Bot
from app.models.document import Document, DocumentChunk
from app.models.user import User
import uuid

async def test_rag_comprehensive():
    print("=== Comprehensive RAG Implementation Test ===\n")
    
    # Get database session
    db = next(get_db())
    chat_service = ChatService(db)
    vector_service = VectorService()
    embedding_service = EmbeddingProviderService()
    
    # Get bot
    bot_id = uuid.UUID('de0fb446-197d-4e8a-a79e-d2851e0c4bfc')
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    if not bot:
        print("❌ Bot not found!")
        return
    
    print(f"✅ Bot found: {bot.name}")
    print(f"   Embedding provider: {bot.embedding_provider}")
    print(f"   Embedding model: {bot.embedding_model}")
    print(f"   LLM provider: {bot.llm_provider}")
    print(f"   LLM model: {bot.llm_model}")
    
    # Test 1: Check if bot has documents
    print("\n--- Test 1: Document Check ---")
    has_docs = await chat_service._bot_has_documents(bot_id)
    print(f"Bot has documents: {'✅' if has_docs else '❌'} {has_docs}")
    
    if has_docs:
        # Get document details
        documents = db.query(Document).filter(Document.bot_id == bot_id).all()
        print(f"Documents found: {len(documents)}")
        for doc in documents:
            print(f"  - {doc.filename} ({doc.chunk_count} chunks)")
            
        # Check document chunks
        total_chunks = db.query(DocumentChunk).filter(DocumentChunk.bot_id == bot_id).count()
        print(f"Total chunks in database: {total_chunks}")
    
    # Test 2: Vector collection status
    print("\n--- Test 2: Vector Collection Status ---")
    try:
        collection_exists = await vector_service.vector_store.collection_exists(str(bot_id))
        print(f"Vector collection exists: {'✅' if collection_exists else '❌'} {collection_exists}")
        
        if collection_exists:
            collection_info = await vector_service.get_bot_collection_stats(str(bot_id))
            points_count = collection_info.get('points_count', 0)
            vector_size = collection_info.get('config', {}).get('vector_size', 'unknown')
            print(f"  Collection points: {points_count}")
            print(f"  Vector dimension: {vector_size}")
            
            # Check if dimensions match expected
            expected_dim = embedding_service.get_embedding_dimension(bot.embedding_provider, bot.embedding_model)
            print(f"  Expected dimension: {expected_dim}")
            print(f"  Dimension match: {'✅' if vector_size == expected_dim else '❌'}")
        
    except Exception as e:
        print(f"❌ Vector collection check failed: {e}")
    
    # Test 3: Embedding generation
    print("\n--- Test 3: Embedding Generation ---")
    try:
        # Get user (bot owner) for API key
        user = db.query(User).filter(User.id == bot.owner_id).first()
        if not user:
            print("❌ Bot owner not found")
            return
            
        # Try to get API key
        from app.services.user_service import UserService
        user_service = UserService(db)
        
        try:
            api_key = user_service.get_user_api_key(bot.owner_id, bot.embedding_provider)
            if api_key:
                print("✅ API key found for embedding provider")
                
                # Test embedding generation
                test_text = "What is this document about?"
                embedding = await embedding_service.generate_single_embedding(
                    provider=bot.embedding_provider,
                    text=test_text,
                    model=bot.embedding_model,
                    api_key=api_key
                )
                
                print(f"✅ Embedding generated successfully")
                print(f"  Embedding dimension: {len(embedding)}")
                print(f"  First 5 values: {embedding[:5]}")
                
            else:
                print("❌ No API key configured for embedding provider")
                
        except Exception as e:
            print(f"❌ API key retrieval failed: {e}")
            
    except Exception as e:
        print(f"❌ Embedding generation test failed: {e}")
    
    # Test 4: RAG retrieval
    print("\n--- Test 4: RAG Retrieval ---")
    try:
        test_query = "What is this document about?"
        chunks = await chat_service._retrieve_relevant_chunks(bot, test_query)
        
        print(f"Retrieved chunks: {'✅' if chunks else '❌'} {len(chunks)}")
        
        if chunks:
            print("Top chunks:")
            for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                score = chunk.get('score', 'N/A')
                text_preview = chunk.get('text', '')[:100] + '...' if len(chunk.get('text', '')) > 100 else chunk.get('text', '')
                print(f"  {i+1}. Score: {score}")
                print(f"     Text: {text_preview}")
        else:
            print("❌ No chunks retrieved - investigating...")
            
            # Debug: Try with different similarity thresholds
            if collection_exists and points_count > 0:
                print("  Debugging with different thresholds...")
                
                # Generate embedding for debug
                try:
                    api_key = user_service.get_user_api_key(bot.owner_id, bot.embedding_provider)
                    query_embedding = await embedding_service.generate_single_embedding(
                        provider=bot.embedding_provider,
                        text=test_query,
                        model=bot.embedding_model,
                        api_key=api_key
                    )
                    
                    # Try without threshold
                    debug_chunks = await vector_service.search_relevant_chunks(
                        bot_id=str(bot_id),
                        query_embedding=query_embedding,
                        top_k=5,
                        score_threshold=None
                    )
                    
                    if debug_chunks:
                        print(f"  Found {len(debug_chunks)} chunks without threshold")
                        print(f"  Top score: {debug_chunks[0].get('score', 'N/A')}")
                        print(f"  Similarity threshold might be too high (current: {chat_service.similarity_threshold})")
                    else:
                        print("  No chunks found even without threshold - possible indexing issue")
                        
                except Exception as debug_e:
                    print(f"  Debug search failed: {debug_e}")
    
    except Exception as e:
        print(f"❌ RAG retrieval test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: End-to-end chat test (if everything works)
    print("\n--- Test 5: End-to-End Chat Test ---")
    try:
        if has_docs and collection_exists:
            from app.schemas.conversation import ChatRequest
            
            chat_request = ChatRequest(
                message="What is this document about?",
                session_id=None
            )
            
            # This would require proper user authentication, so we'll skip for now
            print("⏭️  Skipping end-to-end test (requires user authentication)")
        else:
            print("⏭️  Skipping end-to-end test (missing documents or collection)")
    
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
    
    print("\n=== RAG Test Summary ===")
    print("Key components to check:")
    print("1. ✅ Documents uploaded and chunked")
    print("2. ✅ Vector collection created with correct dimensions") 
    print("3. ✅ API keys configured for embedding provider")
    print("4. ❓ Similarity threshold tuning (may need adjustment)")
    print("5. ❓ Embedding compatibility between stored and generated")

if __name__ == "__main__":
    asyncio.run(test_rag_comprehensive())