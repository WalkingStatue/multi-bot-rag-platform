"""
Unit tests for analytics service.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.analytics_service import AnalyticsService
from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.models.conversation import ConversationSession, Message
from app.models.document import Document
from app.models.activity import ActivityLog


class TestAnalyticsService:
    """Test analytics service functionality."""
    
    def test_get_bot_usage_analytics_success(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test successful bot usage analytics retrieval."""
        analytics_service = AnalyticsService(db)
        
        # Create test data
        session = ConversationSession(
            bot_id=test_bot.id,
            user_id=test_user.id,
            title="Test Analytics Session"
        )
        db.add(session)
        db.commit()
        
        # Add messages with metadata
        user_message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="Test user message"
        )
        assistant_message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="assistant",
            content="Test assistant response",
            message_metadata={"response_time": 2.5, "tokens_used": 50}
        )
        db.add_all([user_message, assistant_message])
        
        # Add a document
        document = Document(
            bot_id=test_bot.id,
            uploaded_by=test_user.id,
            filename="test_analytics.txt",
            file_path="/test/path",
            file_size=2048,
            mime_type="text/plain",
            chunk_count=10
        )
        db.add(document)
        db.commit()
        
        # Get analytics
        analytics = analytics_service.get_bot_usage_analytics(
            bot_id=str(test_bot.id),
            user_id=str(test_user.id),
            days=30
        )
        
        assert analytics["bot_id"] == str(test_bot.id)
        assert analytics["period_days"] == 30
        
        metrics = analytics["metrics"]
        assert metrics["total_conversations"] == 1
        assert metrics["total_messages"] == 2
        assert metrics["user_messages"] == 1
        assert metrics["assistant_messages"] == 1
        assert metrics["unique_users"] == 1
        assert metrics["documents_count"] == 1
        
        assert "daily_activity" in analytics
        assert "top_users" in analytics
        assert len(analytics["top_users"]) >= 1
    
    def test_get_bot_usage_analytics_no_permission(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test bot usage analytics with no permission."""
        analytics_service = AnalyticsService(db)
        
        # Remove user's permission
        db.query(BotPermission).filter(
            BotPermission.bot_id == test_bot.id,
            BotPermission.user_id == test_user.id
        ).delete()
        db.commit()
        
        with pytest.raises(ValueError, match="does not have access"):
            analytics_service.get_bot_usage_analytics(
                bot_id=str(test_bot.id),
                user_id=str(test_user.id),
                days=30
            )
    
    def test_get_user_dashboard_analytics_success(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test successful user dashboard analytics retrieval."""
        analytics_service = AnalyticsService(db)
        
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
        
        # Get analytics
        analytics = analytics_service.get_user_dashboard_analytics(
            user_id=str(test_user.id),
            days=30
        )
        
        assert analytics["user_id"] == str(test_user.id)
        assert analytics["period_days"] == 30
        
        metrics = analytics["metrics"]
        assert metrics["total_bots"] >= 1
        assert metrics["owned_bots"] >= 1
        assert metrics["total_conversations"] >= 1
        assert metrics["messages_sent"] >= 1
        
        assert "bot_activity" in analytics
        assert "recent_conversations" in analytics
    
    def test_get_user_dashboard_analytics_no_bots(
        self, 
        db: Session, 
        test_user: User
    ):
        """Test user dashboard analytics with no accessible bots."""
        analytics_service = AnalyticsService(db)
        
        # Remove all bot permissions for user
        db.query(BotPermission).filter(
            BotPermission.user_id == test_user.id
        ).delete()
        db.commit()
        
        analytics = analytics_service.get_user_dashboard_analytics(
            user_id=str(test_user.id),
            days=30
        )
        
        assert analytics["user_id"] == str(test_user.id)
        metrics = analytics["metrics"]
        assert metrics["total_bots"] == 0
        assert metrics["owned_bots"] == 0
        assert metrics["total_conversations"] == 0
        assert metrics["total_messages"] == 0
    
    def test_get_bot_activity_logs_success(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test successful bot activity logs retrieval."""
        analytics_service = AnalyticsService(db)
        
        # Create test activity logs
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
                details={"field": "name", "old_value": "Old Name", "new_value": "New Name"}
            )
        ]
        db.add_all(activities)
        db.commit()
        
        # Get activity logs
        logs = analytics_service.get_bot_activity_logs(
            bot_id=str(test_bot.id),
            user_id=str(test_user.id),
            limit=50
        )
        
        assert len(logs) >= 2
        
        # Check log structure
        log = logs[0]
        assert "id" in log
        assert "action" in log
        assert "details" in log
        assert "created_at" in log
        assert "user" in log
        assert log["user"]["username"] == test_user.username
    
    def test_get_bot_activity_logs_with_filter(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test bot activity logs with action filter."""
        analytics_service = AnalyticsService(db)
        
        # Create test activity logs
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
        
        # Get filtered activity logs
        logs = analytics_service.get_bot_activity_logs(
            bot_id=str(test_bot.id),
            user_id=str(test_user.id),
            limit=50,
            action_filter="bot_created"
        )
        
        # Should only return logs with the specified action
        for log in logs:
            assert log["action"] == "bot_created"
    
    def test_get_system_analytics_success(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test successful system analytics retrieval."""
        analytics_service = AnalyticsService(db)
        
        # Create some test data
        session = ConversationSession(
            bot_id=test_bot.id,
            user_id=test_user.id,
            title="System Analytics Test"
        )
        db.add(session)
        db.commit()
        
        message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="System analytics test message"
        )
        db.add(message)
        db.commit()
        
        # Get system analytics
        analytics = analytics_service.get_system_analytics(
            user_id=str(test_user.id),
            days=30
        )
        
        assert analytics["period_days"] == 30
        
        metrics = analytics["metrics"]
        assert metrics["total_users"] >= 1
        assert metrics["total_bots"] >= 1
        assert metrics["total_conversations"] >= 1
        assert metrics["total_messages"] >= 1
        
        assert "most_active_bots" in analytics
        assert "daily_activity" in analytics
    
    def test_export_bot_data_success(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test successful bot data export."""
        analytics_service = AnalyticsService(db)
        
        # Create comprehensive test data
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
            content="Export test message",
            message_metadata={"test": "metadata"}
        )
        db.add(message)
        
        document = Document(
            bot_id=test_bot.id,
            uploaded_by=test_user.id,
            filename="export_test.txt",
            file_path="/export/test/path",
            file_size=4096,
            mime_type="text/plain",
            chunk_count=20
        )
        db.add(document)
        
        activity = ActivityLog(
            bot_id=test_bot.id,
            user_id=test_user.id,
            action="export_test_action",
            details={"test": "export activity"}
        )
        db.add(activity)
        db.commit()
        
        # Export bot data
        export_data = analytics_service.export_bot_data(
            bot_id=str(test_bot.id),
            user_id=str(test_user.id),
            format_type="json",
            include_messages=True,
            include_documents=True,
            include_activity=True
        )
        
        # Verify export structure
        assert "bot" in export_data
        assert export_data["bot"]["id"] == str(test_bot.id)
        assert export_data["bot"]["name"] == test_bot.name
        
        assert "export_metadata" in export_data
        assert export_data["export_metadata"]["format"] == "json"
        assert export_data["export_metadata"]["exported_by"] == str(test_user.id)
        
        assert "conversations" in export_data
        assert len(export_data["conversations"]) >= 1
        
        conversation = export_data["conversations"][0]
        assert conversation["session_id"] == str(session.id)
        assert len(conversation["messages"]) >= 1
        
        assert "documents" in export_data
        assert len(export_data["documents"]) >= 1
        
        assert "activity_logs" in export_data
        assert len(export_data["activity_logs"]) >= 1
    
    def test_export_bot_data_selective_inclusion(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test bot data export with selective data inclusion."""
        analytics_service = AnalyticsService(db)
        
        # Export with selective inclusion
        export_data = analytics_service.export_bot_data(
            bot_id=str(test_bot.id),
            user_id=str(test_user.id),
            format_type="json",
            include_messages=False,
            include_documents=False,
            include_activity=True
        )
        
        # Verify selective inclusion
        assert "bot" in export_data
        assert "export_metadata" in export_data
        assert "conversations" not in export_data
        assert "documents" not in export_data
        assert "activity_logs" in export_data
    
    def test_export_bot_data_no_permission(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test bot data export with no permission."""
        analytics_service = AnalyticsService(db)
        
        # Remove user's permission
        db.query(BotPermission).filter(
            BotPermission.bot_id == test_bot.id,
            BotPermission.user_id == test_user.id
        ).delete()
        db.commit()
        
        with pytest.raises(ValueError, match="does not have access"):
            analytics_service.export_bot_data(
                bot_id=str(test_bot.id),
                user_id=str(test_user.id)
            )
    
    def test_analytics_with_date_filtering(
        self, 
        db: Session, 
        test_user: User, 
        test_bot: Bot
    ):
        """Test analytics with different date ranges."""
        analytics_service = AnalyticsService(db)
        
        # Create old and new messages
        session = ConversationSession(
            bot_id=test_bot.id,
            user_id=test_user.id,
            title="Date Filter Test"
        )
        db.add(session)
        db.commit()
        
        # Old message (outside 7-day range)
        old_message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="Old message",
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        
        # New message (within 7-day range)
        new_message = Message(
            session_id=session.id,
            bot_id=test_bot.id,
            user_id=test_user.id,
            role="user",
            content="New message"
        )
        
        db.add_all([old_message, new_message])
        db.commit()
        
        # Get 7-day analytics
        analytics_7d = analytics_service.get_bot_usage_analytics(
            bot_id=str(test_bot.id),
            user_id=str(test_user.id),
            days=7
        )
        
        # Get 30-day analytics
        analytics_30d = analytics_service.get_bot_usage_analytics(
            bot_id=str(test_bot.id),
            user_id=str(test_user.id),
            days=30
        )
        
        # 7-day should have fewer messages than 30-day
        assert analytics_7d["metrics"]["total_messages"] < analytics_30d["metrics"]["total_messages"]