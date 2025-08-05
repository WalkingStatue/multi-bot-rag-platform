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
from app.core.database import get_db
from app.models.bot import Bot
import uuid

async def test_rag():
    # Get database session
    db = next(get_db())
    chat_service = ChatService(db)
    
    # Get bot
    bot_id = uuid.UUID('c8c0470a-bbb4-4a75-952b-102203d866de')
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    
    print(f"Bot embedding provider: {bot.embedding_provider}")
    print(f"Bot embedding model: {bot.embedding_model}")
    print(f"Bot LLM provider: {bot.llm_provider}")
    print(f"Bot LLM model: {bot.llm_model}")
    
    # Test if bot has documents
    has_docs = await chat_service._bot_has_documents(bot_id)
    print(f"Bot has documents: {has_docs}")
    
    # Test vector collection
    collection_exists = await chat_service.vector_service.vector_store.collection_exists(str(bot_id))
    print(f"Vector collection exists: {collection_exists}")
    
    if collection_exists:
        try:
            collection_info = await chat_service.vector_service.get_bot_collection_stats(str(bot_id))
            print(f"Collection points: {collection_info.get('points_count', 0)}")
            print(f"Collection vector size: {collection_info.get('config', {}).get('vector_size', 'unknown')}")
        except Exception as e:
            print(f"Failed to get collection info: {e}")
    
    # Test RAG retrieval directly
    print("\n--- Testing RAG Retrieval ---")
    try:
        chunks = await chat_service._retrieve_relevant_chunks(bot, 'What is this document about?')
        print(f"Retrieved chunks: {len(chunks)}")
        if chunks:
            for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
                print(f"Chunk {i+1} (score: {chunk.get('score', 'N/A')}): {chunk.get('text', '')[:100]}...")
        else:
            print("No chunks retrieved - this is the issue!")
    except Exception as e:
        print(f"RAG retrieval failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag())