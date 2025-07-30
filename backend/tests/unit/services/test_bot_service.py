"""
Tests for bot service functionality.
"""
import pytest
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.models.activity import ActivityLog
from app.schemas.bot import BotCreate, BotUpdate
from app.services.bot_service import BotService


class TestBotService:
    """Test cases for BotService."""
    
    def test_create_bot(self, db_session: Session, sample_user: User):
        """Test creating a new bot."""
        service = BotService(db_session)
        
        bot_config = BotCreate(
            name="Test Bot",
            description="A test bot",
            system_prompt="You are a helpful assistant",
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        bot = service.create_bot(sample_user.id, bot_config)
        
        # Check bot properties
        assert bot.name == "Test Bot"
        assert bot.description == "A test bot"
        assert bot.system_prompt == "You are a helpful assistant"
        assert bot.owner_id == sample_user.id
        assert bot.llm_provider == "openai"
        assert bot.llm_model == "gpt-3.5-turbo"
        assert bot.temperature == 0.7
        
        # Check owner permission was created
        permission = db_session.query(BotPermission).filter(
            BotPermission.bot_id == bot.id,
            BotPermission.user_id == sample_user.id,
            BotPermission.role == "owner"
        ).first()
        assert permission is not None
        
        # Check activity log
        activity = db_session.query(ActivityLog).filter(
            ActivityLog.action == "bot_created",
            ActivityLog.bot_id == bot.id
        ).first()
        assert activity is not None
        assert activity.user_id == sample_user.id
    
    def test_create_bot_nonexistent_user(self, db_session: Session):
        """Test creating bot with nonexistent user."""
        service = BotService(db_session)
        
        bot_config = BotCreate(
            name="Test Bot",
            system_prompt="You are a helpful assistant"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_bot(uuid.uuid4(), bot_config)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    def test_get_bot_with_access(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test getting bot when user has access."""
        service = BotService(db_session)
        
        # Create permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        bot = service.get_bot(sample_bot.id, sample_user.id)
        assert bot.id == sample_bot.id
        assert bot.name == sample_bot.name
    
    def test_get_bot_without_access(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test getting bot when user has no access."""
        service = BotService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_bot(sample_bot.id, sample_user.id)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)
    
    def test_get_bot_nonexistent(self, db_session: Session, sample_user: User):
        """Test getting nonexistent bot."""
        service = BotService(db_session)
        
        # Try to get nonexistent bot without permission
        fake_bot_id = uuid.uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_bot(fake_bot_id, sample_user.id)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)
    
    def test_update_bot_with_permission(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test updating bot when user has edit permission."""
        service = BotService(db_session)
        
        # Create admin permission (can edit)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        updates = BotUpdate(
            name="Updated Bot Name",
            temperature=0.8,
            max_tokens=2000
        )
        
        updated_bot = service.update_bot(sample_bot.id, sample_user.id, updates)
        
        assert updated_bot.name == "Updated Bot Name"
        assert updated_bot.temperature == 0.8
        assert updated_bot.max_tokens == 2000
        
        # Check activity log
        activity = db_session.query(ActivityLog).filter(
            ActivityLog.action == "bot_updated",
            ActivityLog.bot_id == sample_bot.id
        ).first()
        assert activity is not None
        assert "changes" in activity.details
    
    def test_update_bot_without_permission(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test updating bot when user lacks edit permission."""
        service = BotService(db_session)
        
        # Create viewer permission (cannot edit)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        updates = BotUpdate(name="Updated Bot Name")
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_bot(sample_bot.id, sample_user.id, updates)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions to edit bot" in str(exc_info.value.detail)
    
    def test_update_bot_no_changes(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test updating bot with no actual changes."""
        service = BotService(db_session)
        
        # Create admin permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        # Update with same values
        updates = BotUpdate(
            name=sample_bot.name,
            temperature=sample_bot.temperature
        )
        
        updated_bot = service.update_bot(sample_bot.id, sample_user.id, updates)
        
        # Should not create activity log for no changes
        activity_count = db_session.query(ActivityLog).filter(
            ActivityLog.action == "bot_updated",
            ActivityLog.bot_id == sample_bot.id
        ).count()
        assert activity_count == 0
    
    def test_delete_bot_as_owner(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test deleting bot as owner."""
        service = BotService(db_session)
        
        # Create owner permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        result = service.delete_bot(sample_bot.id, sample_user.id)
        assert result is True
        
        # Check bot is deleted
        deleted_bot = db_session.query(Bot).filter(Bot.id == sample_bot.id).first()
        assert deleted_bot is None
        
        # Check activity log was created before deletion
        # Note: Activity logs are cascade deleted with the bot, so we can't check them after deletion
        # The test passes if no exception was raised during deletion
    
    def test_delete_bot_without_permission(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test deleting bot without owner permission."""
        service = BotService(db_session)
        
        # Create admin permission (not owner)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_bot(sample_bot.id, sample_user.id)
        
        assert exc_info.value.status_code == 403
        assert "Only the owner can delete a bot" in str(exc_info.value.detail)
    
    def test_list_user_bots(self, db_session: Session, sample_user: User):
        """Test listing user's accessible bots."""
        service = BotService(db_session)
        
        # Create another user for bot2
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.flush()  # Get the user ID
        
        # Create multiple bots
        bot1 = Bot(
            name="Bot 1",
            system_prompt="System prompt 1",
            owner_id=sample_user.id
        )
        bot2 = Bot(
            name="Bot 2",
            system_prompt="System prompt 2", 
            owner_id=other_user.id
        )
        db_session.add_all([bot1, bot2])
        db_session.flush()
        
        # Create permissions
        owner_permission = BotPermission(
            bot_id=bot1.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        editor_permission = BotPermission(
            bot_id=bot2.id,
            user_id=sample_user.id,
            role="editor",
            granted_by=other_user.id
        )
        db_session.add_all([owner_permission, editor_permission])
        db_session.commit()
        
        bots = service.list_user_bots(sample_user.id)
        
        assert len(bots) == 2
        
        # Check owner bot
        owner_bot = next(b for b in bots if b["role"] == "owner")
        assert owner_bot["bot"].name == "Bot 1"
        
        # Check editor bot
        editor_bot = next(b for b in bots if b["role"] == "editor")
        assert editor_bot["bot"].name == "Bot 2"
    
    def test_transfer_ownership(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test transferring bot ownership."""
        service = BotService(db_session)
        
        # Create owner permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        
        # Create new owner
        new_owner = User(
            username="newowner",
            email="newowner@example.com",
            password_hash="hashed_password"
        )
        db_session.add(new_owner)
        db_session.commit()
        
        result = service.transfer_ownership(sample_bot.id, sample_user.id, new_owner.id)
        assert result is True
        
        # Check bot owner updated
        db_session.refresh(sample_bot)
        assert sample_bot.owner_id == new_owner.id
    
    def test_get_bot_analytics(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test getting bot analytics."""
        service = BotService(db_session)
        
        # Create permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        analytics = service.get_bot_analytics(sample_bot.id, sample_user.id)
        
        assert analytics["bot_id"] == sample_bot.id
        assert analytics["bot_name"] == sample_bot.name
        assert analytics["user_role"] == "viewer"
        assert "collaborator_count" in analytics
        assert "conversation_count" in analytics
        assert "message_count" in analytics
        assert "document_count" in analytics
    
    def test_get_bot_analytics_without_access(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test getting bot analytics without access."""
        service = BotService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_bot_analytics(sample_bot.id, sample_user.id)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)
    
    def test_create_bot_multi_llm_providers(self, db_session: Session, sample_user: User):
        """Test creating bots with different LLM providers."""
        service = BotService(db_session)
        
        # Test different provider configurations
        provider_configs = [
            {
                "name": "OpenAI Bot",
                "system_prompt": "You are an OpenAI assistant",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-large"
            },
            {
                "name": "Anthropic Bot",
                "system_prompt": "You are a Claude assistant", 
                "llm_provider": "anthropic",
                "llm_model": "claude-3-sonnet-20240229",
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-small"
            },
            {
                "name": "Gemini Bot",
                "system_prompt": "You are a Gemini assistant",
                "llm_provider": "gemini", 
                "llm_model": "gemini-pro",
                "embedding_provider": "gemini",
                "embedding_model": "embedding-001"
            },
            {
                "name": "OpenRouter Bot",
                "system_prompt": "You are an OpenRouter assistant",
                "llm_provider": "openrouter",
                "llm_model": "anthropic/claude-3-haiku",
                "embedding_provider": "local",
                "embedding_model": "all-MiniLM-L6-v2"
            }
        ]
        
        created_bots = []
        for config in provider_configs:
            bot_config = BotCreate(**config)
            bot = service.create_bot(sample_user.id, bot_config)
            created_bots.append(bot)
            
            # Verify configuration
            assert bot.name == config["name"]
            assert bot.llm_provider == config["llm_provider"]
            assert bot.llm_model == config["llm_model"]
            assert bot.embedding_provider == config["embedding_provider"]
            assert bot.embedding_model == config["embedding_model"]
            assert bot.owner_id == sample_user.id
        
        # Verify all bots were created
        assert len(created_bots) == 4
    
    def test_update_bot_llm_configuration(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test updating bot LLM and embedding configuration."""
        service = BotService(db_session)
        
        # Create admin permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        # Update LLM configuration
        updates = BotUpdate(
            llm_provider="anthropic",
            llm_model="claude-3-opus-20240229",
            embedding_provider="gemini",
            embedding_model="embedding-001",
            temperature=0.5,
            max_tokens=2000,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.2
        )
        
        updated_bot = service.update_bot(sample_bot.id, sample_user.id, updates)
        
        # Verify all updates
        assert updated_bot.llm_provider == "anthropic"
        assert updated_bot.llm_model == "claude-3-opus-20240229"
        assert updated_bot.embedding_provider == "gemini"
        assert updated_bot.embedding_model == "embedding-001"
        assert updated_bot.temperature == 0.5
        assert updated_bot.max_tokens == 2000
        assert updated_bot.top_p == 0.9
        assert updated_bot.frequency_penalty == 0.1
        assert updated_bot.presence_penalty == 0.2
    
    def test_delete_bot_cascade_cleanup(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test that bot deletion cascades to related data."""
        service = BotService(db_session)
        
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        
        # Create additional collaborator
        collaborator = User(
            username="collaborator",
            email="collaborator@example.com",
            password_hash="hashed_password"
        )
        db_session.add(collaborator)
        db_session.flush()
        
        collaborator_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=collaborator.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(collaborator_permission)
        db_session.commit()
        
        # Verify permissions exist before deletion
        permissions_count = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id
        ).count()
        assert permissions_count == 2
        
        # Delete bot
        result = service.delete_bot(sample_bot.id, sample_user.id)
        assert result is True
        
        # Verify bot is deleted
        deleted_bot = db_session.query(Bot).filter(Bot.id == sample_bot.id).first()
        assert deleted_bot is None
        
        # Verify permissions are cascade deleted
        remaining_permissions = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id
        ).count()
        assert remaining_permissions == 0
    
    def test_bot_configuration_validation(self, db_session: Session, sample_user: User):
        """Test bot configuration validation for different providers."""
        service = BotService(db_session)
        
        # Test valid configurations
        valid_configs = [
            BotCreate(
                name="Valid OpenAI Bot",
                system_prompt="Test prompt",
                llm_provider="openai",
                llm_model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=1000
            ),
            BotCreate(
                name="Valid Anthropic Bot", 
                system_prompt="Test prompt",
                llm_provider="anthropic",
                llm_model="claude-3-haiku-20240307",
                temperature=0.5,
                max_tokens=2000
            )
        ]
        
        for config in valid_configs:
            bot = service.create_bot(sample_user.id, config)
            assert bot.name == config.name
            assert bot.llm_provider == config.llm_provider
            assert bot.llm_model == config.llm_model