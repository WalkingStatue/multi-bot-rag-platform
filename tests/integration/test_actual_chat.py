#!/usr/bin/env python3
"""
Test actual chat processing to identify the issue
"""
import asyncio
import sys
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_actual_chat():
    """Test actual chat processing with mock data"""
    try:
        from app.services.chat_service import ChatService
        from app.core.database import get_db
        from app.schemas.conversation import ChatRequest
        from app.models.bot import Bot
        from app.models.user import User
        
        logger.info("Testing actual chat processing...")
        
        # Get database session
        db = next(get_db())
        
        # Try to get a real bot and user from the database
        bot = db.query(Bot).first()
        user = db.query(User).first()
        
        if not bot:
            logger.error("No bot found in database")
            return False
            
        if not user:
            logger.error("No user found in database")
            return False
            
        logger.info(f"Found bot: {bot.name} (ID: {bot.id})")
        logger.info(f"Found user: {user.username} (ID: {user.id})")
        logger.info(f"Bot LLM provider: {bot.llm_provider}")
        logger.info(f"Bot embedding provider: {bot.embedding_provider}")
        
        # Create chat service
        chat_service = ChatService(db)
        
        # Test with a simple message
        chat_request = ChatRequest(message='Hello, this is a test message')
        
        logger.info("Attempting to process message...")
        
        try:
            response = await chat_service.process_message(
                bot_id=bot.id,
                user_id=user.id,
                chat_request=chat_request
            )
            
            logger.info("✓ Message processed successfully!")
            logger.info(f"Response: {response.message[:100]}...")
            logger.info(f"Processing time: {response.processing_time}s")
            logger.info(f"Chunks used: {len(response.chunks_used)}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Message processing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
    except Exception as e:
        logger.error(f"✗ Test setup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run the test"""
    logger.info("="*60)
    logger.info("TESTING ACTUAL CHAT PROCESSING")
    logger.info("="*60)
    
    success = await test_actual_chat()
    
    if success:
        logger.info("\n🎉 Chat processing test PASSED!")
    else:
        logger.error("\n❌ Chat processing test FAILED!")
        logger.info("\nThis explains why the frontend is not getting responses.")

if __name__ == "__main__":
    asyncio.run(main())