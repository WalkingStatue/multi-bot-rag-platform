"""
Tests for permission service functionality.
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.models.activity import ActivityLog
from app.services.permission_service import PermissionService


class TestPermissionService:
    """Test cases for PermissionService."""
    
    def test_role_hierarchy(self):
        """Test role hierarchy constants."""
        service = PermissionService(None)
        
        assert service.ROLE_HIERARCHY["viewer"] < service.ROLE_HIERARCHY["editor"]
        assert service.ROLE_HIERARCHY["editor"] < service.ROLE_HIERARCHY["admin"]
        assert service.ROLE_HIERARCHY["admin"] < service.ROLE_HIERARCHY["owner"]
    
    def test_role_permissions(self):
        """Test role permissions constants."""
        service = PermissionService(None)
        
        # Viewer permissions
        viewer_perms = service.ROLE_PERMISSIONS["viewer"]
        assert "view_bot" in viewer_perms
        assert "chat" not in viewer_perms
        assert "edit_bot" not in viewer_perms
        
        # Editor permissions (includes viewer + more)
        editor_perms = service.ROLE_PERMISSIONS["editor"]
        assert "view_bot" in editor_perms
        assert "chat" in editor_perms
        assert "upload_documents" in editor_perms
        assert "edit_bot" not in editor_perms
        
        # Admin permissions (includes editor + more)
        admin_perms = service.ROLE_PERMISSIONS["admin"]
        assert "view_bot" in admin_perms
        assert "chat" in admin_perms
        assert "edit_bot" in admin_perms
        assert "manage_collaborators" in admin_perms
        assert "delete_bot" not in admin_perms
        
        # Owner permissions (includes all)
        owner_perms = service.ROLE_PERMISSIONS["owner"]
        assert "view_bot" in owner_perms
        assert "edit_bot" in owner_perms
        assert "delete_bot" in owner_perms
        assert "transfer_ownership" in owner_perms
    
    def test_check_bot_permission_no_access(self, db_session: Session):
        """Test permission check when user has no access."""
        service = PermissionService(db_session)
        
        user_id = uuid.uuid4()
        bot_id = uuid.uuid4()
        
        result = service.check_bot_permission(user_id, bot_id, "view_bot")
        assert result is False
    
    def test_check_bot_permission_with_access(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test permission check when user has access."""
        service = PermissionService(db_session)
        
        # Create permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        # Test permissions
        assert service.check_bot_permission(sample_user.id, sample_bot.id, "view_bot") is True
        assert service.check_bot_permission(sample_user.id, sample_bot.id, "chat") is True
        assert service.check_bot_permission(sample_user.id, sample_bot.id, "edit_bot") is False
        assert service.check_bot_permission(sample_user.id, sample_bot.id, "delete_bot") is False
    
    def test_check_bot_role(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test role checking functionality."""
        service = PermissionService(db_session)
        
        # Create admin permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        # Test role checks
        assert service.check_bot_role(sample_user.id, sample_bot.id, "viewer") is True
        assert service.check_bot_role(sample_user.id, sample_bot.id, "editor") is True
        assert service.check_bot_role(sample_user.id, sample_bot.id, "admin") is True
        assert service.check_bot_role(sample_user.id, sample_bot.id, "owner") is False
    
    def test_get_user_bot_role(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test getting user's role for a bot."""
        service = PermissionService(db_session)
        
        # No permission initially
        role = service.get_user_bot_role(sample_user.id, sample_bot.id)
        assert role is None
        
        # Create permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        # Should return role
        role = service.get_user_bot_role(sample_user.id, sample_bot.id)
        assert role == "editor"
    
    def test_grant_permission_new(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test granting new permission."""
        service = PermissionService(db_session)
        
        # Create owner permission for granter
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        db_session.commit()
        
        # Create another user
        other_user = User(
            username="testuser2",
            email="test2@example.com",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.commit()
        
        # Grant permission
        permission = service.grant_permission(
            bot_id=sample_bot.id,
            user_id=other_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        
        assert permission.bot_id == sample_bot.id
        assert permission.user_id == other_user.id
        assert permission.role == "editor"
        assert permission.granted_by == sample_user.id
        
        # Check activity log
        activity = db_session.query(ActivityLog).filter(
            ActivityLog.action == "permission_granted"
        ).first()
        assert activity is not None
        assert activity.bot_id == sample_bot.id
        assert activity.user_id == sample_user.id
    
    def test_grant_permission_update_existing(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test updating existing permission."""
        service = PermissionService(db_session)
        
        # Create owner permission for granter
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        
        # Create another user with existing permission
        other_user = User(
            username="testuser2",
            email="test2@example.com",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.flush()  # Flush to get the user ID
        
        existing_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=other_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(existing_permission)
        db_session.commit()
        
        # Update permission
        updated_permission = service.grant_permission(
            bot_id=sample_bot.id,
            user_id=other_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        
        assert updated_permission.id == existing_permission.id
        assert updated_permission.role == "admin"
        
        # Check activity log
        activity = db_session.query(ActivityLog).filter(
            ActivityLog.action == "permission_updated"
        ).first()
        assert activity is not None
    
    def test_grant_permission_invalid_role(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test granting permission with invalid role."""
        service = PermissionService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.grant_permission(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                role="invalid_role",
                granted_by=sample_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid role" in str(exc_info.value.detail)
    
    def test_grant_permission_insufficient_permissions(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test granting permission without sufficient permissions."""
        service = PermissionService(db_session)
        
        # Create viewer permission (insufficient for granting)
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        other_user = User(
            username="testuser2",
            email="test2@example.com",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            service.grant_permission(
                bot_id=sample_bot.id,
                user_id=other_user.id,
                role="editor",
                granted_by=sample_user.id
            )
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)
    
    def test_grant_owner_role_forbidden(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test that granting owner role directly is forbidden."""
        service = PermissionService(db_session)
        
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        db_session.commit()
        
        other_user = User(
            username="testuser2",
            email="test2@example.com",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            service.grant_permission(
                bot_id=sample_bot.id,
                user_id=other_user.id,
                role="owner",
                granted_by=sample_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "Cannot grant owner role directly" in str(exc_info.value.detail)
    
    def test_revoke_permission(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test revoking permission."""
        service = PermissionService(db_session)
        
        # Create owner permission for revoker
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        
        # Create another user with permission to revoke
        other_user = User(
            username="testuser2",
            email="test2@example.com",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.flush()  # Flush to get the user ID
        
        permission_to_revoke = BotPermission(
            bot_id=sample_bot.id,
            user_id=other_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(permission_to_revoke)
        db_session.commit()
        
        # Revoke permission
        result = service.revoke_permission(
            bot_id=sample_bot.id,
            user_id=other_user.id,
            revoked_by=sample_user.id
        )
        
        assert result is True
        
        # Check permission is deleted
        remaining_permission = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id,
            BotPermission.user_id == other_user.id
        ).first()
        assert remaining_permission is None
        
        # Check activity log
        activity = db_session.query(ActivityLog).filter(
            ActivityLog.action == "permission_revoked"
        ).first()
        assert activity is not None
    
    def test_revoke_permission_nonexistent(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test revoking nonexistent permission."""
        service = PermissionService(db_session)
        
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        db_session.commit()
        
        # Try to revoke nonexistent permission
        result = service.revoke_permission(
            bot_id=sample_bot.id,
            user_id=uuid.uuid4(),
            revoked_by=sample_user.id
        )
        
        assert result is False
    
    def test_revoke_owner_permission_forbidden(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test that revoking owner permission is forbidden."""
        service = PermissionService(db_session)
        
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            service.revoke_permission(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                revoked_by=sample_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "Cannot revoke owner permission" in str(exc_info.value.detail)
    
    def test_list_bot_collaborators(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test listing bot collaborators."""
        service = PermissionService(db_session)
        
        # Create permissions for multiple users
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        
        other_user = User(
            username="testuser2",
            email="test2@example.com",
            password_hash="hashed_password",
            full_name="Test User 2"
        )
        db_session.add(other_user)
        db_session.flush()  # Flush to get the user ID
        
        editor_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=other_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(editor_permission)
        db_session.commit()
        
        # List collaborators
        collaborators = service.list_bot_collaborators(sample_bot.id)
        
        assert len(collaborators) == 2
        
        # Check owner
        owner_collab = next(c for c in collaborators if c["role"] == "owner")
        assert owner_collab["user_id"] == sample_user.id
        assert owner_collab["username"] == sample_user.username
        
        # Check editor
        editor_collab = next(c for c in collaborators if c["role"] == "editor")
        assert editor_collab["user_id"] == other_user.id
        assert editor_collab["username"] == other_user.username
        assert editor_collab["full_name"] == other_user.full_name
    
    def test_transfer_ownership(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test transferring bot ownership."""
        service = PermissionService(db_session)
        
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        
        # Create new owner user
        new_owner = User(
            username="newowner",
            email="newowner@example.com",
            password_hash="hashed_password"
        )
        db_session.add(new_owner)
        db_session.commit()
        
        # Transfer ownership
        result = service.transfer_ownership(
            bot_id=sample_bot.id,
            current_owner=sample_user.id,
            new_owner=new_owner.id
        )
        
        assert result is True
        
        # Check bot owner updated
        db_session.refresh(sample_bot)
        assert sample_bot.owner_id == new_owner.id
        
        # Check old owner permission removed
        old_permission = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id,
            BotPermission.user_id == sample_user.id,
            BotPermission.role == "owner"
        ).first()
        assert old_permission is None
        
        # Check new owner permission created
        new_permission = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id,
            BotPermission.user_id == new_owner.id,
            BotPermission.role == "owner"
        ).first()
        assert new_permission is not None
        assert new_permission.granted_by == sample_user.id
        
        # Check activity log
        activity = db_session.query(ActivityLog).filter(
            ActivityLog.action == "ownership_transferred"
        ).first()
        assert activity is not None
    
    def test_transfer_ownership_not_owner(self, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test transfer ownership when user is not owner."""
        service = PermissionService(db_session)
        
        # Create non-owner permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        new_owner = User(
            username="newowner",
            email="newowner@example.com",
            password_hash="hashed_password"
        )
        db_session.add(new_owner)
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            service.transfer_ownership(
                bot_id=sample_bot.id,
                current_owner=sample_user.id,
                new_owner=new_owner.id
            )
        
        assert exc_info.value.status_code == 403
        assert "Only the owner can transfer ownership" in str(exc_info.value.detail)
    
    def test_get_user_accessible_bots(self, db_session: Session, sample_user: User):
        """Test getting user's accessible bots."""
        service = PermissionService(db_session)
        
        # Create another user for bot2
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.flush()  # Get the user ID
        
        # Create multiple bots with different permissions
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
        
        # Get accessible bots
        accessible_bots = service.get_user_accessible_bots(sample_user.id)
        
        assert len(accessible_bots) == 2
        
        # Check owner bot
        owner_bot = next(b for b in accessible_bots if b["role"] == "owner")
        assert owner_bot["bot"].id == bot1.id
        assert owner_bot["bot"].name == "Bot 1"
        
        # Check editor bot
        editor_bot = next(b for b in accessible_bots if b["role"] == "editor")
        assert editor_bot["bot"].id == bot2.id
        assert editor_bot["bot"].name == "Bot 2"