"""
Bot management service with permission integration.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
import uuid

from ..models.bot import Bot, BotPermission
from ..models.user import User
from ..models.activity import ActivityLog
from ..schemas.bot import BotCreate, BotUpdate
from .permission_service import PermissionService


class BotService:
    """Service for bot management operations with permission integration."""
    
    def __init__(self, db: Session):
        self.db = db
        self.permission_service = PermissionService(db)
    
    def create_bot(self, user_id: uuid.UUID, bot_config: BotCreate) -> Bot:
        """
        Create a new bot and assign owner permissions.
        
        Args:
            user_id: User ID creating the bot
            bot_config: Bot configuration
            
        Returns:
            Created bot object
            
        Raises:
            HTTPException: If validation fails
        """
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create bot
        bot = Bot(
            name=bot_config.name,
            description=bot_config.description,
            system_prompt=bot_config.system_prompt,
            owner_id=user_id,
            llm_provider=bot_config.llm_provider,
            llm_model=bot_config.llm_model,
            embedding_provider=bot_config.embedding_provider,
            embedding_model=bot_config.embedding_model,
            temperature=bot_config.temperature,
            max_tokens=bot_config.max_tokens,
            top_p=bot_config.top_p,
            frequency_penalty=bot_config.frequency_penalty,
            presence_penalty=bot_config.presence_penalty,
            is_public=bot_config.is_public,
            allow_collaboration=bot_config.allow_collaboration
        )
        
        self.db.add(bot)
        self.db.flush()  # Get the bot ID
        
        # Create owner permission
        owner_permission = BotPermission(
            bot_id=bot.id,
            user_id=user_id,
            role="owner",
            granted_by=user_id
        )
        
        self.db.add(owner_permission)
        
        # Log activity
        self.permission_service._log_activity(
            bot_id=bot.id,
            user_id=user_id,
            action="bot_created",
            details={
                "bot_name": bot.name,
                "llm_provider": bot.llm_provider,
                "llm_model": bot.llm_model
            }
        )
        
        self.db.commit()
        self.db.refresh(bot)
        
        return bot
    
    def get_bot(self, bot_id: uuid.UUID, user_id: uuid.UUID) -> Bot:
        """
        Get a bot if user has access.
        
        Args:
            bot_id: Bot ID
            user_id: User ID requesting access
            
        Returns:
            Bot object
            
        Raises:
            HTTPException: If bot not found or access denied
        """
        # Check if user has view permission
        if not self.permission_service.check_bot_permission(user_id, bot_id, "view_bot"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        return bot
    
    def update_bot(self, bot_id: uuid.UUID, user_id: uuid.UUID, updates: BotUpdate) -> Bot:
        """
        Update a bot if user has edit permissions.
        
        Args:
            bot_id: Bot ID
            user_id: User ID requesting update
            updates: Bot updates
            
        Returns:
            Updated bot object
            
        Raises:
            HTTPException: If bot not found or access denied
        """
        # Check if user has edit permission
        if not self.permission_service.check_bot_permission(user_id, bot_id, "edit_bot"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to edit bot"
            )
        
        bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Track changes for logging
        changes = {}
        
        # Update fields
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(bot, field):
                old_value = getattr(bot, field)
                if old_value != value:
                    changes[field] = {"old": old_value, "new": value}
                    setattr(bot, field, value)
        
        if changes:
            # Log activity
            self.permission_service._log_activity(
                bot_id=bot_id,
                user_id=user_id,
                action="bot_updated",
                details={
                    "changes": changes
                }
            )
        
        self.db.commit()
        self.db.refresh(bot)
        
        return bot
    
    def delete_bot(self, bot_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Delete a bot if user is owner.
        
        Args:
            bot_id: Bot ID
            user_id: User ID requesting deletion
            
        Returns:
            True if bot was deleted
            
        Raises:
            HTTPException: If bot not found or access denied
        """
        # Check if user has delete permission (owner only)
        if not self.permission_service.check_bot_permission(user_id, bot_id, "delete_bot"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can delete a bot"
            )
        
        bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Log activity before deletion
        self.permission_service._log_activity(
            bot_id=bot_id,
            user_id=user_id,
            action="bot_deleted",
            details={
                "bot_name": bot.name,
                "bot_id": str(bot_id)
            }
        )
        
        # Delete bot (cascade will handle related records)
        self.db.delete(bot)
        self.db.commit()
        
        return True
    
    def list_user_bots(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        List all bots accessible to a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of bots with user's role
        """
        return self.permission_service.get_user_accessible_bots(user_id)
    
    def transfer_ownership(
        self, 
        bot_id: uuid.UUID, 
        current_owner: uuid.UUID, 
        new_owner: uuid.UUID
    ) -> bool:
        """
        Transfer bot ownership to another user.
        
        Args:
            bot_id: Bot ID
            current_owner: Current owner user ID
            new_owner: New owner user ID
            
        Returns:
            True if ownership was transferred
        """
        return self.permission_service.transfer_ownership(bot_id, current_owner, new_owner)
    
    def get_bot_analytics(self, bot_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get bot analytics if user has access.
        
        Args:
            bot_id: Bot ID
            user_id: User ID requesting analytics
            
        Returns:
            Bot analytics data
            
        Raises:
            HTTPException: If access denied
        """
        # Check if user has view permission
        if not self.permission_service.check_bot_permission(user_id, bot_id, "view_bot"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get basic bot info
        bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Count collaborators
        collaborator_count = self.db.query(BotPermission).filter(
            BotPermission.bot_id == bot_id
        ).count()
        
        # Count conversations (if conversation model exists)
        conversation_count = 0
        message_count = 0
        try:
            from ..models.conversation import ConversationSession, Message
            conversation_count = self.db.query(ConversationSession).filter(
                ConversationSession.bot_id == bot_id
            ).count()
            
            message_count = self.db.query(Message).filter(
                Message.bot_id == bot_id
            ).count()
        except ImportError:
            pass
        
        # Count documents (if document model exists)
        document_count = 0
        try:
            from ..models.document import Document
            document_count = self.db.query(Document).filter(
                Document.bot_id == bot_id
            ).count()
        except ImportError:
            pass
        
        return {
            "bot_id": bot_id,
            "bot_name": bot.name,
            "created_at": bot.created_at,
            "collaborator_count": collaborator_count,
            "conversation_count": conversation_count,
            "message_count": message_count,
            "document_count": document_count,
            "user_role": self.permission_service.get_user_bot_role(user_id, bot_id)
        }