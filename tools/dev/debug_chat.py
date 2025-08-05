#!/usr/bin/env python3
"""
Debug script to test chat functionality
"""
import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chat_service():
    """Test chat service functionality"""
    try:
        from app.services.chat_service import ChatService
        from app.core.database import get_db
        from app.schemas.conversation import ChatRequest
        
        logger.info("Testing chat service...")
        
        # Get database session
        db = next(get_db())
        
        # Create chat service
        chat_service = ChatService(db)
        logger.info("✓ Chat service created successfully")
        
        # Check available methods
        methods = [method for method in dir(chat_service) if not method.startswith('_')]
        logger.info(f"Available methods: {methods}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Chat service test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_api_response():
    """Test API response structure"""
    try:
        from app.schemas.conversation import ChatResponse
        
        # Test creating a ChatResponse
        response = ChatResponse(
            message="Test response",
            session_id="123e4567-e89b-12d3-a456-426614174000",
            chunks_used=[],
            processing_time=0.5,
            metadata={}
        )
        
        logger.info("✓ ChatResponse created successfully")
        logger.info(f"Response: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ API response test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run debug tests"""
    logger.info("="*50)
    logger.info("DEBUGGING CHAT FUNCTIONALITY")
    logger.info("="*50)
    
    tests = [
        ("Chat Service", test_chat_service),
        ("API Response", test_api_response),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("DEBUG RESULTS")
    logger.info("="*50)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")

if __name__ == "__main__":
    asyncio.run(main())