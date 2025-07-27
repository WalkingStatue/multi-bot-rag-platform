"""
Bot permissions and collaboration API endpoints.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from ..core.database import get_db
from ..core.dependencies import get_current_active_user
from ..core.permissions import (
    get_permission_service,
    require_bot_view,
    require_admin_role
)
from ..models.user import User
from ..schemas.bot import BotPermissionCreate, BotPermissionUpdate, BotPermissionResponse
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/bots/{bot_id}/permissions", tags=["permissions"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_bot_collaborators(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    permission_service: PermissionService = Depends(get_permission_service),
    _: bool = Depends(require_bot_view)
):
    """
    List all collaborators for a bot.
    
    Requires viewer role or higher.
    """
    return permission_service.list_bot_collaborators(bot_id)


@router.post("/", response_model=BotPermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_bot_permission(
    bot_id: uuid.UUID,
    permission_data: BotPermissionCreate,
    current_user: User = Depends(get_current_active_user),
    permission_service: PermissionService = Depends(get_permission_service),
    _: bool = Depends(require_admin_role)
):
    """
    Grant permission to a user for a bot.
    
    Requires admin role or higher. Cannot grant owner role directly.
    """
    permission = permission_service.grant_permission(
        bot_id=bot_id,
        user_id=permission_data.user_id,
        role=permission_data.role,
        granted_by=current_user.id
    )
    
    return BotPermissionResponse.model_validate(permission)


@router.put("/{user_id}", response_model=BotPermissionResponse)
async def update_bot_permission(
    bot_id: uuid.UUID,
    user_id: uuid.UUID,
    permission_update: BotPermissionUpdate,
    current_user: User = Depends(get_current_active_user),
    permission_service: PermissionService = Depends(get_permission_service),
    _: bool = Depends(require_admin_role)
):
    """
    Update a user's role for a bot.
    
    Requires admin role or higher. Cannot update to owner role directly.
    """
    permission = permission_service.grant_permission(
        bot_id=bot_id,
        user_id=user_id,
        role=permission_update.role,
        granted_by=current_user.id
    )
    
    return BotPermissionResponse.model_validate(permission)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_bot_permission(
    bot_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    permission_service: PermissionService = Depends(get_permission_service),
    _: bool = Depends(require_admin_role)
):
    """
    Revoke a user's permission for a bot.
    
    Requires admin role or higher. Cannot revoke owner permission.
    """
    success = permission_service.revoke_permission(
        bot_id=bot_id,
        user_id=user_id,
        revoked_by=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )


@router.get("/my-role", response_model=Dict[str, Any])
async def get_my_bot_role(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    permission_service: PermissionService = Depends(get_permission_service),
    _: bool = Depends(require_bot_view)
):
    """
    Get current user's role for a bot.
    
    Requires viewer role or higher.
    """
    role = permission_service.get_user_bot_role(current_user.id, bot_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this bot"
        )
    
    return {
        "bot_id": bot_id,
        "user_id": current_user.id,
        "role": role,
        "permissions": permission_service.ROLE_PERMISSIONS.get(role, [])
    }