"""
Tests for permissions API endpoints.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bot import Bot, BotPermission
from tests.test_auth_helper import mock_authentication, create_mock_user


class TestPermissionsAPI:
    """Test cases for permissions API endpoints."""
    
    def test_list_bot_collaborators(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot):
        """Test listing bot collaborators."""
        # Note: sample_bot fixture already creates owner permission for sample_user
        
        # Create another user with editor permission
        editor_user = User(
            username="editor",
            email="editor@example.com",
            password_hash="hashed_password",
            full_name="Editor User"
        )
        db_session.add(editor_user)
        db_session.flush()  # Ensure editor_user gets an ID
        
        editor_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=editor_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(editor_permission)
        db_session.commit()
        
        with mock_authentication(sample_user):
            response = client.get(
                f"/api/bots/{sample_bot.id}/permissions/", 
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check owner
        owner_collab = next(c for c in data if c["role"] == "owner")
        assert owner_collab["username"] == sample_user.username
        
        # Check editor
        editor_collab = next(c for c in data if c["role"] == "editor")
        assert editor_collab["username"] == "editor"
        assert editor_collab["full_name"] == "Editor User"
    
    def test_list_bot_collaborators_without_access(self, client: TestClient, sample_bot: Bot, auth_headers):
        """Test listing collaborators without access."""
        response = client.get(f"/api/bots/{sample_bot.id}/permissions/", headers=auth_headers)
        assert response.status_code == 403
    
    def test_grant_bot_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, sample_auth_headers):
        """Test granting permission to a user."""
        # Note: sample_user already has owner permission from sample_bot fixture (owner > admin)
        
        # Create target user
        target_user = User(
            username="target",
            email="target@example.com",
            password_hash="hashed_password"
        )
        db_session.add(target_user)
        db_session.commit()
        
        permission_data = {
            "user_id": str(target_user.id),
            "role": "editor"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/",
            json=permission_data,
            headers=sample_auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(target_user.id)
        assert data["role"] == "editor"
        assert data["granted_by"] == str(sample_user.id)
    
    def test_grant_bot_permission_without_admin_role(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test granting permission without admin role."""
        # Create a different user with editor permission (insufficient)
        editor_user = User(
            username="editor_user",
            email="editor@example.com",
            password_hash="hashed_password"
        )
        db_session.add(editor_user)
        db_session.flush()
        
        editor_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=editor_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(editor_permission)
        db_session.commit()
        
        # Use auth_headers (test_user) who has no permissions on this bot
        
        target_user_id = uuid.uuid4()
        permission_data = {
            "user_id": str(target_user_id),
            "role": "viewer"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/",
            json=permission_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_grant_owner_role_forbidden(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test that granting owner role is forbidden."""
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        
        target_user = User(
            username="target",
            email="target@example.com",
            password_hash="hashed_password"
        )
        db_session.add(target_user)
        db_session.commit()
        
        permission_data = {
            "user_id": str(target_user.id),
            "role": "owner"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/",
            json=permission_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Cannot grant owner role directly" in response.json()["detail"]
    
    def test_update_bot_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test updating a user's permission."""
        # Create admin permission for updater
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        
        # Create target user with existing permission
        target_user = User(
            username="target",
            email="target@example.com",
            password_hash="hashed_password"
        )
        db_session.add(target_user)
        db_session.flush()  # Ensure target_user gets an ID
        
        existing_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=target_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(existing_permission)
        db_session.commit()
        
        update_data = {"role": "editor"}
        
        response = client.put(
            f"/api/bots/{sample_bot.id}/permissions/{target_user.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "editor"
    
    def test_revoke_bot_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test revoking a user's permission."""
        # Create admin permission for revoker
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        
        # Create target user with permission to revoke
        target_user = User(
            username="target",
            email="target@example.com",
            password_hash="hashed_password"
        )
        db_session.add(target_user)
        db_session.flush()  # Ensure target_user gets an ID
        
        permission_to_revoke = BotPermission(
            bot_id=sample_bot.id,
            user_id=target_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(permission_to_revoke)
        db_session.commit()
        
        response = client.delete(
            f"/api/bots/{sample_bot.id}/permissions/{target_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify permission is deleted
        remaining_permission = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id,
            BotPermission.user_id == target_user.id
        ).first()
        assert remaining_permission is None
    
    def test_revoke_nonexistent_permission(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test revoking nonexistent permission."""
        # Create admin permission
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        db_session.commit()
        
        fake_user_id = uuid.uuid4()
        response = client.delete(
            f"/api/bots/{sample_bot.id}/permissions/{fake_user_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_revoke_owner_permission_forbidden(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test that revoking owner permission is forbidden."""
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        db_session.commit()
        
        response = client.delete(
            f"/api/bots/{sample_bot.id}/permissions/{sample_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Cannot revoke owner permission" in response.json()["detail"]
    
    def test_get_my_bot_role(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test getting current user's role for a bot."""
        # Create editor permission
        permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(permission)
        db_session.commit()
        
        response = client.get(f"/api/bots/{sample_bot.id}/permissions/my-role", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_id"] == str(sample_bot.id)
        assert data["user_id"] == str(sample_user.id)
        assert data["role"] == "editor"
        assert "permissions" in data
        assert "chat" in data["permissions"]
    
    def test_get_my_bot_role_no_access(self, client: TestClient, sample_bot: Bot, auth_headers):
        """Test getting role when user has no access."""
        response = client.get(f"/api/bots/{sample_bot.id}/permissions/my-role", headers=auth_headers)
        assert response.status_code == 403