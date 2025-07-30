#!/usr/bin/env python3
"""
Script to set up a test user in the database for testing purposes.

This script creates a dedicated test user with all necessary data
that can be used across all tests to ensure the real database
doesn't get corrupted during testing.

Usage:
    python scripts/setup_test_user.py [--cleanup] [--reset]
    
Options:
    --cleanup: Remove the test user and all associated data
    --reset: Remove existing test user and create a new one
"""
import sys
import argparse
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base
from tests.fixtures.test_user_setup import TestUserManager


def create_database_session():
    """Create a database session using the application settings."""
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Set to True for SQL debugging
    )
    
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def setup_test_user():
    """Set up the test user and all associated data."""
    print("Setting up test user in database...")
    
    db = create_database_session()
    try:
        manager = TestUserManager(db)
        
        # Check if test user already exists
        existing_user = manager.get_test_user()
        if existing_user:
            print(f"Test user '{existing_user.username}' already exists!")
            print(f"User ID: {existing_user.id}")
            print(f"Email: {existing_user.email}")
            print("Use --reset to recreate the user or --cleanup to remove it.")
            return existing_user
        
        # Create complete test environment
        test_data = manager.setup_complete_test_environment()
        
        print("✅ Test user setup completed successfully!")
        print(f"Username: {test_data['user'].username}")
        print(f"Email: {test_data['user'].email}")
        print(f"User ID: {test_data['user'].id}")
        print(f"Password: {manager.get_test_user_credentials()['password']}")
        print(f"Bot Name: {test_data['bot'].name}")
        print(f"Bot ID: {test_data['bot'].id}")
        print(f"Conversation ID: {test_data['conversation'].id}")
        print(f"Messages created: {len(test_data['messages'])}")
        print(f"API Keys configured: {list(test_data['api_keys'].keys())}")
        
        return test_data['user']
        
    except Exception as e:
        print(f"❌ Error setting up test user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def cleanup_test_user():
    """Remove the test user and all associated data."""
    print("Cleaning up test user from database...")
    
    db = create_database_session()
    try:
        manager = TestUserManager(db)
        
        # Check if test user exists
        existing_user = manager.get_test_user()
        if not existing_user:
            print("No test user found to clean up.")
            return
        
        print(f"Removing test user '{existing_user.username}' and all associated data...")
        manager.cleanup_test_data()
        
        print("✅ Test user cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error cleaning up test user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_test_user():
    """Remove existing test user and create a new one."""
    print("Resetting test user...")
    cleanup_test_user()
    print()
    setup_test_user()


def show_test_user_info():
    """Show information about the existing test user."""
    print("Test user information:")
    
    db = create_database_session()
    try:
        manager = TestUserManager(db)
        
        user = manager.get_test_user()
        if not user:
            print("No test user found. Run with no arguments to create one.")
            return
        
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"User ID: {user.id}")
        print(f"Full Name: {user.full_name}")
        print(f"Active: {user.is_active}")
        print(f"Created: {user.created_at}")
        print(f"Password: {manager.get_test_user_credentials()['password']}")
        
        # Show API keys
        print(f"\nAPI Keys:")
        for api_key in user.api_keys:
            print(f"  - {api_key.provider}: {'Active' if api_key.is_active else 'Inactive'}")
        
        # Show bots
        print(f"\nOwned Bots:")
        for bot in user.owned_bots:
            print(f"  - {bot.name} ({bot.id}): {bot.llm_provider}/{bot.llm_model}")
        
        # Show conversations
        print(f"\nConversation Sessions:")
        for session in user.conversation_sessions:
            message_count = len(session.messages)
            print(f"  - {session.title} ({session.id}): {message_count} messages")
        
    except Exception as e:
        print(f"❌ Error getting test user info: {e}")
        raise
    finally:
        db.close()


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Set up or manage test user in the database"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove the test user and all associated data"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove existing test user and create a new one"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show information about the existing test user"
    )
    
    args = parser.parse_args()
    
    try:
        if args.cleanup:
            cleanup_test_user()
        elif args.reset:
            reset_test_user()
        elif args.info:
            show_test_user_info()
        else:
            setup_test_user()
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()