"""
Integration tests for user management API endpoints.
Tests the new settings and analytics functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserSettings
from app.models.bot import Bot
from app.models.conversation import ConversationSession, Message
from app.models.document import Document


class TestUserManagementIntegration:
    """Integration tests for user management endpoints."""
    
    def test_get_user_settings_creates_default(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """Test that getting user settings creates default settings if none exist."""
        # Act
        response = client.get("/api/users/settings", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "light"
        assert data["language"] == "en"
        assert data["timezone"] == "UTC"
        assert data["notifications_enabled"] is True
        assert data["email_notifications"] is True
        assert data["max_conversation_history"] == 50
        assert data["auto_save_conversations"] is True
        assert data["user_id"] == str(test_user.id)
        
        # Verify settings were created in database
        settings = db_session.query(UserSettings).filter(UserSettings.user_id == test_user.id).first()
        assert settings is not None
        assert settings.theme == "light"
    
    def test_update_user_settings_success(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """Test successful user settings update."""
        # Arrange - Create initial settings
        settings = UserSettings(
            user_id=test_user.id,
            theme="light",
            language="en",
            timezone="UTC"
        )
        db_session.add(settings)
        db_session.commit()
        
        update_data = {
            "theme": "dark",
            "language": "es",
            "timezone": "America/New_York",
            "notifications_enabled": False,
            "default_llm_provider": "anthropic",
            "max_conversation_history": 100
        }
        
        # Act
        response = client.put("/api/users/settings", json=update_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["language"] == "es"
        assert data["timezone"] == "America/New_York"
        assert data["notifications_enabled"] is False
        assert data["default_llm_provider"] == "anthropic"
        assert data["max_conversation_history"] == 100
        
        # Verify changes in database
        db_session.refresh(settings)
        assert settings.theme == "dark"
        assert settings.language == "es"
        assert settings.timezone == "America/New_York"
        assert settings.notifications_enabled is False
        assert settings.default_llm_provider == "anthropic"
        assert settings.max_conversation_history == 100
    
    def test_update_user_settings_invalid_theme(self, client: TestClient, auth_headers: dict):
        """Test user settings update with invalid theme."""
        update_data = {
            "theme": "invalid_theme"
        }
        
        # Act
        response = client.put("/api/users/settings", json=update_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["detail"][0]["type"] == "string_pattern_mismatch"
    
    def test_update_user_settings_invalid_provider(self, client: TestClient, auth_headers: dict):
        """Test user settings update with invalid provider."""
        update_data = {
            "default_llm_provider": "invalid_provider"
        }
        
        # Act
        response = client.put("/api/users/settings", json=update_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["detail"][0]["type"] == "string_pattern_mismatch"
    
    def test_update_user_settings_invalid_history_limit(self, client: TestClient, auth_headers: dict):
        """Test user settings update with invalid conversation history limit."""
        update_data = {
            "max_conversation_history": 300  # Exceeds maximum of 200
        }
        
        # Act
        response = client.put("/api/users/settings", json=update_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["detail"][0]["type"] == "less_than_equal"
    
    def test_get_user_analytics_empty_data(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test user analytics with no data."""
        # Act
        response = client.get("/api/users/analytics", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Check activity summary
        assert data["activity_summary"]["total_bots"] == 0
        assert data["activity_summary"]["total_conversations"] == 0
        assert data["activity_summary"]["total_messages"] == 0
        assert data["activity_summary"]["total_documents_uploaded"] == 0
        assert data["activity_summary"]["most_used_bot"] is None
        assert data["activity_summary"]["most_used_provider"] is None
        assert data["activity_summary"]["activity_last_30_days"] == 0
        
        # Check other sections
        assert data["bot_usage"] == []
        assert data["conversation_analytics"]["total_conversations"] == 0
        assert data["conversation_analytics"]["total_messages"] == 0
        assert data["provider_usage"] == {}
        assert data["recent_activity"] == []
    
    def test_get_user_analytics_with_data(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """Test user analytics with actual data."""
        # Arrange - Create test data
        # Create a bot
        bot = Bot(
            name="Test Bot",
            description="A test bot",
            system_prompt="You are a test assistant",
            owner_id=test_user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        db_session.add(bot)
        db_session.commit()
        db_session.refresh(bot)
        
        # Create a conversation session
        session = ConversationSession(
            bot_id=bot.id,
            user_id=test_user.id,
            title="Test Conversation"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Create messages
        message1 = Message(
            session_id=session.id,
            bot_id=bot.id,
            user_id=test_user.id,
            role="user",
            content="Hello"
        )
        message2 = Message(
            session_id=session.id,
            bot_id=bot.id,
            user_id=test_user.id,
            role="assistant",
            content="Hi there!"
        )
        db_session.add_all([message1, message2])
        db_session.commit()
        
        # Create a document
        document = Document(
            bot_id=bot.id,
            uploaded_by=test_user.id,
            filename="test.txt",
            file_path="/test/path",
            file_size=1024,
            mime_type="text/plain"
        )
        db_session.add(document)
        db_session.commit()
        
        # Act
        response = client.get("/api/users/analytics", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Check activity summary
        assert data["activity_summary"]["total_bots"] == 1
        assert data["activity_summary"]["total_conversations"] == 1
        assert data["activity_summary"]["total_messages"] == 2
        assert data["activity_summary"]["total_documents_uploaded"] == 1
        assert data["activity_summary"]["most_used_bot"] == "Test Bot"
        assert data["activity_summary"]["most_used_provider"] == "openai"
        
        # Check bot usage
        assert len(data["bot_usage"]) == 1
        bot_usage = data["bot_usage"][0]
        assert bot_usage["bot_name"] == "Test Bot"
        assert bot_usage["message_count"] == 2
        assert bot_usage["conversation_count"] == 1
        assert bot_usage["document_count"] == 1
        
        # Check conversation analytics
        assert data["conversation_analytics"]["total_conversations"] == 1
        assert data["conversation_analytics"]["total_messages"] == 2
        assert data["conversation_analytics"]["avg_messages_per_conversation"] == 2.0
        assert data["conversation_analytics"]["most_active_bot"] == "Test Bot"
        
        # Check provider usage
        assert data["provider_usage"]["openai"] == 2
    
    def test_get_user_activity_summary(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """Test user activity summary endpoint."""
        # Arrange - Create a bot for activity
        bot = Bot(
            name="Activity Bot",
            description="A bot for activity testing",
            system_prompt="You are an activity assistant",
            owner_id=test_user.id,
            llm_provider="anthropic",
            llm_model="claude-3-sonnet"
        )
        db_session.add(bot)
        db_session.commit()
        
        # Act
        response = client.get("/api/users/activity?limit=25", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "activity_summary" in data
        assert "message" in data
        assert "Retrieved activity summary" in data["message"]
        assert data["activity_summary"]["total_bots"] == 1
    
    def test_get_user_activity_invalid_limit(self, client: TestClient, auth_headers: dict):
        """Test user activity with invalid limit parameter."""
        # Act
        response = client.get("/api/users/activity?limit=200", headers=auth_headers)  # Exceeds maximum
        
        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["detail"][0]["type"] == "less_than_equal"
    
    def test_user_settings_unauthorized(self, client: TestClient):
        """Test user settings endpoints without authentication."""
        # Test GET settings
        response = client.get("/api/users/settings")
        assert response.status_code == 403
        
        # Test PUT settings
        response = client.put("/api/users/settings", json={"theme": "dark"})
        assert response.status_code == 403
    
    def test_user_analytics_unauthorized(self, client: TestClient):
        """Test user analytics endpoints without authentication."""
        # Test analytics
        response = client.get("/api/users/analytics")
        assert response.status_code == 403
        
        # Test activity
        response = client.get("/api/users/activity")
        assert response.status_code == 403
    
    def test_user_settings_persistence(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """Test that user settings persist across requests."""
        # Arrange - Update settings
        update_data = {
            "theme": "dark",
            "language": "fr",
            "notifications_enabled": False,
            "max_conversation_history": 75
        }
        
        # Act - Update settings
        response = client.put("/api/users/settings", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Act - Get settings again
        response = client.get("/api/users/settings", headers=auth_headers)
        
        # Assert - Settings should persist
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["language"] == "fr"
        assert data["notifications_enabled"] is False
        assert data["max_conversation_history"] == 75
        
        # Verify in database
        settings = db_session.query(UserSettings).filter(UserSettings.user_id == test_user.id).first()
        assert settings.theme == "dark"
        assert settings.language == "fr"
        assert settings.notifications_enabled is False
        assert settings.max_conversation_history == 75
    
    def test_user_analytics_multiple_bots(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """Test user analytics with multiple bots and different providers."""
        # Arrange - Create multiple bots with different providers
        bot1 = Bot(
            name="OpenAI Bot",
            description="Bot using OpenAI",
            system_prompt="You are an OpenAI assistant",
            owner_id=test_user.id,
            llm_provider="openai",
            llm_model="gpt-4"
        )
        bot2 = Bot(
            name="Anthropic Bot",
            description="Bot using Anthropic",
            system_prompt="You are an Anthropic assistant",
            owner_id=test_user.id,
            llm_provider="anthropic",
            llm_model="claude-3-sonnet"
        )
        db_session.add_all([bot1, bot2])
        db_session.commit()
        
        # Create conversations and messages for both bots
        session1 = ConversationSession(bot_id=bot1.id, user_id=test_user.id, title="OpenAI Chat")
        session2 = ConversationSession(bot_id=bot2.id, user_id=test_user.id, title="Anthropic Chat")
        db_session.add_all([session1, session2])
        db_session.commit()
        
        # More messages for bot1 to make it "most used"
        messages = [
            Message(session_id=session1.id, bot_id=bot1.id, user_id=test_user.id, role="user", content="Hello OpenAI"),
            Message(session_id=session1.id, bot_id=bot1.id, user_id=test_user.id, role="assistant", content="Hi from OpenAI"),
            Message(session_id=session1.id, bot_id=bot1.id, user_id=test_user.id, role="user", content="How are you?"),
            Message(session_id=session2.id, bot_id=bot2.id, user_id=test_user.id, role="user", content="Hello Anthropic"),
            Message(session_id=session2.id, bot_id=bot2.id, user_id=test_user.id, role="assistant", content="Hi from Anthropic"),
        ]
        db_session.add_all(messages)
        db_session.commit()
        
        # Act
        response = client.get("/api/users/analytics", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Check activity summary
        assert data["activity_summary"]["total_bots"] == 2
        assert data["activity_summary"]["total_conversations"] == 2
        assert data["activity_summary"]["total_messages"] == 5
        assert data["activity_summary"]["most_used_bot"] == "OpenAI Bot"  # Has more messages
        assert data["activity_summary"]["most_used_provider"] == "openai"  # Has more messages
        
        # Check bot usage
        assert len(data["bot_usage"]) == 2
        bot_names = [bot["bot_name"] for bot in data["bot_usage"]]
        assert "OpenAI Bot" in bot_names
        assert "Anthropic Bot" in bot_names
        
        # Check provider usage
        assert data["provider_usage"]["openai"] == 3  # 3 messages from OpenAI bot
        assert data["provider_usage"]["anthropic"] == 2  # 2 messages from Anthropic bot