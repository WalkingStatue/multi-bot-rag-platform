"""
Test user setup utility for creating a dedicated test user in the database.

This module provides utilities to create and manage a test user that can be used
across all tests to ensure the real database doesn't get corrupted during testing.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserAPIKey, UserSettings
from app.models.bot import Bot, BotPermission
from app.models.conversation import ConversationSession, Message
from app.models.document import Document
from app.core.security import get_password_hash
from app.utils.encryption import encrypt_api_key


class TestUserManager:
    """Manager for creating and managing test users in the database."""
    
    # Default test user data
    DEFAULT_TEST_USER = {
        "id": "550e8400-e29b-41d4-a716-446655440000",  # Fixed UUID for consistency
        "username": "test_user_automated",
        "email": "test.automated@example.com",
        "password": "TestPassword123!",
        "full_name": "Automated Test User",
        "is_active": True
    }
    
    # Default test bot data
    DEFAULT_TEST_BOT = {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Test Bot Automated",
        "description": "Automated test bot for integration testing",
        "system_prompt": "You are a helpful test assistant for automated testing.",
        "llm_provider": "openai",
        "llm_model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_public": False,
        "allow_collaboration": True
    }
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def create_test_user(self, user_data: Optional[Dict[str, Any]] = None) -> User:
        """
        Create a test user in the database.
        
        Args:
            user_data: Optional custom user data. Uses defaults if not provided.
            
        Returns:
            Created User object
            
        Raises:
            IntegrityError: If user already exists
        """
        data = {**self.DEFAULT_TEST_USER, **(user_data or {})}
        
        # Convert string ID to UUID if needed
        if isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        
        # Hash the password
        password = data.pop("password")
        password_hash = get_password_hash(password)
        
        user = User(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            password_hash=password_hash,
            full_name=data["full_name"],
            is_active=data["is_active"]
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            # User already exists, return existing user
            return self.get_test_user()
    
    def get_test_user(self) -> Optional[User]:
        """Get the existing test user from database."""
        return self.db.query(User).filter(
            User.username == self.DEFAULT_TEST_USER["username"]
        ).first()
    
    def create_test_user_settings(self, user: User, settings_data: Optional[Dict[str, Any]] = None) -> UserSettings:
        """
        Create user settings for the test user.
        
        Args:
            user: User object
            settings_data: Optional custom settings data
            
        Returns:
            Created UserSettings object
        """
        default_settings = {
            "theme": "light",
            "language": "en",
            "timezone": "UTC",
            "notifications_enabled": True,
            "email_notifications": False,  # Disable for testing
            "default_llm_provider": "openai",
            "default_embedding_provider": "openai",
            "max_conversation_history": 50,
            "auto_save_conversations": True,
            "custom_settings": {"test_mode": True}
        }
        
        data = {**default_settings, **(settings_data or {})}
        
        # Check if settings already exist
        existing_settings = self.db.query(UserSettings).filter(
            UserSettings.user_id == user.id
        ).first()
        
        if existing_settings:
            return existing_settings
        
        settings = UserSettings(
            user_id=user.id,
            **data
        )
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def create_test_api_keys(self, user: User, api_keys_data: Optional[Dict[str, str]] = None) -> Dict[str, UserAPIKey]:
        """
        Create test API keys for the user.
        
        Args:
            user: User object
            api_keys_data: Dictionary of provider -> api_key mappings
            
        Returns:
            Dictionary of provider -> UserAPIKey objects
        """
        default_keys = {
            "openai": "sk-test-openai-key-for-testing-only",
            "anthropic": "sk-ant-test-anthropic-key-for-testing-only",
            "gemini": "test-gemini-key-for-testing-only",
            "openrouter": "sk-or-test-openrouter-key-for-testing-only"
        }
        
        keys_data = {**default_keys, **(api_keys_data or {})}
        created_keys = {}
        
        for provider, api_key in keys_data.items():
            # Check if key already exists
            existing_key = self.db.query(UserAPIKey).filter(
                UserAPIKey.user_id == user.id,
                UserAPIKey.provider == provider
            ).first()
            
            if existing_key:
                created_keys[provider] = existing_key
                continue
            
            # Encrypt the API key
            encrypted_key = encrypt_api_key(api_key)
            
            user_api_key = UserAPIKey(
                user_id=user.id,
                provider=provider,
                api_key_encrypted=encrypted_key,
                is_active=True
            )
            
            self.db.add(user_api_key)
            created_keys[provider] = user_api_key
        
        self.db.commit()
        return created_keys
    
    def create_test_bot(self, user: User, bot_data: Optional[Dict[str, Any]] = None) -> Bot:
        """
        Create a test bot owned by the test user.
        
        Args:
            user: User object (owner)
            bot_data: Optional custom bot data
            
        Returns:
            Created Bot object
        """
        data = {**self.DEFAULT_TEST_BOT, **(bot_data or {})}
        
        # Convert string ID to UUID if needed
        if isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        
        # Check if bot already exists
        existing_bot = self.db.query(Bot).filter(
            Bot.id == data["id"]
        ).first()
        
        if existing_bot:
            return existing_bot
        
        bot = Bot(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            system_prompt=data["system_prompt"],
            owner_id=user.id,
            llm_provider=data["llm_provider"],
            llm_model=data["llm_model"],
            temperature=data["temperature"],
            max_tokens=data["max_tokens"],
            is_public=data["is_public"],
            allow_collaboration=data["allow_collaboration"]
        )
        
        self.db.add(bot)
        self.db.commit()
        self.db.refresh(bot)
        
        # Create owner permission
        self.create_bot_permission(bot, user, "owner", user)
        
        return bot
    
    def create_bot_permission(self, bot: Bot, user: User, role: str, granted_by: User) -> BotPermission:
        """
        Create a bot permission for a user.
        
        Args:
            bot: Bot object
            user: User to grant permission to
            role: Permission role (owner, admin, editor, viewer)
            granted_by: User who granted the permission
            
        Returns:
            Created BotPermission object
        """
        # Check if permission already exists
        existing_permission = self.db.query(BotPermission).filter(
            BotPermission.bot_id == bot.id,
            BotPermission.user_id == user.id
        ).first()
        
        if existing_permission:
            return existing_permission
        
        permission = BotPermission(
            bot_id=bot.id,
            user_id=user.id,
            role=role,
            granted_by=granted_by.id
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission
    
    def create_test_conversation(self, bot: Bot, user: User, session_data: Optional[Dict[str, Any]] = None) -> ConversationSession:
        """
        Create a test conversation session.
        
        Args:
            bot: Bot object
            user: User object
            session_data: Optional custom session data
            
        Returns:
            Created ConversationSession object
        """
        default_data = {
            "title": "Test Conversation Session",
            "is_shared": False
        }
        
        data = {**default_data, **(session_data or {})}
        
        session = ConversationSession(
            bot_id=bot.id,
            user_id=user.id,
            title=data["title"],
            is_shared=data["is_shared"]
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def create_test_messages(self, session: ConversationSession, user: User, messages_data: Optional[list] = None) -> list[Message]:
        """
        Create test messages in a conversation session.
        
        Args:
            session: ConversationSession object
            user: User object
            messages_data: Optional list of message data
            
        Returns:
            List of created Message objects
        """
        default_messages = [
            {"role": "user", "content": "Hello, this is a test message."},
            {"role": "assistant", "content": "Hello! I'm a test bot. How can I help you with testing?"},
            {"role": "user", "content": "Can you help me test the system?"},
            {"role": "assistant", "content": "Of course! I'm here to help with all your testing needs."}
        ]
        
        messages_data = messages_data or default_messages
        created_messages = []
        
        for i, msg_data in enumerate(messages_data):
            message = Message(
                session_id=session.id,
                bot_id=session.bot_id,
                user_id=user.id,
                role=msg_data["role"],
                content=msg_data["content"]
            )
            
            self.db.add(message)
            created_messages.append(message)
        
        self.db.commit()
        return created_messages
    
    def setup_complete_test_environment(self) -> Dict[str, Any]:
        """
        Set up a complete test environment with user, bot, conversation, and messages.
        
        Returns:
            Dictionary containing all created objects
        """
        # Create test user
        user = self.create_test_user()
        
        # Create user settings
        settings = self.create_test_user_settings(user)
        
        # Create API keys
        api_keys = self.create_test_api_keys(user)
        
        # Create test bot
        bot = self.create_test_bot(user)
        
        # Create test conversation
        conversation = self.create_test_conversation(bot, user)
        
        # Create test messages
        messages = self.create_test_messages(conversation, user)
        
        return {
            "user": user,
            "settings": settings,
            "api_keys": api_keys,
            "bot": bot,
            "conversation": conversation,
            "messages": messages
        }
    
    def cleanup_test_data(self):
        """
        Clean up all test data from the database.
        
        WARNING: This will delete all data associated with the test user!
        """
        user = self.get_test_user()
        if not user:
            return
        
        # Delete in reverse order of dependencies
        # Messages will be deleted by cascade
        # Conversation sessions will be deleted by cascade
        # Bot permissions will be deleted by cascade
        # Bots will be deleted by cascade
        # API keys will be deleted by cascade
        # User settings will be deleted by cascade
        
        self.db.delete(user)
        self.db.commit()
    
    def get_test_user_credentials(self) -> Dict[str, str]:
        """
        Get the test user credentials for authentication.
        
        Returns:
            Dictionary with username and password
        """
        return {
            "username": self.DEFAULT_TEST_USER["username"],
            "password": self.DEFAULT_TEST_USER["password"]
        }


def setup_test_user(db_session: Session) -> Dict[str, Any]:
    """
    Convenience function to set up a complete test environment.
    
    Args:
        db_session: Database session
        
    Returns:
        Dictionary containing all created test objects
    """
    manager = TestUserManager(db_session)
    return manager.setup_complete_test_environment()


def cleanup_test_user(db_session: Session):
    """
    Convenience function to clean up test data.
    
    Args:
        db_session: Database session
    """
    manager = TestUserManager(db_session)
    manager.cleanup_test_data()


def get_test_user_auth(db_session: Session) -> Dict[str, str]:
    """
    Get test user authentication credentials.
    
    Args:
        db_session: Database session
        
    Returns:
        Dictionary with username and password
    """
    manager = TestUserManager(db_session)
    return manager.get_test_user_credentials()