"""
Bot management API endpoints.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from ..core.database import get_db
from ..core.dependencies import get_current_active_user
from ..core.permissions import (
    get_bot_service, 
    get_permission_service,
    require_bot_view,
    require_bot_edit,
    require_owner_role
)
from ..models.user import User
from ..schemas.bot import BotCreate, BotUpdate, BotResponse, BotTransferRequest
from ..services.bot_service import BotService
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_config: BotCreate,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service)
):
    """
    Create a new bot.
    
    The user creating the bot automatically becomes the owner.
    """
    bot = bot_service.create_bot(current_user.id, bot_config)
    return BotResponse.model_validate(bot)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_user_bots(
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service)
):
    """
    List all bots accessible to the current user.
    
    Returns bots with the user's role for each bot.
    """
    accessible_bots = bot_service.list_user_bots(current_user.id)
    
    # Convert to serializable format
    result = []
    for bot_info in accessible_bots:
        bot_data = BotResponse.model_validate(bot_info["bot"])
        result.append({
            "bot": bot_data.model_dump(),
            "role": bot_info["role"],
            "granted_at": bot_info["granted_at"].isoformat() if bot_info["granted_at"] else None
        })
    
    return result


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_bot_view)
):
    """
    Get bot details.
    
    Requires viewer role or higher.
    """
    bot = bot_service.get_bot(bot_id, current_user.id)
    return BotResponse.model_validate(bot)


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: uuid.UUID,
    updates: BotUpdate,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_bot_edit)
):
    """
    Update bot configuration.
    
    Requires admin role or higher.
    """
    bot = bot_service.update_bot(bot_id, current_user.id, updates)
    return BotResponse.model_validate(bot)


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_owner_role)
):
    """
    Delete a bot.
    
    Only the owner can delete a bot. This will cascade delete all
    associated data including conversations, documents, and permissions.
    """
    bot_service.delete_bot(bot_id, current_user.id)


@router.post("/{bot_id}/transfer", status_code=status.HTTP_200_OK)
async def transfer_ownership(
    bot_id: uuid.UUID,
    request: BotTransferRequest,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_owner_role)
):
    """
    Transfer bot ownership to another user.
    
    Only the current owner can transfer ownership.
    """
    success = bot_service.transfer_ownership(bot_id, current_user.id, request.new_owner_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to transfer ownership"
        )
    
    return {"message": "Ownership transferred successfully"}


@router.get("/{bot_id}/analytics", response_model=Dict[str, Any])
async def get_bot_analytics(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_bot_view)
):
    """
    Get bot analytics and usage statistics.
    
    Requires viewer role or higher.
    """
    return bot_service.get_bot_analytics(bot_id, current_user.id)