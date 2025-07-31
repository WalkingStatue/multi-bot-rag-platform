#!/usr/bin/env python3
"""
Test script to debug bot listing 403 errors.
"""
import asyncio
import sys
import os
import logging
from pathlib import Path
import uuid

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import get_db
from app.services.bot_service import BotService
from app.services.permission_service import PermissionService
from app.models.user import User
from app.models.bot import Bot, BotPermission
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot_listing():
    """Test bot listing functionality to identify 403 errors."""
    
    print("🔍 Testing Bot Listing Functionality")
    print("=" * 50)
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Test 1: Get test user
        print("\n1. Getting test user...")
        
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            print("❌ Test user 'testuser' not found")
            return False
        
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        
        # Test 2: Check user's bot permissions directly
        print("\n2. Checking user's bot permissions...")
        
        permissions = db.query(BotPermission).filter(
            BotPermission.user_id == user.id
        ).all()
        
        print(f"   Found {len(permissions)} permissions for user")
        for perm in permissions:
            print(f"   - Bot ID: {perm.bot_id}, Role: {perm.role}")
        
        # Test 3: Check if bots exist
        print("\n3. Checking available bots...")
        
        all_bots = db.query(Bot).all()
        print(f"   Total bots in database: {len(all_bots)}")
        
        for bot in all_bots:
            print(f"   - Bot: {bot.name} (ID: {bot.id}, Owner: {bot.owner_id})")
        
        # Test 4: Test permission service directly
        print("\n4. Testing permission service...")
        
        permission_service = PermissionService(db)
        
        try:
            accessible_bots = permission_service.get_user_accessible_bots(user.id)
            print(f"✅ Permission service returned {len(accessible_bots)} accessible bots")
            
            for bot_info in accessible_bots:
                print(f"   - Bot: {bot_info['bot'].name}, Role: {bot_info['role']}")
                
        except Exception as e:
            print(f"❌ Permission service failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Test bot service directly
        print("\n5. Testing bot service...")
        
        bot_service = BotService(db)
        
        try:
            user_bots = bot_service.list_user_bots(user.id)
            print(f"✅ Bot service returned {len(user_bots)} bots")
            
            for bot_info in user_bots:
                print(f"   - Bot: {bot_info['bot'].name}, Role: {bot_info['role']}")
                
        except Exception as e:
            print(f"❌ Bot service failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 6: Check if user has any permissions at all
        print("\n6. Checking user permissions in detail...")
        
        for bot in all_bots:
            has_view = permission_service.check_bot_permission(user.id, bot.id, "view_bot")
            user_role = permission_service.get_user_bot_role(user.id, bot.id)
            print(f"   Bot {bot.name}: view_permission={has_view}, role={user_role}")
        
        print("\n" + "=" * 50)
        print("🎉 Bot Listing Test Complete!")
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
    success = asyncio.run(test_bot_listing())
    if success:
        print("\n✅ Bot listing functionality is working!")
    else:
        print("\n❌ Bot listing has issues. Check the errors above.")
        sys.exit(1)