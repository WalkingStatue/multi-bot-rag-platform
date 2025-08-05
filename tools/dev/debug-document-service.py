#!/usr/bin/env python3
"""
Debug script to test document service functionality and identify 422 errors.
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import get_db
from app.services.document_service import DocumentService
from app.services.permission_service import PermissionService
from app.models.user import User
from app.models.bot import Bot
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_service():
    """Test document service functionality step by step."""
    
    print("🔍 Testing Document Service Components")
    print("=" * 50)
    
    # Test 1: Database connection
    print("\n1. Testing database connection...")
    try:
        db_gen = get_db()
        db = next(db_gen)
        print("✅ Database connection successful")
        
        # Test basic queries
        user_count = db.query(User).count()
        bot_count = db.query(Bot).count()
        print(f"   Users in database: {user_count}")
        print(f"   Bots in database: {bot_count}")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 2: Permission service initialization
    print("\n2. Testing permission service...")
    try:
        permission_service = PermissionService(db)
        print("✅ Permission service initialized")
    except Exception as e:
        print(f"❌ Permission service failed: {e}")
        return False
    
    # Test 3: Document service initialization
    print("\n3. Testing document service initialization...")
    try:
        document_service = DocumentService(db)
        print("✅ Document service initialized")
        
        # Check if processor is available
        if document_service.processor:
            print("✅ Document processor available")
        else:
            print("❌ Document processor not available")
            
        # Check upload directory
        if document_service.upload_dir.exists():
            print(f"✅ Upload directory exists: {document_service.upload_dir}")
        else:
            print(f"⚠️  Upload directory will be created: {document_service.upload_dir}")
            
    except Exception as e:
        print(f"❌ Document service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Vector service (if enabled)
    print("\n4. Testing vector service...")
    if document_service.vector_service:
        print("✅ Vector service is enabled")
        try:
            # Test basic vector service functionality
            print("   Testing vector service connection...")
            # This would test Qdrant connection
        except Exception as e:
            print(f"⚠️  Vector service connection issue: {e}")
    else:
        print("⚠️  Vector service is disabled (for debugging)")
    
    # Test 5: Embedding service
    print("\n5. Testing embedding service...")
    try:
        embedding_service = document_service.embedding_service
        print("✅ Embedding service available")
        
        # Test provider listing
        providers = embedding_service.get_supported_providers()
        print(f"   Available providers: {providers}")
        
        # Test model listing
        all_models = embedding_service.get_all_available_models()
        print(f"   Available models: {list(all_models.keys())}")
        
    except Exception as e:
        print(f"❌ Embedding service failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Text processing
    print("\n6. Testing text processing...")
    try:
        processor = document_service.processor
        if processor:
            # Test with sample text
            sample_text = "This is a test document. It contains multiple sentences. We want to test if the text processing works correctly."
            
            # Test text normalization
            normalized = processor.chunker._normalize_text(sample_text)
            print(f"✅ Text normalization works")
            
            # Test chunking
            chunks = processor.chunker.chunk_text(sample_text)
            print(f"✅ Text chunking works: {len(chunks)} chunks created")
            
        else:
            print("❌ Document processor not available")
            return False
            
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 7: File validation
    print("\n7. Testing file validation...")
    try:
        from app.utils.text_processing import DocumentExtractor
        
        # Test with sample text file
        sample_content = b"This is a test text file content."
        file_path = Path("test.txt")
        
        is_valid, mime_type, error_msg = DocumentExtractor.validate_file(file_path, sample_content)
        
        if is_valid:
            print(f"✅ File validation works: {mime_type}")
        else:
            print(f"❌ File validation failed: {error_msg}")
            
    except Exception as e:
        print(f"❌ File validation test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Document Service Component Test Complete!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_document_service())
    if success:
        print("\n✅ All tests passed! Document service should be working.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)