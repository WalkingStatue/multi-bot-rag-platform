"""
Tests for database models.
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models import (
    User, UserAPIKey, Bot, BotPermission, 
    ConversationSession, Message, Document, DocumentChunk, ActivityLog
)


class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_unique_constraints(self, db_session):
        """Test user unique constraints."""
        user1 = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Test duplicate username
        user2 = User(
            username="testuser",
            email="test2@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Test duplicate email
        user3 = User(
            username="testuser2",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user3)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestUserAPIKeyModel:
    """Test UserAPIKey model."""
    
    def test_create_api_key(self, db_session):
        """Test creating an API key."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        api_key = UserAPIKey(
            user_id=user.id,
            provider="openai",
            api_key_encrypted="encrypted_key"
        )
        db_session.add(api_key)
        db_session.commit()
        
        assert api_key.id is not None
        assert api_key.user_id == user.id
        assert api_key.provider == "openai"
        assert api_key.is_active is True
    
    def test_api_key_unique_constraint(self, db_session):
        """Test API key unique constraint per user and provider."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        api_key1 = UserAPIKey(
            user_id=user.id,
            provider="openai",
            api_key_encrypted="encrypted_key1"
        )
        db_session.add(api_key1)
        db_session.commit()
        
        # Try to add another key for same user and provider
        api_key2 = UserAPIKey(
            user_id=user.id,
            provider="openai",
            api_key_encrypted="encrypted_key2"
        )
        db_session.add(api_key2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestBotModel:
    """Test Bot model."""
    
    def test_create_bot(self, db_session):
        """Test creating a bot."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            description="A test bot",
            system_prompt="You are a helpful assistant",
            owner_id=user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        assert bot.id is not None
        assert bot.name == "Test Bot"
        assert bot.owner_id == user.id
        assert bot.temperature == 0.7  # default value
        assert bot.is_public is False  # default value
        assert bot.allow_collaboration is True  # default value


class TestBotPermissionModel:
    """Test BotPermission model."""
    
    def test_create_bot_permission(self, db_session):
        """Test creating a bot permission."""
        owner = User(
            username="owner",
            email="owner@example.com",
            password_hash="hashed_password"
        )
        collaborator = User(
            username="collaborator",
            email="collaborator@example.com",
            password_hash="hashed_password"
        )
        db_session.add_all([owner, collaborator])
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=owner.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        permission = BotPermission(
            bot_id=bot.id,
            user_id=collaborator.id,
            role="editor",
            granted_by=owner.id
        )
        db_session.add(permission)
        db_session.commit()
        
        assert permission.id is not None
        assert permission.bot_id == bot.id
        assert permission.user_id == collaborator.id
        assert permission.role == "editor"
        assert permission.granted_by == owner.id
    
    def test_bot_permission_unique_constraint(self, db_session):
        """Test bot permission unique constraint per bot and user."""
        owner = User(
            username="owner",
            email="owner@example.com",
            password_hash="hashed_password"
        )
        collaborator = User(
            username="collaborator",
            email="collaborator@example.com",
            password_hash="hashed_password"
        )
        db_session.add_all([owner, collaborator])
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=owner.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        permission1 = BotPermission(
            bot_id=bot.id,
            user_id=collaborator.id,
            role="editor",
            granted_by=owner.id
        )
        db_session.add(permission1)
        db_session.commit()
        
        # Try to add another permission for same bot and user
        permission2 = BotPermission(
            bot_id=bot.id,
            user_id=collaborator.id,
            role="viewer",
            granted_by=owner.id
        )
        db_session.add(permission2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestConversationModels:
    """Test conversation-related models."""
    
    def test_create_conversation_session(self, db_session):
        """Test creating a conversation session."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        session = ConversationSession(
            bot_id=bot.id,
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(session)
        db_session.commit()
        
        assert session.id is not None
        assert session.bot_id == bot.id
        assert session.user_id == user.id
        assert session.title == "Test Conversation"
        assert session.is_shared is False  # default value
    
    def test_create_message(self, db_session):
        """Test creating a message."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        session = ConversationSession(
            bot_id=bot.id,
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            bot_id=bot.id,
            user_id=user.id,
            role="user",
            content="Hello, bot!",
            message_metadata={"tokens": 3}
        )
        db_session.add(message)
        db_session.commit()
        
        assert message.id is not None
        assert message.session_id == session.id
        assert message.role == "user"
        assert message.content == "Hello, bot!"
        assert message.message_metadata == {"tokens": 3}


class TestDocumentModels:
    """Test document-related models."""
    
    def test_create_document(self, db_session):
        """Test creating a document."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        document = Document(
            bot_id=bot.id,
            uploaded_by=user.id,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        db_session.add(document)
        db_session.commit()
        
        assert document.id is not None
        assert document.bot_id == bot.id
        assert document.uploaded_by == user.id
        assert document.filename == "test.pdf"
        assert document.chunk_count == 0  # default value
    
    def test_create_document_chunk(self, db_session):
        """Test creating a document chunk."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        document = Document(
            bot_id=bot.id,
            uploaded_by=user.id,
            filename="test.pdf",
            file_path="/uploads/test.pdf"
        )
        db_session.add(document)
        db_session.commit()
        
        chunk = DocumentChunk(
            document_id=document.id,
            bot_id=bot.id,
            chunk_index=0,
            content="This is a test chunk",
            embedding_id="embedding_123",
            chunk_metadata={"page": 1, "section": "intro"}
        )
        db_session.add(chunk)
        db_session.commit()
        
        assert chunk.id is not None
        assert chunk.document_id == document.id
        assert chunk.bot_id == bot.id
        assert chunk.chunk_index == 0
        assert chunk.content == "This is a test chunk"
        assert chunk.chunk_metadata == {"page": 1, "section": "intro"}


class TestActivityLogModel:
    """Test ActivityLog model."""
    
    def test_create_activity_log(self, db_session):
        """Test creating an activity log."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        bot = Bot(
            name="Test Bot",
            system_prompt="You are a helpful assistant",
            owner_id=user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        
        activity_log = ActivityLog(
            bot_id=bot.id,
            user_id=user.id,
            action="created",
            details={"description": "Bot was created"}
        )
        db_session.add(activity_log)
        db_session.commit()
        
        assert activity_log.id is not None
        assert activity_log.bot_id == bot.id
        assert activity_log.user_id == user.id
        assert activity_log.action == "created"
        assert activity_log.details == {"description": "Bot was created"}