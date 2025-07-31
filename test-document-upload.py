#!/usr/bin/env python3
"""
Test script to debug document upload 422 errors.
"""
import asyncio
import sys
import os
import logging
from pathlib import Path
import uuid
from io import BytesIO

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import get_db
from app.services.document_service import DocumentService
from app.services.permission_service import PermissionService
from app.models.user import User
from app.models.bot import Bot, BotPermission
from sqlalchemy.orm import Session
from fastapi import UploadFile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockUploadFile:
    """Mock UploadFile for testing."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self._file = BytesIO(content)
    
    async def read(self) -> bytes:
        return self.content
    
    async def seek(self, position: int):
        self._file.seek(position)

async def test_document_upload():
    """Test document upload functionality step by step."""
    
    print("🔍 Testing Document Upload Functionality")
    print("=" * 50)
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Test 1: Get a test user and bot
        print("\n1. Getting test user and bot...")
        
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database")
            return False
        
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        
        # Get a bot owned by this user or with permissions
        bot_permission = db.query(BotPermission).filter(
            BotPermission.user_id == user.id
        ).first()
        
        if bot_permission:
            bot = db.query(Bot).filter(Bot.id == bot_permission.bot_id).first()
            print(f"✅ Found bot via permission: {bot.name} (ID: {bot.id})")
            print(f"   User role: {bot_permission.role}")
        else:
            # Try to find a bot owned by the user
            bot = db.query(Bot).filter(Bot.owner_id == user.id).first()
            if bot:
                print(f"✅ Found owned bot: {bot.name} (ID: {bot.id})")
            else:
                print("❌ No accessible bots found for user")
                return False
        
        # Test 2: Initialize services
        print("\n2. Initializing services...")
        
        permission_service = PermissionService(db)
        document_service = DocumentService(db, permission_service)
        
        print("✅ Services initialized")
        
        # Test 3: Check permissions
        print("\n3. Testing permissions...")
        
        has_upload_permission = permission_service.check_bot_permission(
            user.id, bot.id, "upload_documents"
        )
        
        print(f"   Upload permission: {has_upload_permission}")
        
        if not has_upload_permission:
            print("❌ User doesn't have upload permission")
            return False
        
        print("✅ User has upload permission")
        
        # Test 4: Create test file
        print("\n4. Creating test file...")
        
        test_content = b"This is a test document for upload testing. It contains some sample text to verify that the document processing pipeline works correctly."
        test_file = MockUploadFile("test_document.txt", test_content, "text/plain")
        
        print(f"✅ Created test file: {test_file.filename} ({len(test_content)} bytes)")
        
        # Test 5: Test upload without processing
        print("\n5. Testing document upload (without processing)...")
        
        try:
            document = await document_service.upload_document(
                bot_id=bot.id,
                user_id=user.id,
                file=test_file,
                process_immediately=False
            )
            
            print(f"✅ Document uploaded successfully!")
            print(f"   Document ID: {document.id}")
            print(f"   Filename: {document.filename}")
            print(f"   File size: {document.file_size}")
            print(f"   Chunk count: {document.chunk_count}")
            
        except Exception as e:
            print(f"❌ Document upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 6: Test document processing
        print("\n6. Testing document processing...")
        
        try:
            result = await document_service.process_document(
                document_id=document.id,
                user_id=user.id
            )
            
            print(f"✅ Document processed successfully!")
            print(f"   Chunks created: {result['chunks_created']}")
            print(f"   Embeddings stored: {result['embeddings_stored']}")
            
        except Exception as e:
            print(f"❌ Document processing failed: {e}")
            import traceback
            traceback.print_exc()
            # This might fail due to missing API keys, but upload should work
        
        # Test 7: Test document listing
        print("\n7. Testing document listing...")
        
        try:
            documents = await document_service.list_documents(
                bot_id=bot.id,
                user_id=user.id,
                skip=0,
                limit=10
            )
            
            print(f"✅ Document listing works!")
            print(f"   Found {len(documents)} documents")
            
            for doc in documents:
                print(f"   - {doc['filename']} ({doc['chunk_count']} chunks)")
            
        except Exception as e:
            print(f"❌ Document listing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 8: Test document stats
        print("\n8. Testing document stats...")
        
        try:
            stats = await document_service.get_bot_document_stats(
                bot_id=bot.id,
                user_id=user.id
            )
            
            print(f"✅ Document stats work!")
            print(f"   Total documents: {stats['total_documents']}")
            print(f"   Total chunks: {stats['total_chunks']}")
            print(f"   Total file size: {stats['total_file_size']}")
            
        except Exception as e:
            print(f"❌ Document stats failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Document Upload Test Complete!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_document_upload())
    if success:
        print("\n✅ Document upload functionality is working!")
    else:
        print("\n❌ Document upload has issues. Check the errors above.")
        sys.exit(1)