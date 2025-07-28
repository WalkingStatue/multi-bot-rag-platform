"""
Integration tests for collaboration and permission API endpoints.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bot import Bot, BotPermission
from app.models.activity import ActivityLog


class TestCollaborationAPI:
    """Test cases for collaboration API endpoints."""
    
    def test_invite_collaborator_by_username(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test inviting a collaborator by username."""
        # Create admin permission for inviter
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        
        # Create target user
        target_user = User(
            username="collaborator",
            email="collaborator@example.com",
            password_hash="hashed_password",
            full_name="Collaborator User"
        )
        db_session.add(target_user)
        db_session.commit()
        
        invite_data = {
            "identifier": "collaborator",
            "role": "editor",
            "message": "Welcome to the team!"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/invite",
            json=invite_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "Successfully invited collaborator as editor" in data["message"]
        assert data["user_id"] == str(target_user.id)
        assert data["permission"]["role"] == "editor"
        
        # Verify permission was created in database
        permission = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id,
            BotPermission.user_id == target_user.id
        ).first()
        assert permission is not None
        assert permission.role == "editor"
    
    def test_invite_collaborator_by_email(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test inviting a collaborator by email."""
        # Create admin permission for inviter
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        
        # Create target user
        target_user = User(
            username="emailuser",
            email="emailuser@example.com",
            password_hash="hashed_password"
        )
        db_session.add(target_user)
        db_session.commit()
        
        invite_data = {
            "identifier": "emailuser@example.com",
            "role": "viewer"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/invite",
            json=invite_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["permission"]["role"] == "viewer"
    
    def test_invite_nonexistent_user(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test inviting a user that doesn't exist."""
        # Create admin permission
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        db_session.commit()
        
        invite_data = {
            "identifier": "nonexistent@example.com",
            "role": "editor"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/invite",
            json=invite_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is False
        assert "User not found" in data["message"]
    
    def test_invite_without_admin_role(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test inviting without admin role."""
        # Create editor permission (insufficient)
        editor_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(editor_permission)
        db_session.commit()
        
        invite_data = {
            "identifier": "someone@example.com",
            "role": "viewer"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/invite",
            json=invite_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_bulk_update_permissions(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test bulk updating permissions for multiple users."""
        # Create admin permission
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        
        # Create target users
        user1 = User(username="user1", email="user1@example.com", password_hash="hash")
        user2 = User(username="user2", email="user2@example.com", password_hash="hash")
        user3 = User(username="user3", email="user3@example.com", password_hash="hash")
        
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        
        bulk_data = {
            "user_permissions": [
                {"user_id": str(user1.id), "role": "editor"},
                {"user_id": str(user2.id), "role": "viewer"},
                {"user_id": str(user3.id), "role": "admin"}
            ]
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/bulk-update",
            json=bulk_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["successful"]) == 3
        assert len(data["failed"]) == 0
        
        # Verify permissions were created
        permissions = db_session.query(BotPermission).filter(
            BotPermission.bot_id == sample_bot.id,
            BotPermission.user_id.in_([user1.id, user2.id, user3.id])
        ).all()
        
        assert len(permissions) == 3
        roles = {p.user_id: p.role for p in permissions}
        assert roles[user1.id] == "editor"
        assert roles[user2.id] == "viewer"
        assert roles[user3.id] == "admin"
    
    def test_bulk_update_with_invalid_data(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test bulk update with some invalid data."""
        # Create admin permission
        admin_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="admin",
            granted_by=sample_user.id
        )
        db_session.add(admin_permission)
        
        # Create one valid user
        valid_user = User(username="valid", email="valid@example.com", password_hash="hash")
        db_session.add(valid_user)
        db_session.commit()
        
        bulk_data = {
            "user_permissions": [
                {"user_id": str(valid_user.id), "role": "editor"},  # Valid
                {"user_id": "invalid-uuid", "role": "viewer"},      # Invalid UUID
                {"user_id": str(uuid.uuid4()), "role": "admin"},    # Non-existent user
                {"user_id": str(valid_user.id), "role": "invalid_role"}  # Invalid role
            ]
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/bulk-update",
            json=bulk_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["successful"]) == 1
        assert len(data["failed"]) == 3
        
        # Check specific error messages
        failed_items = {item["user_id"]: item["error"] for item in data["failed"]}
        assert "Invalid user ID format" in failed_items["invalid-uuid"]
        assert "Invalid role" in failed_items[str(valid_user.id)]
    
    def test_get_permission_history(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test getting permission change history."""
        # Create viewer permission
        viewer_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(viewer_permission)
        
        # Create some activity logs
        activity1 = ActivityLog(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            action="permission_granted",
            details={
                "target_user_id": str(sample_user.id),
                "target_username": sample_user.username,
                "role": "viewer"
            }
        )
        
        activity2 = ActivityLog(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            action="permission_updated",
            details={
                "target_user_id": str(sample_user.id),
                "target_username": sample_user.username,
                "old_role": "viewer",
                "new_role": "editor"
            }
        )
        
        db_session.add_all([activity1, activity2])
        db_session.commit()
        
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check the most recent activity first (desc order)
        assert data[0]["action"] == "updated"
        assert data[0]["old_role"] == "viewer"
        assert data[0]["new_role"] == "editor"
        
        assert data[1]["action"] == "granted"
        assert data[1]["new_role"] == "viewer"
        assert data[1]["old_role"] is None
    
    def test_get_permission_history_with_pagination(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test permission history with pagination."""
        # Create viewer permission
        viewer_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(viewer_permission)
        
        # Create multiple activity logs
        activities = []
        for i in range(10):
            activity = ActivityLog(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                action="permission_granted",
                details={
                    "target_user_id": str(sample_user.id),
                    "target_username": f"user{i}",
                    "role": "viewer"
                }
            )
            activities.append(activity)
        
        db_session.add_all(activities)
        db_session.commit()
        
        # Test pagination
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/history?limit=5&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Test second page
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/history?limit=5&offset=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_get_bot_activity_logs(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test getting bot activity logs."""
        # Create viewer permission
        viewer_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(viewer_permission)
        
        # Create various activity logs
        activities = [
            ActivityLog(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                action="bot_created",
                details={"name": sample_bot.name}
            ),
            ActivityLog(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                action="permission_granted",
                details={"target_user_id": str(sample_user.id), "role": "viewer"}
            ),
            ActivityLog(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                action="document_uploaded",
                details={"filename": "test.pdf"}
            )
        ]
        
        db_session.add_all(activities)
        db_session.commit()
        
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/activity",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Check that all activities are returned
        actions = [item["action"] for item in data]
        assert "bot_created" in actions
        assert "permission_granted" in actions
        assert "document_uploaded" in actions
    
    def test_get_bot_activity_logs_with_filter(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test getting bot activity logs with action filter."""
        # Create viewer permission
        viewer_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="viewer",
            granted_by=sample_user.id
        )
        db_session.add(viewer_permission)
        
        # Create various activity logs
        activities = [
            ActivityLog(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                action="permission_granted",
                details={"target_user_id": str(sample_user.id), "role": "viewer"}
            ),
            ActivityLog(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                action="permission_granted",
                details={"target_user_id": str(uuid.uuid4()), "role": "editor"}
            ),
            ActivityLog(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                action="document_uploaded",
                details={"filename": "test.pdf"}
            )
        ]
        
        db_session.add_all(activities)
        db_session.commit()
        
        # Filter by permission_granted action
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/activity?action_filter=permission_granted",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # All returned activities should be permission_granted
        for item in data:
            assert item["action"] == "permission_granted"
    
    def test_activity_logs_without_access(self, client: TestClient, sample_bot: Bot, auth_headers):
        """Test accessing activity logs without bot access."""
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/activity",
            headers=auth_headers
        )
        assert response.status_code == 403
    
    def test_permission_history_without_access(self, client: TestClient, sample_bot: Bot, auth_headers):
        """Test accessing permission history without bot access."""
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/history",
            headers=auth_headers
        )
        assert response.status_code == 403
    
    def test_bulk_update_without_admin_role(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test bulk update without admin role."""
        # Create editor permission (insufficient)
        editor_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="editor",
            granted_by=sample_user.id
        )
        db_session.add(editor_permission)
        db_session.commit()
        
        bulk_data = {
            "user_permissions": [
                {"user_id": str(uuid.uuid4()), "role": "viewer"}
            ]
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/bulk-update",
            json=bulk_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403


class TestCollaborationWorkflows:
    """Test complete collaboration workflows."""
    
    def test_complete_collaboration_workflow(self, client: TestClient, db_session: Session, sample_user: User, sample_bot: Bot, auth_headers):
        """Test a complete collaboration workflow from invitation to removal."""
        # Step 1: Create owner permission
        owner_permission = BotPermission(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            role="owner",
            granted_by=sample_user.id
        )
        db_session.add(owner_permission)
        
        # Create collaborator user
        collaborator = User(
            username="collaborator",
            email="collaborator@example.com",
            password_hash="hashed_password"
        )
        db_session.add(collaborator)
        db_session.commit()
        
        # Step 2: Invite collaborator
        invite_data = {
            "identifier": "collaborator",
            "role": "editor"
        }
        
        response = client.post(
            f"/api/bots/{sample_bot.id}/permissions/invite",
            json=invite_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["success"] is True
        
        # Step 3: List collaborators
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        collaborators = response.json()
        assert len(collaborators) == 2  # Owner + collaborator
        
        # Step 4: Update collaborator role
        update_data = {"role": "admin"}
        response = client.put(
            f"/api/bots/{sample_bot.id}/permissions/{collaborator.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["role"] == "admin"
        
        # Step 5: Check permission history
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        history = response.json()
        assert len(history) >= 2  # At least grant and update
        
        # Step 6: Remove collaborator
        response = client.delete(
            f"/api/bots/{sample_bot.id}/permissions/{collaborator.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Step 7: Verify collaborator is removed
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        collaborators = response.json()
        assert len(collaborators) == 1  # Only owner remains
        
        # Step 8: Check final activity logs
        response = client.get(
            f"/api/bots/{sample_bot.id}/permissions/activity",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        activities = response.json()
        
        # Should have activities for grant, update, and revoke
        actions = [activity["action"] for activity in activities]
        assert "permission_granted" in actions
        assert "permission_updated" in actions
        assert "permission_revoked" in actions