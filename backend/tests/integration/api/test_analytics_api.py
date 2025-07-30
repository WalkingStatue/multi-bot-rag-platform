"""
Integration tests for analytics API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.models.conversation import ConversationSession, Message
from app.models.document import Document
from app.models.activity import ActivityLog
from tests.test_auth_helper import mock_authentication, create_mock_user


class TestAnalyticsAPI:
    """Test analytics API endpoints."""
    
    def test_get_bot_analytics_success(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test successful bot analytics retrieval."""
        # Create some test data
        session = ConversationSession(
            bot_id=test_bot.id,
            user_id=test_user.id,
            title="Test Session"
        )
        db.add(session)
        db.commit()
        
        # Add some messages
        user_message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="Hello bot"
        )
        assistant_message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="assistant",
            content="Hello user",
            message_metadata={"response_time": 1.5, "tokens_used": 25}
        )
        db.add_all([user_message, assistant_message])
        db.commit()
        
        response = client.get(
            f"/api/bots/{test_bot.id}/analytics?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["bot_id"] == str(test_bot.id)
        assert data["period_days"] == 30
        assert "metrics" in data
        assert data["metrics"]["total_conversations"] == 1
        assert data["metrics"]["total_messages"] == 2
        assert data["metrics"]["user_messages"] == 1
        assert data["metrics"]["assistant_messages"] == 1
        assert data["metrics"]["unique_users"] == 1
        assert "daily_activity" in data
        assert "top_users" in data
    
    def test_get_bot_analytics_no_permission(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test bot analytics with no permission."""
        # Remove user's permission to the bot
        db.query(BotPermission).filter(
            BotPermission.bot_id == test_bot.id,
            BotPermission.user_id == test_user.id
        ).delete()
        db.commit()
        
        response = client.get(
            f"/api/bots/{test_bot.id}/analytics?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 403
        assert "does not have access" in response.json()["detail"]
    
    def test_get_dashboard_analytics_success(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test successful dashboard analytics retrieval."""
        # Create test data
        session = ConversationSession(
            bot_id=test_bot.id,
            user_id=test_user.id,
            title="Dashboard Test Session"
        )
        db.add(session)
        db.commit()
        
        message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="Dashboard test message"
        )
        db.add(message)
        db.commit()
        
        response = client.get(
            "/api/dashboard/analytics?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == str(test_user.id)
        assert data["period_days"] == 30
        assert "metrics" in data
        assert data["metrics"]["total_bots"] >= 1
        assert data["metrics"]["owned_bots"] >= 1
        assert "bot_activity" in data
        assert "recent_conversations" in data
    
    def test_get_bot_activity_logs_success(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test successful bot activity logs retrieval."""
        # Create test activity log
        activity = ActivityLog(
            bot_id=test_bot.id,
            user_id=test_user.id,
            action="bot_created",
            details={"description": "Bot was created"}
        )
        db.add(activity)
        db.commit()
        
        response = client.get(
            f"/api/bots/{test_bot.id}/activity?limit=50",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "activity_logs" in data
        assert len(data["activity_logs"]) >= 1
        
        log_entry = data["activity_logs"][0]
        assert "id" in log_entry
        assert "action" in log_entry
        assert "details" in log_entry
        assert "created_at" in log_entry
        assert "user" in log_entry
    
    def test_get_bot_activity_logs_with_filter(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test bot activity logs with action filter."""
        # Create multiple activity logs
        activities = [
            ActivityLog(
                bot_id=test_bot.id,
                user_id=test_user.id,
                action="bot_created",
                details={"description": "Bot was created"}
            ),
            ActivityLog(
                bot_id=test_bot.id,
                user_id=test_user.id,
                action="bot_updated",
                details={"description": "Bot was updated"}
            )
        ]
        db.add_all(activities)
        db.commit()
        
        response = client.get(
            f"/api/bots/{test_bot.id}/activity?action=bot_created",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "activity_logs" in data
        # Should only return logs with the specified action
        for log in data["activity_logs"]:
            assert log["action"] == "bot_created"
    
    def test_get_system_analytics_success(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test successful system analytics retrieval."""
        response = client.get(
            "/api/system/analytics?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["period_days"] == 30
        assert "metrics" in data
        assert data["metrics"]["total_users"] >= 1
        assert data["metrics"]["total_bots"] >= 1
        assert "most_active_bots" in data
        assert "daily_activity" in data
    
    def test_export_bot_data_success(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test successful bot data export."""
        # Create test data for export
        session = ConversationSession(
            bot_id=test_bot.id,
            user_id=test_user.id,
            title="Export Test Session"
        )
        db.add(session)
        db.commit()
        
        message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="Export test message"
        )
        db.add(message)
        
        document = Document(
            bot_id=test_bot.id,
            uploaded_by=test_user.id,
            filename="test_export.txt",
            file_path="/test/path",
            file_size=1024,
            mime_type="text/plain",
            chunk_count=5
        )
        db.add(document)
        
        activity = ActivityLog(
            bot_id=test_bot.id,
            user_id=test_user.id,
            action="export_test",
            details={"test": "export"}
        )
        db.add(activity)
        db.commit()
        
        response = client.get(
            f"/api/bots/{test_bot.id}/export?format_type=json&include_messages=true&include_documents=true&include_activity=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "bot" in data
        assert data["bot"]["id"] == str(test_bot.id)
        assert data["bot"]["name"] == test_bot.name
        
        assert "export_metadata" in data
        assert data["export_metadata"]["format"] == "json"
        assert data["export_metadata"]["exported_by"] == str(test_user.id)
        
        assert "conversations" in data
        assert len(data["conversations"]) >= 1
        
        assert "documents" in data
        assert len(data["documents"]) >= 1
        
        assert "activity_logs" in data
        assert len(data["activity_logs"]) >= 1
    
    def test_export_bot_data_selective_inclusion(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test bot data export with selective data inclusion."""
        response = client.get(
            f"/api/bots/{test_bot.id}/export?include_messages=false&include_documents=false&include_activity=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "bot" in data
        assert "export_metadata" in data
        assert "conversations" not in data or data["conversations"] is None
        assert "documents" not in data or data["documents"] is None
        assert "activity_logs" in data
    
    def test_get_user_analytics_success(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test successful user analytics retrieval."""
        response = client.get(
            f"/api/users/{test_user.id}/analytics?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == str(test_user.id)
        assert data["period_days"] == 30
        assert "metrics" in data
        assert "bot_activity" in data
        assert "recent_conversations" in data
    
    def test_get_analytics_summary_success(
        self, 
        client: TestClient, 
        db: Session, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test successful analytics summary retrieval."""
        # Create some test data
        session = ConversationSession(
            bot_id=test_bot.id,
            user_id=test_user.id,
            title="Summary Test Session"
        )
        db.add(session)
        db.commit()
        
        message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="Summary test message"
        )
        db.add(message)
        db.commit()
        
        response = client.get(
            "/api/analytics/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "recent_activity" in data
        
        summary = data["summary"]
        assert "total_bots" in summary
        assert "owned_bots" in summary
        assert "messages_this_week" in summary
        assert "messages_this_month" in summary
        assert "conversations_this_week" in summary
        assert "conversations_this_month" in summary
    
    def test_analytics_endpoints_require_authentication(self, client: TestClient):
        """Test that analytics endpoints require authentication."""
        endpoints = [
            "/api/bots/test-id/analytics",
            "/api/dashboard/analytics",
            "/api/bots/test-id/activity",
            "/api/system/analytics",
            "/api/bots/test-id/export",
            "/api/users/test-id/analytics",
            "/api/analytics/summary"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Accept both 401 (no auth) and 403 (auth but no permission)
            assert response.status_code in [401, 403]
    
    def test_analytics_with_date_range_validation(
        self, 
        client: TestClient, 
        test_user: User, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test analytics endpoints with invalid date ranges."""
        # Test with days parameter too small
        response = client.get(
            f"/api/bots/{test_bot.id}/analytics?days=0",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test with days parameter too large
        response = client.get(
            f"/api/bots/{test_bot.id}/analytics?days=400",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_analytics_with_nonexistent_bot(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test analytics endpoints with nonexistent bot ID."""
        fake_bot_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/api/bots/{fake_bot_id}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 403  # No permission to nonexistent bot
    
    def test_activity_logs_limit_validation(
        self, 
        client: TestClient, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test activity logs endpoint with limit validation."""
        # Test with limit too small
        response = client.get(
            f"/api/bots/{test_bot.id}/activity?limit=0",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test with limit too large
        response = client.get(
            f"/api/bots/{test_bot.id}/activity?limit=300",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_export_format_validation(
        self, 
        client: TestClient, 
        test_bot: Bot,
        auth_headers: dict
    ):
        """Test export endpoint with invalid format."""
        response = client.get(
            f"/api/bots/{test_bot.id}/export?format_type=xml",
            headers=auth_headers
        )
        assert response.status_code == 422