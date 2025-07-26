"""
Tests for Pydantic schemas.
"""
import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError

from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    APIKeyCreate, APIKeyResponse,
    BotCreate, BotUpdate, BotResponse,
    BotPermissionCreate, BotPermissionResponse,
    ConversationSessionCreate, ConversationSessionResponse,
    MessageCreate, MessageResponse, ChatRequest, ChatResponse,
    DocumentResponse, DocumentUpload,
    ActivityLogResponse
)


class TestUserSchemas:
    """Test user-related schemas."""
    
    def test_user_create_valid(self):
        """Test valid user creation schema."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        user = UserCreate(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.full_name == "Test User"
    
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_create_short_username(self):
        """Test user creation with short username."""
        user_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_create_short_password(self):
        """Test user creation with short password."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short"  # Too short
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_login_valid(self):
        """Test valid user login schema."""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        login = UserLogin(**login_data)
        
        assert login.username == "testuser"
        assert login.password == "password123"


class TestAPIKeySchemas:
    """Test API key schemas."""
    
    def test_api_key_create_valid(self):
        """Test valid API key creation."""
        api_key_data = {
            "provider": "openai",
            "api_key": "sk-1234567890abcdef"
        }
        api_key = APIKeyCreate(**api_key_data)
        
        assert api_key.provider == "openai"
        assert api_key.api_key == "sk-1234567890abcdef"
    
    def test_api_key_create_invalid_provider(self):
        """Test API key creation with invalid provider."""
        api_key_data = {
            "provider": "invalid_provider",
            "api_key": "sk-1234567890abcdef"
        }
        
        with pytest.raises(ValidationError):
            APIKeyCreate(**api_key_data)
    
    def test_api_key_create_short_key(self):
        """Test API key creation with short key."""
        api_key_data = {
            "provider": "openai",
            "api_key": "short"  # Too short
        }
        
        with pytest.raises(ValidationError):
            APIKeyCreate(**api_key_data)


class TestBotSchemas:
    """Test bot-related schemas."""
    
    def test_bot_create_valid(self):
        """Test valid bot creation schema."""
        bot_data = {
            "name": "Test Bot",
            "description": "A test bot",
            "system_prompt": "You are a helpful assistant",
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
        bot = BotCreate(**bot_data)
        
        assert bot.name == "Test Bot"
        assert bot.system_prompt == "You are a helpful assistant"
        assert bot.llm_provider == "openai"
        assert bot.temperature == 0.7
    
    def test_bot_create_invalid_provider(self):
        """Test bot creation with invalid LLM provider."""
        bot_data = {
            "name": "Test Bot",
            "system_prompt": "You are a helpful assistant",
            "llm_provider": "invalid_provider"
        }
        
        with pytest.raises(ValidationError):
            BotCreate(**bot_data)
    
    def test_bot_create_invalid_temperature(self):
        """Test bot creation with invalid temperature."""
        bot_data = {
            "name": "Test Bot",
            "system_prompt": "You are a helpful assistant",
            "temperature": 3.0  # Too high
        }
        
        with pytest.raises(ValidationError):
            BotCreate(**bot_data)
    
    def test_bot_permission_create_valid(self):
        """Test valid bot permission creation."""
        permission_data = {
            "user_id": str(uuid.uuid4()),
            "role": "editor"
        }
        permission = BotPermissionCreate(**permission_data)
        
        assert permission.role == "editor"
    
    def test_bot_permission_create_invalid_role(self):
        """Test bot permission creation with invalid role."""
        permission_data = {
            "user_id": str(uuid.uuid4()),
            "role": "invalid_role"
        }
        
        with pytest.raises(ValidationError):
            BotPermissionCreate(**permission_data)


class TestConversationSchemas:
    """Test conversation-related schemas."""
    
    def test_conversation_session_create_valid(self):
        """Test valid conversation session creation."""
        session_data = {
            "bot_id": str(uuid.uuid4()),
            "title": "Test Conversation"
        }
        session = ConversationSessionCreate(**session_data)
        
        assert session.title == "Test Conversation"
    
    def test_message_create_valid(self):
        """Test valid message creation."""
        message_data = {
            "session_id": str(uuid.uuid4()),
            "role": "user",
            "content": "Hello, bot!",
            "message_metadata": {"tokens": 3}
        }
        message = MessageCreate(**message_data)
        
        assert message.role == "user"
        assert message.content == "Hello, bot!"
        assert message.message_metadata == {"tokens": 3}
    
    def test_message_create_invalid_role(self):
        """Test message creation with invalid role."""
        message_data = {
            "session_id": str(uuid.uuid4()),
            "role": "invalid_role",
            "content": "Hello, bot!"
        }
        
        with pytest.raises(ValidationError):
            MessageCreate(**message_data)
    
    def test_chat_request_valid(self):
        """Test valid chat request."""
        chat_data = {
            "message": "Hello, how are you?",
            "session_id": str(uuid.uuid4())
        }
        chat_request = ChatRequest(**chat_data)
        
        assert chat_request.message == "Hello, how are you?"
    
    def test_chat_request_empty_message(self):
        """Test chat request with empty message."""
        chat_data = {
            "message": ""  # Empty message
        }
        
        with pytest.raises(ValidationError):
            ChatRequest(**chat_data)
    
    def test_chat_request_long_message(self):
        """Test chat request with very long message."""
        chat_data = {
            "message": "x" * 10001  # Too long
        }
        
        with pytest.raises(ValidationError):
            ChatRequest(**chat_data)


class TestDocumentSchemas:
    """Test document-related schemas."""
    
    def test_document_upload_valid(self):
        """Test valid document upload schema."""
        upload_data = {
            "bot_id": str(uuid.uuid4())
        }
        upload = DocumentUpload(**upload_data)
        
        assert upload.bot_id is not None